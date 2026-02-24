from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

# CORS (VERY IMPORTANT for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root test
@app.get("/")
async def root():
    return {"message": "GlitchPrice Finder backend is running."}


# TEST glitches route
@app.get("/glitches")
async def get_glitches(category: str = "general"):
    return {
        "items": [
            {
                "name": f"Test {category} Product",
                "description": "This is a fake glitch item (test mode).",
                "savingsPercentage": 65,
                "discountedPrice": 120,
                "nextBestPrice": {
                    "price": 300,
                    "store": "Amazon"
                },
                "url": "https://example.com",
                "category": category
            }
        ]
    }


@app.post("/verify")
async def verify_item(data: dict):
    return {
        "status": "available",
        "reason": "Test verification successful"
    }
