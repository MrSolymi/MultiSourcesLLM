import os
import json
import socket
import helper
import requests
import searcher

from transformers import AutoConfig
from transformers import AutoTokenizer

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  

# Object(s)

# Konfig fájl betöltése
# with open('config.json', 'r', encoding='utf-8') as file:
with open('./mount/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
print("LOADED\t\t\t: config")

# Semantikus kereső betöltése
searcher.load_data(config['sources'])
print("SEARCHER\t\t:", searcher.SORUCES)

## Triton URL összerakása
url = f"{config['triton']['host']}:{config['triton']['port']}/v2/{config['triton']['model']}/{config['triton']['generation']}"
print("URL\t\t\t:", url)

## Tokenizer betöltése
tokenizer = AutoTokenizer.from_pretrained(config["tokenizer"])
print("TOKENIZER\t\t:", config["tokenizer"])

## Token limit betöltése és kiszámítása
autoconfig = AutoConfig.from_pretrained(config["tokenizer"])
limit_pe = autoconfig.max_position_embeddings - config["guard"]["reduce_max_position_embeddings"]
print("MAX TOKEN INPUT SIZE\t:", autoconfig.max_position_embeddings)

# Main

## TCP szerver inicializálása
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((config["bridge"]["host"], config["bridge"]["port"]))
    server_socket.listen()
    print("SERVER\t\t\t: live",config["bridge"]["host"],config["bridge"]["port"])

    while True:
        client_socket, client_address = server_socket.accept()
        with client_socket:
            print(f"CONNECTION READY: {client_address}")

            ### Üzenet fogadása a kliens felől
            try:
                message = client_socket.recv(1000000).decode('utf-8')
                print(f"MESSAGE FROM CLIENT: {message}")
                message = json.loads(message)
            except:
                print("ERROR\t\t\t: TO LONG MESSAGE!")
                continue
            
            file_name = message[0]["source"]
            print("SOURCE\t\t\t:", file_name)

            history = message[1:]
            ### Alap chat beállítása
            chat = config["chat history"].copy()

            ### History hozzáadása
            if len(history) > 1:
                chat = chat + history[:-1]
            chat.append({"role": "assistant", "content": "Értem az előzményeket!"})

            ### Contextus hozzáadsa
            content = searcher.get_contexts(file_name)
            print("CONTENT\t\t\t:", content[:25].replace("\n", " "))
            chat.append({"role": "user", "content": content})
            chat.append({"role": "assistant", "content": "Értem a kontextust és használni fogom a válaszhoz!"})

            ### Ha a kérdés megfelelő. Tehát arra kérdez amire a modell válaszolhat.
            print("SERVER RESPONSE:")
            
            #### Új kérdés hozzáadása
            chat.append(message[-1])

            #### megerősítés hozzáadása
            chat[-1]["content"] = chat[-1]["content"] + config["guard"]["reinforce"]
            
            #### Üzenet létrehozzása limit határon belül
            reduced_message = helper.reduce_message(chat, limit_pe, config["guard"]["max_history_items"], tokenizer)
            print(f"MESSAGE TO MODEL: {reduced_message[:25]}...")
            # print(f"MESSAGE TO MODEL: {reduced_message}...")

            #### Triton kérés összeállítása
            payload = {
                "text_input": reduced_message,
                "max_tokens": config['triton']['max_tokens'],
                "temperature": config['triton']['temperature'],
                "stream": ("stream" in config['triton']['generation'])
            }
                    
            #### Kérelem küldése Triton szerverhez és stream feldolgozása
            with requests.post(url, json=payload, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            batch = json.loads(line.decode('utf-8').replace("data: ", ""))
                            ##### Válaszból kitisztitjuk a templétet jelölő karaktereket.
                            if helper.cleaning_stream(batch):
                                ###### Stream válasz küldése a kliens felé
                                client_socket.sendall(batch['text_output'].encode('utf-8'))
                else:
                    error_message = f"ERROR MESSAGE: {response.status_code}"
                    print(error_message)
                    print(config["guard"]["server error"])
                    client_socket.sendall(config["guard"]["server error"].encode('utf-8'))