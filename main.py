from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import httpx

app = FastAPI()

class CategoryRequest(BaseModel):
    category: str

MAX_PRICE = 1000

def generate_keywords(category):
    if category.lower() == "perfume":
        return [
            "parfum promo",
            "soldes parfum",
            "eau de parfum reduction",
            "luxury perfume discount",
            "clearance fragrance",
            "parfum 50% reduction",
            "niche parfum promo"
        ]
    if category.lower() == "jewelry":
        return [
            "bijoux soldes",
            "collier or reduction",
            "bracelet argent promo",
            "bague diamant soldes",
            "luxury jewelry discount",
            "montre luxe promo"
        ]
    return [category]

def parse_price(text):
    try:
        price = text.replace("€", "").replace(",", ".").strip()
        return float(price)
    except:
        return None

def search_notino(keyword):
    url = f"https://www.notino.fr/search.asp?exps={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    
    soup = BeautifulSoup(r.text, "lxml")
    products = soup.select(".product-item")
    
    results = []
    
    for p in products[:10]:
        try:
            title = p.select_one(".product-item-title").text.strip()
            price_text = p.select_one(".price").text
            price = parse_price(price_text)
            
            if price and price <= MAX_PRICE:
                results.append({
                    "title": title,
                    "price": price,
                    "link": "https://www.notino.fr"
                })
        except:
            continue
    
    return results

@app.get("/")
def root():
    return {"status": "Deal Finder API running"}

@app.post("/search")
def search_deals(data: CategoryRequest):
    keywords = generate_keywords(data.category)
    collected = []

    for kw in keywords:
        results = search_notino(kw)
        for item in results:
            collected.append(item)
        if len(collected) >= 6:
            break

    return {"category": data.category, "results": collected[:6]}
