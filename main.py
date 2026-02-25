from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests

# ----- CONFIG -----
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"  # Your frontend URL
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant"

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

# ----- APP SETUP -----
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Only your frontend can call
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- MODELS -----
class VerifyRequest(BaseModel):
    url: str

# ----- ROUTES -----
@app.get("/")
def root():
    return {"message": "GlitchPrice Finder backend is running."}

@app.get("/glitches")
def get_glitches(category: str = "all"):
    prompt = f"Generate 5 keyword ideas for {category} products online deals."
    payload = {
        "model": MODEL,
        "input": prompt,
        "max_output_tokens": 200,
    }

    response = requests.post("https://api.groq.com/v1/generate", headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

    data = response.json()
    text = data.get("output_text", "")
    keywords = [kw.strip() for kw in text.split(",") if kw.strip()]

    items = [
        {
            "name": kw,
            "description": f"Keyword idea for {category}",
            "savingsPercentage": 0,
            "discountedPrice": 0,
            "nextBestPrice": {"price": 0, "store": ""},
            "url": "",
            "category": category
        }
        for kw in keywords
    ]

    return {"category": category, "items": items}

@app.post("/verify")
def verify_item(req: VerifyRequest):
    prompt = f"Verify if this product URL {req.url} is a good deal or glitch. Answer with 'verified' or 'unavailable' and a short reason."
    payload = {
        "model": MODEL,
        "input": prompt,
        "max_output_tokens": 50,
    }

    response = requests.post("https://api.groq.com/v1/generate", headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

    data = response.json()
    text = data.get("output_text", "unavailable: could not verify")
    
    if ":" in text:
        status, reason = [t.strip() for t in text.split(":", 1)]
    else:
        status, reason = "unavailable", text.strip()

    return {
        "status": status,
        "reason": reason
    }
