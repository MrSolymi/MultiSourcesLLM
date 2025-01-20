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
    
def reduce_message(chat, max_len, num_limit, tokenizer):
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