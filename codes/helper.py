from llama_index.core import Document, VectorStoreIndex
from transformers import AutoTokenizer
from llama_index.core import StorageContext, load_index_from_storage

def cleaning_stream(batch):
    if len(batch['text_output']) == 0:
        return False
    elif batch['text_output'] == "\n\n":
        return False
    elif "<|start_header_id|>" in batch['text_output']:
        return False
    elif "assistant" in batch['text_output']:
        return False
    elif "<|end_header_id|>" in batch['text_output']:
        return False
    else:
        return True
    
def reduce_message_old(chat, max_len, num_limit, tokenizer):
    message = tokenizer.apply_chat_template(chat, tokenize=False)
    len_chat = len(tokenizer.encode(message))      
    while len_chat > max_len and len(chat) > num_limit:
        chat = chat[0:1] + chat[2:]

        message = tokenizer.apply_chat_template(chat, tokenize=False)
        len_chat = len(tokenizer.encode(message))
        # print(len_chat, chat)

    if len_chat < max_len:
        return message
    else:
        return ""
    
def reduce_message(chat, max_len, num_limit, tokenizer):
    # Apply the chat template to the initial chat history
    message = tokenizer.apply_chat_template(chat, tokenize=False)
    len_chat = len(tokenizer.encode(message))
    # Early exit if the initial message is within the limit
    if len_chat <= max_len:
        return message
    # Trim the chat history by removing the oldest messages first
    while len_chat > max_len and len(chat) > num_limit:
        # Remove the oldest user-assistant pair
        chat = chat[2:]  # Remove the first two messages (user and assistant)
        # Recalculate the message length
        message = tokenizer.apply_chat_template(chat, tokenize=False)
        len_chat = len(tokenizer.encode(message))
    # Return the reduced message if within the limit, otherwise return an empty string
    return message if len_chat <= max_len else ""


def create_vector_database(text, token_size, max_length, folder_name):
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")

    chunks = create_documents(tokenizer, text, max_length, token_size)

    index = VectorStoreIndex.from_documents(chunks)
    index.storage_context.persist(folder_name)

def append_vector_database(text, token_size, max_length, folder_name):
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")

    storage_context = StorageContext.from_defaults(persist_dir=f"{folder_name}")
    index_to_append = load_index_from_storage(storage_context)

    chunks = create_documents(tokenizer, text, max_length, token_size)
    
    index_to_append.insert_nodes(chunks)

    index_to_append.storage_context.persist(folder_name)

def create_documents(tokenizer, text, max_length, token_size):
    chunks = []
    tokens = tokenizer.tokenize(text, max_length=max_length, truncation=True)

    for i in range(0, len(tokens), token_size):
        chunk_tokens = tokens[i:i + token_size]
        chunk = tokenizer.convert_tokens_to_string(chunk_tokens)
        chunks.append(Document(text=chunk))
    
    return chunks
