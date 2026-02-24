from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests

app = FastAPI()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class SearchRequest(BaseModel):
    category: str

def generate_keywords(category):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Generate 12 shopping search keywords in English and French
    related to this category: {category}.
    Only return a comma separated list.
    """

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    content = result["choices"][0]["message"]["content"]
    keywords = [k.strip() for k in content.split(",")]

    return keywords


@app.post("/search")
def search_products(request: SearchRequest):
    keywords = generate_keywords(request.category)

    return {
        "category": request.category,
        "generated_keywords": keywords
    }


@app.get("/")
def root():
    return {"status": "Groq backend running"}
