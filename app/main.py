#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Optionnel pour le CORS

app = FastAPI(title="Food Truck API", version="0.1.0")

# Config CORS (optionnel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exemple de donnée temporaire (à remplacer par une vraie DB)
fake_menu = [
    {"id": 1, "name": "Cheeseburger", "price": 8.5, "options": []},
    {"id": 2, "name": "Frites", "price": 3.5, "options": []}
]

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API du Food Truck!"}
