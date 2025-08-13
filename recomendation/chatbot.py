from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
import requests
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------------
# Initialize FastAPI
# -----------------------------
app = FastAPI(title="Chatbot + Recommendations")

# -----------------------------
# Gemma Model Setup
# -----------------------------
MODEL_ID = "google/gemma-3-1b-it"  # or your verified checkpoint

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to("cpu")  # adjust device if GPU available

# -----------------------------
# Helper: Extract intent from user message
# -----------------------------
def extract_intent(user_message: str) -> dict:
    """
    Extract structured intent from a user message (Portuguese).
    Returns a dict with keys:
    - query (string or None)
    - features (list of strings)
    - min_rating (float)
    - max_distance_km (float or None)
    - lat (float or None)
    - lon (float or None)
    """
    
    prompt = f"""
Você é um assistente que extrai parâmetros de busca para um sistema de recomendação de restaurantes.
Usuário disse: "{user_message}"

Retorne um **objeto JSON válido somente**, com as seguintes chaves:
- query (string ou null)
- features (lista de strings)
- min_rating (float)
- max_distance_km (float ou null)
- lat (float ou null)
- lon (float ou null)

O JSON deve ser analisável com Python json.loads().
Não inclua texto extra.

Exemplos:
Usuário: "Quero comer pizza com estacionamento"
JSON: {{"query": "pizza", "features": ["estacionamento"], "min_rating": 0, "max_distance_km": null, "lat": null, "lon": null}}

Usuário: "Procurando sushi e um lugar romântico"
JSON: {{"query": "sushi", "features": ["romântico"], "min_rating": 0, "max_distance_km": null, "lat": null, "lon": null}}

Usuário: "Quero hambúrguer barato perto de mim"
JSON: {{"query": "hambúrguer", "features": ["barato"], "min_rating": 0, "max_distance_km": null, "lat": null, "lon": null}}
"""

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=128)

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    import json, re
    try:
        json_text = re.search(r"\{.*\}", text, re.DOTALL).group()
        intent = json.loads(json_text)
    except:
        intent = {
            "query": None,
            "features": [],
            "min_rating": 0,
            "max_distance_km": None,
            "lat": None,
            "lon": None
        }

    if intent["query"] is None:
        keywords = {
            "pizza": ["pizza", "pizzaria"],
            "sushi": ["sushi", "sushibar"],
            "hambúrguer": ["hambúrguer", "burger", "hamburguer"],
            "churrasco": ["churrasco", "churrascaria"],
        }
        for key, kw_list in keywords.items():
            for kw in kw_list:
                if re.search(kw, user_message, re.IGNORECASE):
                    intent["query"] = key
                    break
            if intent["query"]:
                break

    return intent

# -----------------------------
# Pydantic model for chat input
# -----------------------------
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[int] = None

# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
def chat(msg: ChatMessage):
    # 1️⃣ Extract intent via Gemma
    intent = extract_intent(msg.message)

    # 2️⃣ Call recommendations API
    rec_api_url = "http://127.0.0.1:8000/recommendations"  # adjust if hosted elsewhere
    try:
        resp = requests.post(rec_api_url, json=intent, timeout=5)
        restaurants = resp.json()
    except Exception as e:
        restaurants = []
    
    # 3️⃣ Return structured response
    return {
        "user_message": msg.message,
        "intent": intent,
        "recommendations": restaurants
    }