import os
import json
import socket
import helper
import requests
import searcher

import pymupdf

from transformers import AutoConfig
from transformers import AutoTokenizer

from flask import Flask, request, jsonify

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

app = Flask(__name__)

UPLOAD_FOLDER = './mount/pdfs/'
UPLOAD_VEKTOR_FOLDER = './mount/vectors/'
OUTPUT_FOLDER = './mount/texts/'
HISTORIES_BY_USER_FOLDER = './mount/histories/'

Settings.llm = None
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L12-v2")

def get_saved_history(id):
    """Beolvassa és visszaadja a felhasználó előzményeit, ha létezik."""
    history_file_path = os.path.join(HISTORIES_BY_USER_FOLDER, f"{id}.json")

    if not os.path.exists(history_file_path):
        return None  # Ha nem létezik, `None`-t adunk vissza
    
    with open(history_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)  # Az előzményeket szótárként adjuk vissza

@app.route('/')
def home():
    return "API működik!", 200

@app.route('/history', methods=['POST'])
def get_history():
    """Végpont, amely visszaadja egy felhasználó előzményeit."""
    data = request.get_json()  
    
    if not data or 'user_id' not in data:
        return jsonify({"error": "No user_id provided"}), 400

    user_id = data['user_id']
    history = get_saved_history(user_id)

    if history is None:
        return jsonify({"error": "History does not exist for this user ID"}), 400

    return jsonify({"history": history}), 200

@app.route('/history_reset', methods=['POST'])
def reset_history():
    """Felhasználó előzményeinek törlése és alapértelmezett érték beállítása."""
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        return jsonify({"error": "No user_id provided"}), 400

    user_id = data['user_id']
    history_file_path = os.path.join(HISTORIES_BY_USER_FOLDER, f"{user_id}.json")

    # Beolvassuk az előzményeket, hogy ellenőrizzük, létezik-e a fájl
    if get_saved_history(user_id) is None:
        return jsonify({"error": "History does not exist for this user ID"}), 400

    # Új előzmények létrehozása
    new_history = [{"role": "system", "content": default_history}]

    # Fájl felülírása új adatokkal
    with open(history_file_path, 'w', encoding='utf-8') as file:
        json.dump(new_history, file, ensure_ascii=False, indent=4)

    return jsonify({"message": "History reset successfully"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    # Ellenőrzi, hogy van-e fájl a kérésben
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # Ellenőrzi, hogy van-e tényleges fájl
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Csak PDF fájlokat engedélyez
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Fájl mentése a szerverre
    input_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file_exists = os.path.exists(input_file_path)

    if file_exists:
        return jsonify({"error": "File already exists"}), 400
    
    file.save(input_file_path)

    # PDF feldolgozása
    try:
        doc = pymupdf.open(input_file_path)
        output_file_path = os.path.join(OUTPUT_FOLDER, file.filename.replace('.pdf', '.txt'))

        with open(output_file_path, 'w', encoding='utf-8') as f:
            for page in doc:
                text = page.get_text()
                f.write(text + '\n')
        
        # os.remove(input_file_path) # Törli a PDF fájlt

        with open(output_file_path, "r", encoding="utf-8") as f:
            txt = f.read()
        print("output file path\t\t:", output_file_path)

        is_folder_empty = not any(os.scandir(UPLOAD_VEKTOR_FOLDER))

        if is_folder_empty:
            helper.create_vector_database(txt, 512, limit_pe, f"{UPLOAD_VEKTOR_FOLDER}")

            # source = file.filename.replace('.pdf', '.txt')
            # history.append({"role": "system", "source": source})

            return jsonify({
                "message": f"File processed successfully. Files saved to {UPLOAD_FOLDER}, {OUTPUT_FOLDER}, {UPLOAD_VEKTOR_FOLDER}.",
                "output_folder": f"{UPLOAD_VEKTOR_FOLDER}"
            }), 200
        else:
            helper.append_vector_database(txt, 512, limit_pe, f"{UPLOAD_VEKTOR_FOLDER}")

            return jsonify({
                "message": f"File processed successfully. Vectors appended to {UPLOAD_VEKTOR_FOLDER}, files saved to {UPLOAD_FOLDER}, {OUTPUT_FOLDER}.",
                "output_file": f"{UPLOAD_VEKTOR_FOLDER}"
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    user_id = data.get('user_id', '')

    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400

    is_folder_empty = not any(os.scandir(UPLOAD_VEKTOR_FOLDER))

    if is_folder_empty:
        return jsonify({"error": "No documents uploaded yet"}), 400
    
    # Megpróbáljuk beolvasni a felhasználó előzményeit
    history = get_saved_history(user_id)

    if history is None:
        # Ha nincs előzmény, létrehozzuk az alapértelmezett history-t
        history = [{"role": "system", "content": default_history}]
        history_file_path = os.path.join(HISTORIES_BY_USER_FOLDER, f"{user_id}.json")
        with open(history_file_path, 'w', encoding='utf-8') as file:
            json.dump(history, file, ensure_ascii=False, indent=4)

    history_file_path = os.path.join(HISTORIES_BY_USER_FOLDER, f"{user_id}.json")

    # Hozzáadjuk a kérdést a history-hoz
    history.append({"role": "user", "content": question})

    try:
        # Kontextus lekérése a keresőből
        #content = searcher.get_contexts_old(file_name)
        content = searcher.get_contexts(f"{UPLOAD_VEKTOR_FOLDER}", question)
        print("CONTEXT\t\t\t:", content)
        #content = content.replace("\n", " ")  # Sorvége karakterek eltávolítása
        history.append({"role": "user", "content": content})  # System szerepkörben kontextus

        # Üzenet méretének csökkentése EZT ÁT KELL MAJD IRNI - LLAMAINDEX CHAT
        # reduced_message = helper.reduce_message_old(history, limit_pe, config["guard"]["max_history_items"], tokenizer)
        reduced_message = helper.reduce_message(history, max_history_tokens, config["guard"]["max_history_items"], tokenizer)
        print("REDUCED MESSAGE\t:", reduced_message)
        # Triton szerverhez való kérelem összeállítása
        payload = {
            "text_input": reduced_message,
            "max_tokens": config['triton']['max_tokens'],
            "temperature": config['triton']['temperature'],
            "stream": ("stream" in config['triton']['generation'])
        }

        # Kérelem küldése a Triton szerverhez
        response = requests.post(url, json=payload, stream=True)

        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        batch = json.loads(line.decode('utf-8').replace("data: ", ""))
                        if helper.cleaning_stream(batch):
                            full_response += batch.get('text_output', '')
                    except json.JSONDecodeError:
                        continue  # Ha nem sikerül JSON-ként beolvasni, ugrás a következőre

            history.append({"role": "assistant", "content": full_response})

            with open(history_file_path, 'w', encoding='utf-8') as file:
                json.dump(history, file, ensure_ascii=False, indent=4)
            # return jsonify({"response": full_response, "history": history}), 200
            return jsonify({"response": full_response}), 200
        else:
            return jsonify({"error": f"Triton server error: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  

# Konfig fájl betöltése
# with open('config.json', 'r', encoding='utf-8') as file:
with open('./mount/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
print("LOADED\t\t\t: config")

# Semantikus kereső betöltése
searcher.load_data(config['sources'])
print("SEARCHER\t\t:", searcher.SORUCES)

## Triton URL összerakása
# url = f"{config['triton']['host']}:{config['triton']['port']}/v2/{config['triton']['model']}/{config['triton']['generation']}"
url = f"{config['triton']['host']}:{config['triton']['port']}/v2/models/{config['triton']['model']}/{config['triton']['generation']}"
print("URL\t\t\t:", url)

## Tokenizer betöltése
tokenizer = AutoTokenizer.from_pretrained(config["tokenizer"])
print("TOKENIZER\t\t:", config["tokenizer"])

## Token limit betöltése és kiszámítása
autoconfig = AutoConfig.from_pretrained(config["tokenizer"])
limit_pe = autoconfig.max_position_embeddings - config["guard"]["reduce_max_position_embeddings"]
print("MAX TOKEN INPUT SIZE\t:", autoconfig.max_position_embeddings)

max_history_tokens = config["guard"]["max_history_tokens"]
print("MAX HISTORY TOKENS\t:", max_history_tokens)

default_history = config["chat history"][0]['content']

## history = []

## history.append({"role": "system", "content": default_history})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=20249)

## dockerhez másik image
## postgres sql
## sql alchemy, CLASS history - id, userid, history, timestamp (nemuszaj de szokták csinálni)

## can egy api ednpoint, pl lekérdezni az elmult 30 napot

## konextus lehetséges endpoint mikre jok
## 1 lépés
## pl elmult 30 nap -> kontextus + question -> lekérdező url
## 2 lépés
## lekérdező url -> adatok -> (nem megy bele a historyba) - de ez lesz az új kontextus -> ugyan az a question -> megvan a válasz és ez megy bele az historyba