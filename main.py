from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import random
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- CATEGORY KEYWORDS --------

CATEGORY_QUERIES = {
    "general": ["montre", "sac", "chaussure", "écouteurs", "parfum"],
    "tech": ["iphone", "pc portable", "airpods", "samsung", "tablette"],
    "outfit": ["sneakers", "sac cuir", "veste", "robe", "lunettes"],
    "jewelry": ["bague", "collier", "bracelet", "montre luxe", "parfum"],
    "nearfree": ["accessoire", "destockage", "clearance", "fin de serie", "promo"],
    "hugesaving": ["pc portable", "tv 4k", "iphone", "robot cuisine", "console"],
    "forher": ["sac femme", "chaussures femme", "lingerie", "bijoux femme", "robe"]
}

# -------- WEBSITES (max 50 later) --------

WEBSITES = [
    "https://www.cdiscount.com",
    "https://www.fnac.com",
    "https://www.rakuten.fr",
    "https://www.boulanger.com",
    "https://www.darty.com",
]

# -------- FAKE SEARCH SIMULATION (REAL SCRAPING LATER) --------

def simulate_search(keyword, website):
    """
    Temporary simulation to make system functional.
    Real scraping logic will replace this.
    """

    price = random.randint(10, 500)
    old_price = price + random.randint(20, 400)

    discount = round((old_price - price) / old_price * 100, 2)

    if discount < 40:
        return None

    return {
        "title": f"{keyword.title()} - {website.split('//')[1]}",
        "price": price,
        "old_price": old_price,
        "discount": discount,
        "website": website,
        "buy_link": website,
        "available": True
    }

# -------- MAIN SEARCH ENDPOINT --------

@app.get("/search")
def search(category: str = "general"):

    if category not in CATEGORY_QUERIES:
        category = "general"

    results = []

    for keyword in CATEGORY_QUERIES[category]:

        for website in WEBSITES:

            if len(results) >= 5:
                break

            item = simulate_search(keyword, website)

            if item:
                results.append(item)

            time.sleep(1)  # Slow scan to protect Render free

        if len(results) >= 5:
            break

    # If no glitch found → return 2 best fallback
    if len(results) == 0:
        for i in range(2):
            results.append({
                "title": f"Fallback Item {i+1}",
                "price": random.randint(50, 300),
                "old_price": random.randint(400, 700),
                "discount": 50,
                "website": "Various",
                "buy_link": "#",
                "available": True
            })

    return {"items": results}
