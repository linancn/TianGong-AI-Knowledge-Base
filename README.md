
# TianGong Knowledge Base

## Env Preparing

Install `Python 3.11

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11
```

Setup `venv`:

```bash
sudo apt install python3.11-venv
python3.11 -m venv .venv
source .venv/bin/activate
```

Install requirements:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt --upgrade
```

## Env Preparing in MacOS

Install `Python 3.11`

```bash
brew update
brew install python@3.11
```

Setup `venv`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install requirements:

```bash
pip install -r requirements.txt
```

## Run Streamlit

```bash
streamlit run Home.py
```

### Auto Build

The auto build will be triggered by pushing any tag named like release-v$version. For instance, push a tag named as v0.0.1 will build a docker image of 0.0.1 version.

```bash
#list existing tags
git tag
#creat a new tag
git tag v0.0.1
#push this tag to origin
git push origin v0.0.1
```

### Production Run

```bash
docker run --detach \
    --name tiangong-ai-kb \
    --restart=always \
    --expose 8501 \
    --net=tiangongbridge \
    --env VIRTUAL_HOST=YourURL \
    --env VIRTUAL_PORT=8501 \
    --env LETSENCRYPT_HOST=YourURL \
    --env LETSENCRYPT_EMAIL=YourEmail \
    linancn/tiangong-ai-kb:v0.0.1

docker cp secrets_kb.toml tiangong-ai-kb:/app/.streamlit/secrets.toml
```
