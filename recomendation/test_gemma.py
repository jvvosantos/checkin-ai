from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "google/gemma-3-1b-it"


tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",  # Uses GPU if available, otherwise CPU
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

user_input = "I want a place to eat pizza near the beach"

prompt = f"""You are a helpful assistant. 
The user will ask about restaurants, and you will respond with only the food type they want.

User: {user_input}
Assistant:"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.inference_mode():
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.3,
        do_sample=False
    )


response = tokenizer.decode(outputs[0], skip_special_tokens=True)

answer = response.split("Assistant:")[-1].strip()
print("Model output:", answer)