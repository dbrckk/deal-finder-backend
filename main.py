from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import random

app = FastAPI()

class CategoryRequest(BaseModel):
    category: str

def generate_keywords(category):
    base_words = {
        "perfume": ["parfum", "eau de parfum", "fragrance", "luxury perfume", "niche parfum", "discount parfum", "promo parfum", "soldes parfum", "designer fragrance", "clearance parfum"],
        "jewelry": ["bijoux", "collier or", "bracelet argent", "bague diamant", "montre luxe", "pendentif", "promo bijoux", "soldes bijoux", "luxury jewelry", "clearance jewelry"]
    }
    return base_words.get(category.lower(), [category])

def fake_scrape(keyword):
    # Temporary simulated scraping
    price = random.randint(50, 900)
    original = random.randint(price + 100, price + 600)
    discount = int((original - price) / original * 100)
    saving = original - price
    
    if discount >= 40 or saving >= 300:
        return {
            "title": f"{keyword} deal",
            "price": price,
            "original_price": original,
            "discount_percent": discount,
            "saving": saving,
            "link": "https://example.com/product",
            "available": True
        }
    return None

@app.get("/")
def root():
    return {"status": "Deal Finder API running"}

@app.post("/search")
def search_deals(data: CategoryRequest):
    keywords = generate_keywords(data.category)
    results = []
    
    for keyword in keywords:
        deal = fake_scrape(keyword)
        if deal:
            results.append(deal)
        if len(results) == 6:
            break
    
    return {"category": data.category, "deals": results}
