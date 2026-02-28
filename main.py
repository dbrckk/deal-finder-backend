from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import json
import time
from typing import List, Dict, Any
import re

app = FastAPI()

# Front-end URL
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_ITEMS_PER_SITE = 3

# ----------------------------
# --- Category Keywords ------
# ----------------------------
KEYWORDS_BY_CATEGORY = {
    "general": ["montre", "sac", "bijou", "chaussures", "parfum"],
    "tech": ["smartphone", "ordinateur", "casque", "tablette", "accessoire"],
    "nearfree": ["porte-clé", "stickers", "mini gadget", "stylo", "coque téléphone"],
    "forher": ["sac à main", "bijou femme", "chaussures femme", "parfum femme", "lingerie"]
}

# ----------------------------
# --- Website Parsers --------
# ----------------------------
def parse_cdiscount(html):
    items = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".product")[:MAX_ITEMS_PER_SITE]:
            title_tag = card.select_one(".prdtBTit a")
            price_tag = card.select_one(".prdtPrSt")
            old_price_tag = card.select_one(".prdtPrOld")
            if not title_tag or not price_tag:
                continue
            title = title_tag.text.strip()
            price = float(re.sub(r"[^\d,.]", "", price_tag.text).replace(",", "."))
            old_price = float(re.sub(r"[^\d,.]", "", old_price_tag.text).replace(",", ".")) if old_price_tag else price
            discount = round((old_price - price) / old_price * 100, 2) if old_price > price else 0
            coupon = None  # Placeholder, can add scraping coupon
            items.append({
                "title": title,
                "price": price,
                "old_price": old_price,
                "discount": discount,
                "coupon": coupon,
                "cashback": None,
                "money_saved": old_price - price,
                "score": discount,
                "website": "Cdiscount",
                "buy_link": title_tag.get("href"),
                "available": True
            })
    except:
        pass
    return items

def parse_amazon(html):
    items = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select(".s-result-item")[:MAX_ITEMS_PER_SITE]:
            title_tag = card.select_one("h2 a span")
            price_whole = card.select_one(".a-price-whole")
            price_frac = card.select_one(".a-price-fraction")
            if not title_tag or not price_whole or not price_frac:
                continue
            title = title_tag.text.strip()
            price = float(price_whole.text.replace(",", "") + "." + price_frac.text)
            old_price = price  # Amazon doesn’t always show old price
            discount = 0
            coupon = None
            items.append({
                "title": title,
                "price": price,
                "old_price": old_price,
                "discount": discount,
                "coupon": coupon,
                "cashback": None,
                "money_saved": 0,
                "score": discount,
                "website": "Amazon FR",
                "buy_link": "https://www.amazon.fr" + card.select_one("h2 a")["href"],
                "available": True
            })
    except:
        pass
    return items

def parse_rakuten(html):
    return []  # Placeholder: can implement full parser later

def parse_fnac(html):
    return []

def parse_boulanger(html):
    return []

def parse_darty(html):
    return []

def parse_ldlc(html):
    return []

def parse_ebay(html):
    return []

def parse_veepree(html):
    return []

def parse_showroomprive(html):
    return []

# ----------------------------
# --- Websites ---------------
# ----------------------------
WEBSITES = [
    {"name": "Cdiscount", "search_url": "https://www.cdiscount.com/search/10/{keyword}.html", "parser": "parse_cdiscount"},
    {"name": "Rakuten", "search_url": "https://www.rakuten.com/search/{keyword}", "parser": "parse_rakuten"},
    {"name": "Fnac", "search_url": "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search={keyword}", "parser": "parse_fnac"},
    {"name": "Amazon FR", "search_url": "https://www.amazon.fr/s?k={keyword}", "parser": "parse_amazon"},
    {"name": "Boulanger", "search_url": "https://www.boulanger.com/resultats?search={keyword}", "parser": "parse_boulanger"},
    {"name": "Darty", "search_url": "https://www.darty.com/nav/recherche/{keyword}", "parser": "parse_darty"},
    {"name": "LDLC", "search_url": "https://www.ldlc.com/recherche/{keyword}/", "parser": "parse_ldlc"},
    {"name": "eBay FR", "search_url": "https://www.ebay.fr/sch/i.html?_nkw={keyword}", "parser": "parse_ebay"},
    {"name": "Veepee", "search_url": "https://fr.veepee.com/search/{keyword}", "parser": "parse_veepree"},
    {"name": "Showroomprive", "search_url": "https://www.showroomprive.com/search/{keyword}", "parser": "parse_showroomprive"}
]

# ----------------------------
# --- SSE Generator ----------
# ----------------------------
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
                    # Keep only top 5 items
                    if len(found_items) < 5:
                        found_items.append(item)
                        yield f"data: {json.dumps({'item': item, 'progress': len(found_items), 'keyword': keyword})}\n\n"
                    else:
                        found_items.sort(key=lambda x: x["money_saved"], reverse=True)
                        found_items = found_items[:5]
            except:
                continue
        # Stop early if top 5 found
        if len(found_items) >= 5:
            break

    # Finished signal
    yield f"data: {json.dumps({'finished': True, 'total_found': len(found_items)})}\n\n"

# ----------------------------
# --- Routes -----------------
# ----------------------------
@app.get("/search_stream")
async def search_stream(category: str = "general"):
    return StreamingResponse(event_generator(category), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok"}
