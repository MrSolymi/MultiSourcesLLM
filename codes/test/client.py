import json
import socket
import pymupdf

# Object(s)
# with open('../mount/config.json', 'r', encoding='utf-8') as file:
with open('../mount/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

history = []

print("Hello, add meg a forrást:D")

# if not os.path.exists(source):
#     print(f"Hiba: A megadott fájl nem létezik: {source}")
#     exit()

user_input = input()
if ".txt" in user_input:
    source = user_input
elif ".pdf" in user_input:
    doc = pymupdf.open('../mount/' + user_input)

    output_file = '../mount/' + user_input.replace('.pdf', '.txt')

    with open(output_file, 'w', encoding='utf-8') as f:
        for page in doc:  # iterálunk a dokumentum oldalain
            text = page.get_text()  # kinyerjük az oldal szövegét
            f.write(text + '\n')  # szöveg hozzáadása a fájlhoz új sorral elválasztva
        
    input("Press Enter to continue...")

    source = user_input.replace('.pdf', '.txt')

    print(source + " létrehozva")

history.append({"source" : source})
print("Értettem:", source)

print("Mi a kérdésed?")

while True:
    question = input()
    if len(question) == 0:
        #continue
        print("")
    else:
        history.append({"role": "user", "content": question})
        # print(history)
        
        # Host beállítása
        if config["bridge"]["host"] == "0.0.0.0":
            host = "127.0.0.1"
        else:
            host = config["bridge"]["host"]
        
        # Kliens kapcsolat létrehozása és kérés küldése
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, config["bridge"]["port"]))
            message = json.dumps(history, ensure_ascii=False)
            # print(f"Küldés a szervernek: {question}")
            
            client_socket.sendall(message.encode('utf-8'))  # Kérdés küldése

            # Válasz stream fogadása
            full_response = ""
            while True:
                data = client_socket.recv(32)  # Válasz fogadása
                if not data:
                    break  # Ha nincs több adat, kilép a ciklusból
                full_response += data.decode('utf-8')
                print(data.decode('utf-8'), end='', flush=True)  # Részleges válasz kiírása a streamből
            
            history.append({"role": "assistant", "content": full_response})
            # print("\nTeljes válasz:", full_response)
    print("\n")
