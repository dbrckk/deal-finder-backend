from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Any

app = FastAPI()

# Replace with your front-end URL
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Define the websites and their search URLs (expandable)
WEBSITES = [
    {"name": "Cdiscount", "search_url": "https://www.cdiscount.com/search/10/{keyword}.html"},
    {"name": "Rakuten", "search_url": "https://www.rakuten.com/search/{keyword}"},
    {"name": "Fnac", "search_url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search={keyword}"},
    {"name": "Amazon FR", "search_url": "https://www.amazon.fr/s?k={keyword}"},
    {"name": "Boulanger", "search_url": "https://www.boulanger.com/resultats?search={keyword}"},
    {"name": "Darty", "search_url": "https://www.darty.com/nav/recherche/{keyword}"}
]

# Maximum items per website
MAX_ITEMS_PER_SITE = 3

# Helper function to scrape one website
def scrape_website(site: Dict[str, str], keyword: str) -> List[Dict[str, Any]]:
    items = []
    try:
        url = site["search_url"].replace("{keyword}", keyword)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return items
        soup = BeautifulSoup(response.text, "lxml")

        # Example scraping logic (needs customization per website)
        product_cards = soup.find_all("div", class_="product-card")[:MAX_ITEMS_PER_SITE]
        for card in product_cards:
            try:
                title_tag = card.find("a")
                price_tag = card.find("span", class_="price")
                old_price_tag = card.find("span", class_="old-price")
                if not title_tag or not price_tag:
                    continue
                title = title_tag.text.strip()
                price = float(price_tag.text.replace("€","").replace(",","."))
                old_price = float(old_price_tag.text.replace("€","").replace(",", ".")) if old_price_tag else price
                discount = round((old_price - price) / old_price * 100, 2) if old_price > price else 0
                items.append({
                    "title": title,
                    "price": price,
                    "old_price": old_price,
                    "discount": discount,
                    "coupon": None,
                    "cashback": None,
                    "money_saved": old_price - price,
                    "score": discount,
                    "website": site["name"],
                    "buy_link": title_tag.get("href"),
                    "available": True
                })
            except:
                continue
    except:
        pass
    return items

# SSE endpoint
@app.get("/search_stream")
async def search_stream(category: str = "general"):
    keywords_per_category = {
        "general": ["montre", "sac", "bijou", "chaussures", "parfum"],
        "tech": ["smartphone", "ordinateur", "casque", "tablette", "accessoire"],
        "nearfree": ["porte-clé", "stickers", "mini gadget", "stylo", "coque téléphone"],
        "forher": ["sac à main", "bijou femme", "chaussures femme", "parfum femme", "lingerie"]
    }
    keywords = keywords_per_category.get(category, ["montre", "sac", "bijou"])

    def event_generator():
        found_items = []
        for keyword in keywords:
            for site in WEBSITES:
                scraped_items = scrape_website(site, keyword)
                for item in scraped_items:
                    # Only keep top 5 items by discount or savings
                    if len(found_items) < 5:
                        found_items.append(item)
                        yield f"data: {json.dumps({'item': item, 'progress': len(found_items), 'keyword': keyword})}\n\n"
                    else:
                        # Keep best 5
                        found_items.sort(key=lambda x: x["money_saved"], reverse=True)
                        found_items = found_items[:5]
                time.sleep(1)  # small delay to avoid blocking
            if len(found_items) >= 5:
                break
        yield f"data: {json.dumps({'finished': True, 'total_found': len(found_items)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}
