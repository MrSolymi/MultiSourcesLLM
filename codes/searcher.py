from llama_index.core import StorageContext, load_index_from_storage

DATA = None
SORUCES = None

def load_data(sources):
    global SORUCES
    SORUCES = sources
    
    print("SEMANTIC SEARCH ENGINE\t: ready")

def get_contexts_old(file=""):
    try:
        with open(f"{SORUCES}/{file}", 'r', encoding='utf-8') as file:
            DATA = file.read()
            # print(DATA)

        return f"Kontextus:\n{str(DATA)}\n\n"
    except:
        return f"Kontextus: Nincs!"
    
def get_contexts(folder_name, q):
    try:
        storage_context = StorageContext.from_defaults(persist_dir=f"{folder_name}")
        index = load_index_from_storage(storage_context)
        
        resps = []
        
        query_engine = index.as_query_engine(similarity_top_k=3)

        print(f"--------------------{query_engine}")

        ## meglesni hogy van e valami treshold
        
        resps = get_response(query_engine.query(q).response)


        ##response_proba = query_engine.query(q)
        ### Print the results
        ##print(f"Query: {q}\n")
        ##print("Source details:")
        ##for node in response_proba.source_nodes:
        ##    text = node.text.replace('\n', " ")
        ##    print(f"Node ID: {node.node_id}\nScore: {node.score}\n{text[:200]}\n")
        

        return f"Kontextus:\n{str(resps)}\n\n"
    except Exception as e:
        return f"Kontextus: Nincs!"

def get_response(resp):
    return resp.split("\n---------------------\n")[1].split("\n\n")