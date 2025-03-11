import json
import socket
import pymupdf
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = '../mount/'
OUTPUT_FOLDER = '../mount/'

# Object(s)
# with open('../mount/config.json', 'r', encoding='utf-8') as file:
with open('../mount/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

history = []

@app.route('/')
def home():
    return "API működik!", 200

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

        source = file.filename.replace('.pdf', '.txt')
        history.append({"source": source})

        return jsonify({
            "message": f"File processed successfully. Text saved to {output_file_path}.",
            "output_file": output_file_path,
            "history": history
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500






# print("Hello, add meg a forrást")

# if not os.path.exists(source):
#     print(f"Hiba: A megadott fájl nem létezik: {source}")
#     exit()

# user_input = input()
# if ".txt" in user_input:
#     source = user_input
# elif ".pdf" in user_input:
#     doc = pymupdf.open('../mount/' + user_input)
# 
#     output_file = '../mount/' + user_input.replace('.pdf', '.txt')
# 
#     with open(output_file, 'w', encoding='utf-8') as f:
#         for page in doc:  # iterálunk a dokumentum oldalain
#             text = page.get_text()  # kinyerjük az oldal szövegét
#             f.write(text + '\n')  # szöveg hozzáadása a fájlhoz új sorral elválasztva
#         
#     ##input("Press Enter to continue...")
# 
#     source = user_input.replace('.pdf', '.txt')
# 
#     print(source + " létrehozva")

# history.append({"source" : source})
# print("Értettem:", source)

# print("Mi a kérdésed?")

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    history.append({"role": "user", "content": question})

    try:
        if config["bridge"]["host"] == "0.0.0.0":
            host = "127.0.0.1"
        else:
            host = config["bridge"]["host"]
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, config["bridge"]["port"]))
            message = json.dumps(history, ensure_ascii=False)
            
            client_socket.sendall(message.encode('utf-8'))

            full_response = ""
            while True:
                data = client_socket.recv(32)
                if not data:
                    break
                full_response += data.decode('utf-8')

            history.append({"role": "assistant", "content": full_response})
            return jsonify({"response": full_response, "history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#while True:
#    question = input()
#    if len(question) == 0:
#        #continue
#        print("")
#    else:
#        history.append({"role": "user", "content": question})
#        # print(history)
#        
#        # Host beállítása
#        if config["bridge"]["host"] == "0.0.0.0":
#            host = "127.0.0.1"
#        else:
#            host = config["bridge"]["host"]
#        
#        # Kliens kapcsolat létrehozása és kérés küldése
#        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#            client_socket.connect((host, config["bridge"]["port"]))
#            message = json.dumps(history, ensure_ascii=False)
#            # print(f"Küldés a szervernek: {question}")
#            
#            client_socket.sendall(message.encode('utf-8'))  # Kérdés küldése
#
#            # Válasz stream fogadása
#            full_response = ""
#            while True:
#                data = client_socket.recv(32)  # Válasz fogadása
#                if not data:
#                    break  # Ha nincs több adat, kilép a ciklusból
#                full_response += data.decode('utf-8')
#                print(data.decode('utf-8'), end='', flush=True)  # Részleges válasz kiírása a streamből
#            
#            history.append({"role": "assistant", "content": full_response})
#            # print("\nTeljes válasz:", full_response)
#    print("\n")
#

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=20249)