from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Any

app = FastAPI()

# Your front-end URL
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Websites to scrape (example, expand up to 50+)
WEBSITES = [
    {"name": "Cdiscount", "search_url": "https://www.cdiscount.com/search/10/{keyword}.html", "parser": "parse_cdiscount"},
    {"name": "Rakuten", "search_url": "https://www.rakuten.com/search/{keyword}", "parser": "parse_rakuten"},
    {"name": "Fnac", "search_url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search={keyword}", "parser": "parse_fnac"},
    {"name": "Amazon FR", "search_url": "https://www.amazon.fr/s?k={keyword}", "parser": "parse_amazon"},
    {"name": "Boulanger", "search_url": "https://www.boulanger.com/resultats?search={keyword}", "parser": "parse_boulanger"},
    {"name": "Darty", "search_url": "https://www.darty.com/nav/recherche/{keyword}", "parser": "parse_darty"},
    # Add more websites here
]

# Category keywords
KEYWORDS_BY_CATEGORY = {
    "general": ["montre", "sac", "bijou", "chaussures", "parfum"],
    "tech": ["smartphone", "ordinateur", "casque", "tablette", "accessoire"],
    "nearfree": ["porte-clé", "stickers", "mini gadget", "stylo", "coque téléphone"],
    "forher": ["sac à main", "bijou femme", "chaussures femme", "parfum femme", "lingerie"]
}

MAX_ITEMS_PER_SITE = 3

# Example parsers (expand each parser to real selectors per site)
def parse_cdiscount(html):
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select(".product-card")[:MAX_ITEMS_PER_SITE]:
        try:
            title_tag = card.select_one("a")
            price_tag = card.select_one(".price")
            old_price_tag = card.select_one(".old-price")
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
                "website": "Cdiscount",
                "buy_link": title_tag.get("href"),
                "available": True
            })
        except:
            continue
    return items

def parse_rakuten(html):
    # Placeholder parser, implement real scraping
    return []

def parse_fnac(html):
    # Placeholder parser, implement real scraping
    return []

def parse_amazon(html):
    # Placeholder parser, implement real scraping
    return []

def parse_boulanger(html):
    return []

def parse_darty(html):
    return []

# SSE generator
def event_generator(category: str):
    keywords = KEYWORDS_BY_CATEGORY.get(category, ["montre", "sac", "bijou"])
    found_items = []

    for keyword in keywords:
        for site in WEBSITES:
            try:
                url = site["search_url"].replace("{keyword}", keyword)
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue

                parser_func = globals()[site["parser"]]
                items = parser_func(response.text)

                for item in items:
                    if len(found_items) < 5:
                        found_items.append(item)
                        yield f"data: {json.dumps({'item': item, 'progress': len(found_items), 'keyword': keyword})}\n\n"
                    else:
                        found_items.sort(key=lambda x: x["money_saved"], reverse=True)
                        found_items = found_items[:5]
            except:
                continue

        if len(found_items) >= 5:
            break

    yield f"data: {json.dumps({'finished': True, 'total_found': len(found_items)})}\n\n"

# SSE endpoint
@app.get("/search_stream")
async def search_stream(category: str = "general"):
    return StreamingResponse(event_generator(category), media_type="text/event-stream")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}
