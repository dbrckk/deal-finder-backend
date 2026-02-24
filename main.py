# src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

# ========================
# CORS
# ========================
origins = [
    "*",  # Allow all origins (mobile + web)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# DATA MODELS
# ========================
class GenerateRequest(BaseModel):
    category: str

class VerifyRequest(BaseModel):
    url: str

# ========================
# ENDPOINTS
# ========================

@app.post("/generate-keywords")
async def generate_keywords(req: GenerateRequest):
    """
    Simulate LLM-generated items for a category
    """
    try:
        category = req.category
        # Example: generate 5 fake items
        items = [f"{category.capitalize()} Deal {i+1}" for i in range(5)]
        return {"category": category, "generated_keywords": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify")
async def verify_item(req: VerifyRequest):
    """
    Simulate verification of URL stock
    """
    try:
        # Randomly decide if available
        status = random.choice(["available", "unavailable"])
        reason = "" if status == "available" else "Rupture de stock"
        return {"status": status, "reason": reason}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# ROOT
# ========================
@app.get("/")
async def root():
    return {"message": "GlitchPrice Finder backend is running."}
