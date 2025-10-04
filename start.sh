python3.11 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

rasa train
rasa run --enable-api --cors "*" --debug
