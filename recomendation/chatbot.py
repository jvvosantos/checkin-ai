from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

# --- Config ---
RECOMMENDATION_API_URL = "http://localhost:8000/recommendations"
USE_LOCAL_GEMMA = True  # Set False to call Gemma API instead

# --- In-memory simple context storage (user_id -> conversation history) ---
conversation_contexts: Dict[str, List[str]] = {}

# --- Gemma local model init (if using local) ---
if USE_LOCAL_GEMMA:
    tokenizer = AutoTokenizer.from_pretrained("gpt2-medium")
    model = AutoModelForCausalLM.from_pretrained("gpt2-medium").to("cpu")

# --- Helper functions ---
def generate_gemma_reply(prompt: str) -> str:
    if USE_LOCAL_GEMMA:
        inputs = tokenizer(prompt, return_tensors="pt").to("cpu")
        outputs = model.generate(**inputs, max_length=100, do_sample=True, top_p=0.9)
        reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return reply
    else:
        # Call external Gemma API
        response = requests.post("http://gemma-api-host/generate", json={"prompt": prompt, "max_tokens": 100})
        return response.json().get("text", "Sorry, I didn't understand that.")

def simple_intent_and_entity_parse(message: str):
    # Very naive intent detection and entity extraction
    msg = message.lower()
    intent = "chat"
    entities = {}

    if any(x in msg for x in ["restaurant", "eat", "food", "pizza", "sushi", "cafe"]):
        intent = "recommendation"
        if "pizza" in msg:
            entities["query"] = "pizza"
        if "parking" in msg:
            entities.setdefault("features", []).append("parking")
        if "wifi" in msg:
            entities.setdefault("features", []).append("wifi")
        # Could expand with more parsing here

    return intent, entities

# --- Request / Response models ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- Chat endpoint ---
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Update conversation context (optional)
    ctx = conversation_contexts.setdefault(req.user_id, [])
    ctx.append(f"User: {req.message}")

    intent, entities = simple_intent_and_entity_parse(req.message)

    if intent == "recommendation":
        rec_payload = {
            "query": entities.get("query"),
            "features": entities.get("features"),
            "min_rating": 3.5,
            "limit": 5,
        }
        rec_response = requests.post(RECOMMENDATION_API_URL, json=rec_payload)
        recs = rec_response.json()

        if recs:
            reply = "I found some places you might like:\n"
            for r in recs:
                reply += f"- {r['name']} (Rating: {r['rating']}, Features: {r.get('features','N/A')})\n"
        else:
            reply = "Sorry, I couldn't find any matching places."

    else:
        # Use Gemma for chat responses
        prompt = " ".join(ctx[-6:]) + f"\nAI:"
        reply = generate_gemma_reply(prompt)

    # Append AI reply to context
    ctx.append(f"AI: {reply}")

    return ChatResponse(reply=reply)
