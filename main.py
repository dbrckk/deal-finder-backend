from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI()

class CategoryRequest(BaseModel):
    category: str

@app.get("/")
def root():
    return {"status": "Deal Finder API running"}

@app.post("/search")
def search_deals(data: CategoryRequest):
    category = data.category
    
    # Placeholder response for now
    deals = [
        {
            "title": f"{category} Product {i}",
            "price": random.randint(50, 500),
            "original_price": random.randint(600, 900),
            "discount_percent": random.randint(40, 70),
            "saving": random.randint(300, 600),
            "link": "https://example.com/product",
            "available": True
        }
        for i in range(1, 7)
    ]
    
    return {"category": category, "deals": deals}
