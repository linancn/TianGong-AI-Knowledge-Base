from module import pdf
from pyzotero import zotero
import io
import json
import logging
import pandas as pd
import pdfplumber
import requests
import streamlit as st


# logging.basicConfig(
#     filename="zotero.log",
#     level=logging.DEBUG,
#     format="%(asctime)s:%(levelname)s:%(message)s",
# )

st.set_page_config(layout="wide", page_title="TianGong", page_icon="static/favicon.ico")

st.title("📜 Documents Upload")

st.markdown(
    """
    <style>
        div[data-testid="stDecoration"] {
            background-image: linear-gradient(90deg, #82318E, #C2B6B2);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def text_upsert(
    text_input,
    key_input,
    source_input,
    source_id_input,
    url_input,
    created_at_input,
    author_input,
):
    url = "https://plugins.tiangong.world/upsert"
    access_token = st.secrets["plugin_access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    data = {
        "documents": [
            {
                "id": key_input,
                "text": text_input,
                "metadata": {
                    "source": source_input,
                    "source_id": source_id_input,
                    "url": url_input,
                    "created_at": created_at_input,
                    "author": author_input,
                },
            }
        ]
    }

    data_string = json.dumps(data)

    response = requests.request("POST", url, headers=headers, data=data_string)

    return response


# @st.cache_data(experimental_allow_widgets=True)
def get_zotero_collection(zot_user_id, zot_catagory, zot_api_key):
    # Authenticate with Zotero API
    zot = zotero.Zotero(zot_user_id, zot_catagory, zot_api_key)

    sidebar_placeholder_root = st.sidebar.empty()
    sidebar_placeholder_catalog = st.sidebar.empty()
    sidebar_placeholder_tag = st.sidebar.empty()

    zot_root_collection = sidebar_placeholder_root.text_input(
        "Root collection", value=st.secrets["zot_root_collection"]
    )

    # Get collections from Zotero library
    collections_info = zot.collections_sub(zot_root_collection)
    collections = [
        {"id": c["key"], "name": c["data"]["name"], "count": c["meta"]["numItems"]}
        for c in collections_info
    ]

    # Display collection names in a selectbox
    selected_collection = sidebar_placeholder_catalog.selectbox(
        "Select collection",
        [f"{c['name']} ({c['count']} items)" for c in collections],
        key="selectbox_catalog",
    )

    # Get items from selected collection
    collection_id = next(
        c["id"] for c in collections if c["name"] == selected_collection.split(" (")[0]
    )

    st.session_state["collection_id"] = collection_id

    tags = zot.collection_tags(collection_id)
    tags = [""] + tags

    zot_tag = sidebar_placeholder_tag.selectbox(
        "Zotero Tag", tags, key="zotero_tag_selectbox"
    )

    st.session_state["zot_tag"] = zot_tag


# @st.cache_data(experimental_allow_widgets=True)
def get_zotero_item(zot_user_id, zot_catagory, zot_api_key, collection_id, zot_tag):
    # Authenticate with Zotero API
    zot = zotero.Zotero(zot_user_id, zot_catagory, zot_api_key)

    items = zot.everything(zot.collection_items(collection_id, tag=zot_tag))
    attachments = zot.everything(
        zot.collection_items(collection_id, itemType="attachment")
    )

    # Get items with PDFs

    pdf_file = []
    for attachment in attachments:
        for item in items:
            if item["data"]["key"] == attachment["data"].get("parentItem", None):
                pdf_file.append(
                    {
                        "key": attachment["data"].get("key", ""),
                        "title": item["data"].get("title")
                        or item["data"].get("nameOfAct", ""),
                        "source": item["data"].get("itemType", ""),
                        "url": "https://doi.org/" + item["data"].get("DOI")
                        if item["data"].get("DOI")
                        else item["data"].get("url", ""),
                        "author": ",".join(
                            author.get("name", "")
                            for author in item["data"].get("creators", [])
                        ),
                        "date": item["data"].get("date", "")
                        or item["data"].get("dateEnacted", ""),
                        "parentItem": item["data"]["key"],
                    }
                )

    return pd.DataFrame(pdf_file).sort_values(by="date", ascending=False)


# @st.cache_data()
def get_zotero_attachment(zot_user_id, zot_catagory, zot_api_key, item_key):
    zot = zotero.Zotero(zot_user_id, zot_catagory, zot_api_key)
    raw = zot.file(item_key)
    return raw


def udpate_zotero_tag(zot_user_id, zot_catagory, zot_api_key, item_key, tag_input):
    zot = zotero.Zotero(zot_user_id, zot_catagory, zot_api_key)
    item = zot.item(item_key)
    zot.add_tags(item, tag_input)


if st.secrets["need_password"] is False:
    auth = True
else:
    auth = check_password()


if auth:
    # Get Zotero API key and user ID
    zot_user_id = st.secrets["zot_user_id"]
    zot_api_key = st.secrets["zot_api_key"]

    sidebar_placeholder_group = st.sidebar.empty()

    zot_catagory = sidebar_placeholder_group.selectbox(
        "Group or User",
        [
            "group",
            "user",
        ],
    )

    if zot_user_id and zot_catagory and zot_api_key:
        get_zotero_collection(zot_user_id, zot_catagory, zot_api_key)

        load_button = st.sidebar.button("Load", use_container_width=True)

        if load_button:
            df = get_zotero_item(
                zot_user_id,
                zot_catagory,
                zot_api_key,
                st.session_state["collection_id"],
                st.session_state["zot_tag"],
            )
            st.session_state["df"] = df

        if "df" in st.session_state:
            df = st.session_state["df"]
            st.dataframe(df, use_container_width=True)

            # 使用 st.multiselect() 创建下拉列表，允许用户选择行
            selected_indices = st.multiselect(
                "Select the report you want to upload:",
                options=list(range(len(df))),
                format_func=lambda x: f"Row {x}: {df.iloc[x]['date']} {df.iloc[x]['title']}",
                max_selections=1,
                default=None,
            )

            if selected_indices:
                # 从Zotero获取单个PDF文件
                key = df.iloc[selected_indices]["key"].values[0]
                source = df.iloc[selected_indices]["source"].values[0].upper()
                source_id = df.iloc[selected_indices]["title"].values[0]
                url = df.iloc[selected_indices]["url"].values[0]
                created_at = df.iloc[selected_indices]["date"].values[0]
                author = df.iloc[selected_indices]["author"].values[0]
                parentItem = df.iloc[selected_indices]["parentItem"].values[0]

                raw = get_zotero_attachment(zot_user_id, zot_catagory, zot_api_key, key)

                open_pdf_file = io.BytesIO(raw)
                pdf_reader = pdfplumber.open(open_pdf_file)
                num_pages = len(pdf_reader.pages)
                page_range = st.slider(
                    "Choose pages:",
                    min_value=1,
                    max_value=num_pages,
                    value=[1, num_pages],
                )

                extract_button = st.button("Extract")

                if extract_button:
                    text_input = st.text_area(
                        "text",
                        value=pdf.parse_paper_range(
                            pdf_reader, page_range[0], page_range[1]
                        ),
                        height=600,
                    )

                    st.session_state["text_input"] = text_input

                # 上传文件到vector数据库
                if "text_input" in st.session_state:
                    upsert_button = st.button("Upsert")
                    if upsert_button:
                        try:
                            response = text_upsert(
                                text_input=st.session_state["text_input"],
                                key_input=parentItem,
                                source_input=source,
                                source_id_input=source_id,
                                url_input=url,
                                created_at_input=created_at,
                                author_input=author,
                            )
                            st.write(response)
                            if response.status_code == 200:
                                udpate_zotero_tag(
                                    zot_user_id,
                                    zot_catagory,
                                    zot_api_key,
                                    parentItem,
                                    "uploaded",
                                )
                                st.write(key)
                        except:
                            udpate_zotero_tag(
                                zot_user_id,
                                zot_catagory,
                                zot_api_key,
                                parentItem,
                                "failed",
                            )
                            logging.error(f"uploading {parentItem} failed")
