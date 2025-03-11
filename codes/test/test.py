import os
from llama_index.core.llms import ChatMessage, MessageRole
from flask import jsonify
import json

history = []

with open('./mount/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

default_vmi = config["chat history"][0]['role']
print(default_vmi)

