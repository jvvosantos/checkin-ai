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
    import re, json5

    prompt = f"""
    Você é um assistente que extrai parâmetros de busca para um sistema de recomendação de restaurantes.
    Usuário disse: "{user_message}"

    Retorne um **objeto JSON válido somente**, com as seguintes chaves:
    - query (string ou null)
    - features (lista de strings)
    - min_rating (float)

    O JSON deve ser analisável com Python json.loads().
    Não inclua texto extra.

    Regras importantes:
    1. Se o usuário mencionar 'carne', 'bife', 'churrasco' → query = "churrasco".
    2. Se o usuário mencionar 'pizza', 'pizzaria' → query = "pizza".
    3. Se o usuário mencionar 'sushi', 'sushibar' → query = "sushi".
    4. Se o usuário mencionar 'barato', 'cheap', 'affordable' → adicione 'barato' a features, min_rating = 0.5.
    5. Se o usuário mencionar 'top', 'excelente', 'ótimo' → min_rating = 4.

    Exemplos:
    Usuário: "Quero comer pizza"
    JSON: {{"query": "pizza", "features": [], "min_rating": 0}}

    Usuário: "Quero comer pizza com cadeirinha de bebê"
    JSON: {{"query": "pizza", "features": ["cadeirinha de bebê"], "min_rating": 0}}

    Usuário: "Hoje estou doido por sushi, e preciso de estacionamento"
    JSON: {{"query": "sushi", "features": ["estacionamento"], "min_rating": 0}}

    Usuário: "Preciso encher a cara! Mas que seja um lugar barato por favor"
    JSON: {{"query": "bebida", "features": ["barato"], "min_rating": 0.5}}

    Usuário: "Estou afim de comer carne, mas tem que ser um lugar top!"
    JSON: {{"query": "churrasco", "features": [], "min_rating": 4}}
    """

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=128)

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(text)

    # 1️⃣ Try to extract JSON from model output
    try:
        json_text = re.search(r"\{.*\}", text, re.DOTALL).group()
        intent = json5.loads(json_text)
    except:
        intent = {"query": None, "features": [], "min_rating": 0, "max_distance_km": None, "lat": None, "lon": None}

    # 2️⃣ Hardcoded keyword extraction (query)
    query_keywords = {
        "pizza": ["pizza", "pizzaria"],
        "sushi": ["sushi", "sushibar"],
        "hambúrguer": ["hambúrguer", "burger", "hamburguer"],
        "churrasco": ["churrasco", "churrascaria"],
        "bebida": ["bebida", "cerveja", "drinks", "encher a cara", "alcoólico", "alcoolico"]
    }
    if not intent.get("query"):
        for key, kws in query_keywords.items():
            if any(re.search(kw, user_message, re.IGNORECASE) for kw in kws):
                intent["query"] = key
                break

    # 3️⃣ Hardcoded keyword extraction (features)
    feature_keywords = {
        "cadeirinha de bebê": ["cadeirinha", "bebê", "cadeirinha para bebê"],
        "estacionamento": ["estacionamento", "parking"],
        "romântico": ["romântico", "romantico"],
        "familiar": ["familiar", "kids", "família"],
        "barato": ["barato", "econômico", "economico"],
        "cartão visa": ["visa"],
        "cartão mastercard": ["mastercard"]
    }
    features = intent.get("features", [])
    for feature, kws in feature_keywords.items():
        if any(re.search(kw, user_message, re.IGNORECASE) for kw in kws):
            if feature not in features:
                features.append(feature)
    intent["features"] = features

    # 4️⃣ Ensure defaults for other keys (deterministic)
    for key in ["min_rating", "max_distance_km", "lat", "lon"]:
        if key not in intent or intent[key] is None:
            intent[key] = 0 if key == "min_rating" else None

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