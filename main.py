from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import json
import time
import re
from typing import List, Dict, Any

app = FastAPI()

# Front‑end URL
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_ITEMS_PER_SITE = 3

# ------------ Category Keywords ------------

KEYWORDS_BY_CATEGORY = {
    "general": ["montre", "sac", "bijou", "chaussures", "parfum"],
    "tech": ["smartphone", "ordinateur", "casque", "tablette", "accessoire"],
    "nearfree": ["porte‑clé", "stickers", "mini gadget", "stylo", "coque téléphone"],
    "forher": ["sac à main", "bijou femme", "chaussures femme", "parfum femme", "lingerie"]
}

# ------------- Helper Functions ------------

def extract_price(text: str) -> float:
    try:
        return float(re.sub(r"[^\d.,]", "", text).replace(",", "."))
    except:
        return 0.0

def verify_availability(link: str) -> bool:
    try:
        headers = {"User‑Agent": "Mozilla/5.0"}
        r = requests.get(link, headers=headers, timeout=10)
        return r.status_code == 200 and "indisponible" not in r.text.lower()
    except:
        return False

# ------------ Site Parsers (10 sites) ------------

def parse_cdiscount(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".prdtBloc")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".prdtTitle a")
        price_tag = card.select_one(".price")
        old_tag = card.select_one(".prdtOldPrice")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = extract_price(old_tag.text) if old_tag else price
        discount = round((old_price − price) / old_price * 100, 2) if old_price > price else 0
        link = title_tag["href"] if title_tag.get("href") else ""
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": discount,
            "coupon": None,
            "cashback": None,
            "money_saved": round(old_price − price, 2),
            "score": discount,
            "website": "Cdiscount",
            "buy_link": link,
            "available": True
        })
    return items

def parse_amazon(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".s-result-item")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one("h2 .a‑size‑base")
        price_whole = card.select_one(".a‑price‑whole")
        price_fraction = card.select_one(".a‑price‑fraction")
        if not title_tag or not price_whole or not price_fraction:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_whole.text + "." + price_fraction.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Amazon FR",
            "buy_link": "https://www.amazon.fr" + card.select_one("h2 a")["href"],
            "available": True
        })
    return items

def parse_rakuten(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".search‑item")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one("h3 a")
        price_tag = card.select_one(".price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Rakuten",
            "buy_link": title_tag["href"],
            "available": True
        })
    return items

def parse_fnac(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".Article‑item")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".Article‑title")
        price_tag = card.select_one(".userPrice")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Fnac",
            "buy_link": "https://www.fnac.com" + title_tag.find_parent("a")["href"],
            "available": True
        })
    return items

def parse_boulanger(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".product‑item")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".product‑title")
        price_tag = card.select_one(".price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Boulanger",
            "buy_link": "https://www.boulanger.com" + card.select_one("a")["href"],
            "available": True
        })
    return items

def parse_darty(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".product‑card")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".product‑card‑title")
        price_tag = card.select_one(".product‑price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Darty",
            "buy_link": "https://www.darty.com" + card.select_one("a")["href"],
            "available": True
        })
    return items

def parse_ldlc(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".product")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".product‑title")
        price_tag = card.select_one(".price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "LDLC",
            "buy_link": "https://www.ldlc.com" + card.select_one("a")["href"],
            "available": True
        })
    return items

def parse_ebay(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".s‑item")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".s‑item__title")
        price_tag = card.select_one(".s‑item__price")
        link_tag = card.select_one(".s‑item__link")
        if not title_tag or not price_tag or not link_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "eBay FR",
            "buy_link": link_tag["href"],
            "available": True
        })
    return items

def parse_veepree(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".product‑card")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".product‑card‑title")
        price_tag = card.select_one(".product‑card‑price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Veepee",
            "buy_link": "https://fr.veepee.com" + card.select_one("a")["href"],
            "available": True
        })
    return items

def parse_showroomprive(html):
    items = []
    soup = BeautifulSoup(html, "lxml")
    for card in soup.select(".product‑card")[:MAX_ITEMS_PER_SITE]:
        title_tag = card.select_one(".product‑card‑title")
        price_tag = card.select_one(".product‑card‑price")
        if not title_tag or not price_tag:
            continue
        title = title_tag.text.strip()
        price = extract_price(price_tag.text)
        old_price = price
        items.append({
            "title": title,
            "price": price,
            "old_price": old_price,
            "discount": 0,
            "coupon": None,
            "cashback": None,
            "money_saved": 0,
            "score": 0,
            "website": "Showroomprive",
            "buy_link": "https://www.showroomprive.com" + card.select_one("a")["href"],
            "available": True
        })
    return items

# ------------- Website Config -------------

WEBSITES = [
    {"name": "Cdiscount", "search_url": "https://www.cdiscount.com/search/10/{keyword}.html", "parser": "parse_cdiscount"},
    {"name": "Amazon FR", "search_url": "https://www.amazon.fr/s?k={keyword}", "parser": "parse_amazon"},
    {"name": "Rakuten", "search_url": "https://www.rakuten.fr/s/{keyword}", "parser": "parse_rakuten"},
    {"name": "Fnac", "search_url": "https://www.fnac.com/SearchResult/ResultList.aspx?Search={keyword}", "parser": "parse_fnac"},
    {"name": "Boulanger", "search_url": "https://www.boulanger.com/resultats?search={keyword}", "parser": "parse_boulanger"},
    {"name": "Darty", "search_url": "https://www.darty.com/nav/recherche/{keyword}.html", "parser": "parse_darty"},
    {"name": "LDLC", "search_url": "https://www.ldlc.com/recherche/{keyword}/", "parser": "parse_ldlc"},
    {"name": "eBay FR", "search_url": "https://www.ebay.fr/sch/i.html?_nkw={keyword}", "parser": "parse_ebay"},
    {"name": "Veepee", "search_url": "https://fr.veepee.com/search/{keyword}", "parser": "parse_veepree"},
    {"name": "Showroomprive", "search_url": "https://www.showroomprive.com/search/{keyword}", "parser": "parse_showroomprive"}
]

# ------------- SSE Generator -------------

def event_generator(category: str):
    keywords = KEYWORDS_BY_CATEGORY.get(category, ["montre","sac","bijou"])
    found = []

    for keyword in keywords:
        for site in WEBSITES:
            try:
                url = site["search_url"].replace("{keyword}", keyword)
                headers = {"User‑Agent": "Mozilla/5.0"}
                r = requests.get(url, headers=headers, timeout=12)
                if r.status_code != 200:
                    continue
                parser_func = globals()[site["parser"]]
                items = parser_func(r.text)

                for item in items:
                    if len(found) < 5:
                        found.append(item)
                        yield f"data:{json.dumps({'item': item, 'progress': len(found), 'keyword': keyword})}\n\n"
                    else:
                        found.sort(key=lambda x: x["money_saved"], reverse=True)
                        found = found[:5]

            except:
                continue

        if len(found) >= 5:
            break

    yield f"data:{json.dumps({'finished':True,'total_found':len(found)})}\n\n"

            
@app.get("/search_stream")
async def search_stream(category: str="general"):
    return StreamingResponse(event_generator(category), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status":"ok"}
