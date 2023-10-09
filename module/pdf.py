from collections import Counter
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)


def parse_paper_lastpage(_pdf, last_page_number):
    full_text = ""
    ismisc = False

    page = _pdf.pages[last_page_number]
    isfirstpage = False

    page_text = []
    sentences = []
    processed_text = []

    def visitor_body(text, isfirstpage, x, top, bottom, fontSize, ismisc):
        # ignore header/footer
        if isfirstpage:
            if (top > 200 and bottom < 720) and (len(text.strip()) > 1):
                sentences.append(
                    {
                        "fontsize": fontSize,
                        "text": " " + text.strip().replace("\x03", ""),
                        "x": x,
                        "y": top,
                    }
                )
        else:  # not first page
            if (
                (top > 70 and bottom < 720) and (len(text.strip()) > 1) and not ismisc
            ):  # main text region
                sentences.append(
                    {
                        "fontsize": fontSize,
                        "text": " " + text.strip().replace("\x03", ""),
                        "x": x,
                        "y": top,
                    }
                )
            elif (top > 70 and bottom < 720) and (len(text.strip()) > 1) and ismisc:
                pass

    extracted_words = page.extract_words(
        x_tolerance=1,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=True,
        horizontal_ltr=True,
        vertical_ttb=True,
        extra_attrs=["fontname", "size"],
        split_at_punctuation=False,
    )

    # Treat the first page, main text, and references differently, specifically targeted at headers
    # Define a list of keywords to ignore
    # Online is for Nauture papers
    keywords_for_misc = [
        "References",
        "REFERENCES",
        "Bibliography",
        "BIBLIOGRAPHY",
        "Acknowledgements",
        "ACKNOWLEDGEMENTS",
        "Acknowledgments",
        "ACKNOWLEDGMENTS",
        "参考文献",
        "致谢",
        "謝辞",
        "謝",
        "Online",
    ]

    prev_word_size = None
    prev_word_font = None
    # Loop through the extracted words
    for extracted_word in extracted_words:
        # Strip the text and remove any special characters
        text = extracted_word["text"].strip().replace("\x03", "")

        # Check if the text contains any of the keywords to ignore
        if any(keyword in text for keyword in keywords_for_misc) and (
            prev_word_size != extracted_word["size"]
            or prev_word_font != extracted_word["fontname"]
        ):
            ismisc = True

        prev_word_size = extracted_word["size"]
        prev_word_font = extracted_word["fontname"]

        # Call the visitor_body function with the relevant arguments
        visitor_body(
            text,
            isfirstpage,
            extracted_word["x0"],
            extracted_word["top"],
            extracted_word["bottom"],
            extracted_word["size"],
            ismisc,
        )

    if sentences:
        for sentence in sentences:
            page_text.append(sentence)

    blob_font_sizes = []
    blob_font_size = None
    blob_text = ""
    processed_text = ""
    tolerance = 1

    # Preprocessing for main text font size
    if page_text != []:
        if len(page_text) == 1:
            blob_font_sizes.append(page_text[0]["fontsize"])
        else:
            for t in page_text:
                blob_font_sizes.append(t["fontsize"])
        blob_font_size = Counter(blob_font_sizes).most_common(1)[0][0]

    if page_text != []:
        if len(page_text) == 1:
            if (
                blob_font_size - tolerance
                <= page_text[0]["fontsize"]
                <= blob_font_size + tolerance
            ):
                processed_text += page_text[0]["text"]
                # processed_text.append({"text": page_text[0]["text"], "page": i + 1})
        else:
            for t in range(len(page_text)):
                if (
                    blob_font_size - tolerance
                    <= page_text[t]["fontsize"]
                    <= blob_font_size + tolerance
                ):
                    blob_text += f"{page_text[t]['text']}"
                    if len(blob_text) >= 500:  # set the length of a data chunk
                        processed_text += blob_text
                        # processed_text.append({"text": blob_text, "page": i + 1})
                        blob_text = ""
                    elif t == len(page_text) - 1:  # last element
                        processed_text += blob_text
                        # processed_text.append({"text": blob_text, "page": i + 1})
        full_text += processed_text

    # logging.info("Done parsing paper")
    return full_text


# 简单方法获取范围页面的正文全文
@st.cache_data
def parse_paper_range(_pdf, start_page, end_page):
    # 页码从0开始
    start_page = start_page - 1
    end_page = end_page - 1

    all_text = ""
    if start_page == end_page:
        page_content = _pdf.pages[start_page]
        text = page_content.extract_text()
        all_text = text
    else:
        for page in range(start_page, end_page):
            page_content = _pdf.pages[page]
            text = page_content.extract_text()
            all_text += text
        text = parse_paper_lastpage(_pdf, end_page)
        all_text += text
    return all_text
