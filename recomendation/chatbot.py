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
    Returns a dict with structured intent.
    Example: {"query": "pizza", "features": ["parking"], "min_rating": 4.0}
    """
    prompt = f"""
You are an assistant that extracts search parameters for a restaurant recommendation system.
User said: "{user_message}"

Return a **valid JSON object only**, with the following keys:
- query (string or null)
- features (list of strings)
- min_rating (float)
- max_distance_km (float or null)
- lat (float or null)
- lon (float or null)

The JSON must be parsable by Python's json.loads().
Do not include any extra text.

Examples:
User: "I want pizza with parking nearby"
JSON: {{"query": "pizza", "features": ["parking"], "min_rating": 0, "max_distance_km": null, "lat": null, "lon": null}}

User: "Looking for sushi and a romantic place"
JSON: {{"query": "sushi", "features": ["romantic"], "min_rating": 0, "max_distance_km": null, "lat": null, "lon": null}}
"""

    # Tokenize and generate
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=128)

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Try to extract first JSON object
    import json, re
    try:
        json_text = re.search(r"\{.*\}", text, re.DOTALL).group()
        intent = json.loads(json_text)
    except:
        # fallback defaults
        intent = {
            "query": None,
            "features": [],
            "min_rating": 0,
            "max_distance_km": None,
            "lat": None,
            "lon": None
        }

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