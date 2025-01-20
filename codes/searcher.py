DATA = None
SORUCES = None

def load_data(sources):
    global SORUCES
    SORUCES = sources
    
    print("SEMANTIC SEARCH ENGINE\t: ready")

def get_contexts(file=""):
    try:
        with open(f"{SORUCES}/{file}", 'r', encoding='utf-8') as file:
            DATA = file.read()
            # print(DATA)

        return f"Kontextus:\n{str(DATA)}\n\n"
    except:
        return f"Kontextus: Nincs!"