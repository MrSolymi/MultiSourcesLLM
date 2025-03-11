#!/bin/sh

# Backend indítása és logolása
python server.py >> /msllm/logs/msllm.log 2>&1 &

# Frontend indítása és logolása
# cd /msllm/frontend

# npm install  # Csak ha kell, lehet kihagyni
# npm run dev >> /msllm/logs/frontend.log 2>&1