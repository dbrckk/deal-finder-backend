from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
from bs4 import BeautifulSoup
import time
import random
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORY_QUERIES = {
    "general": ["montre", "sac", "chaussure", "écouteurs", "parfum"],
    "tech": ["iphone", "pc portable", "airpods", "samsung", "tablette"],
    "outfit": ["sneakers", "sac cuir", "veste", "robe", "lunettes"],
    "jewelry": ["bague", "collier", "bracelet", "montre luxe", "parfum"],
    "nearfree": ["accessoire", "destockage", "clearance", "fin de serie", "promo"],
    "hugesaving": ["pc portable", "tv 4k", "iphone", "robot cuisine", "console"],
    "forher": ["sac femme", "chaussures femme", "lingerie", "bijoux femme", "robe"]
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

MAX_RESULTS = 5
MAX_KEYWORD_DEPTH = 3
MAX_PER_SITE = 20

# ------------------ Helpers ------------------ #

def extract_price(text):
    try:
        text = text.replace("€", "").replace(",", ".")
        text = ''.join(c for c in text if c.isdigit() or c == ".")
        return float(text)
    except:
        return None

def verify_availability(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return False
        text = r.text.lower()
        if "indisponible" in text or "rupture" in text or "out of stock" in text:
            return False
        return True
    except:
        return False

def compute_score(item):
    item["money_saved"] = round(item["old_price"] - item["price"], 2)
    item["score"] = (item["discount"] * 2) + (item["money_saved"] / 10)
    # Placeholder for coupon/cashback future integration
    item["coupon"] = None
    item["cashback"] = None
    return item

# ------------------ Search Functions ------------------ #

def search_cdiscount(keyword):
    url = f"https://www.cdiscount.com/search/10/{keyword}.html"
    products = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select(".lpMain .prdtBloc")
        for item in items[:MAX_PER_SITE]:
            title_tag = item.select_one(".prdtTitle")
            price_tag = item.select_one(".price")
            if not title_tag or not price_tag:
                continue
            price = extract_price(price_tag.text)
            if not price or price > 1000:
                continue
            old_price_tag = item.select_one(".strike")
            old_price = extract_price(old_price_tag.text) if old_price_tag else price * random.uniform(1.2, 1.8)
            discount = round((old_price - price) / old_price * 100, 2)
            if discount < 35:
                continue
            link = title_tag.get("href")
            if link and not link.startswith("http"):
                link = "https://www.cdiscount.com" + link
            product = {
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price, 2),
                "discount": discount,
                "website": "Cdiscount",
                "buy_link": link
            }
            products.append(compute_score(product))
        return products
    except:
        return []

def search_rakuten(keyword):
    url = f"https://www.rakuten.fr/s/{keyword}"
    products = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select(".search-result-item")
        for item in items[:MAX_PER_SITE]:
            title_tag = item.select_one(".title")
            price_tag = item.select_one(".main-price")
            if not title_tag or not price_tag:
                continue
            price = extract_price(price_tag.text)
            if not price or price > 1000:
                continue
            old_price_tag = item.select_one(".crossed-price")
            old_price = extract_price(old_price_tag.text) if old_price_tag else price * random.uniform(1.2, 1.7)
            discount = round((old_price - price) / old_price * 100, 2)
            if discount < 35:
                continue
            link = title_tag.get("href")
            if link and not link.startswith("http"):
                link = "https://www.rakuten.fr" + link
            product = {
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price, 2),
                "discount": discount,
                "website": "Rakuten",
                "buy_link": link
            }
            products.append(compute_score(product))
        return products
    except:
        return []

# --- Placeholder for other sites --- #
def search_fnac(keyword): return []
def search_boulanger(keyword): return []
def search_amazon(keyword): return []
def search_darty(keyword): return []
def search_ldlc(keyword): return []
def search_ebay(keyword): return []
def search_veepree(keyword): return []
def search_showroomprive(keyword): return []

# ------------------ SSE Stream Endpoint ------------------ #

@app.get("/search_stream")
def search_stream(category: str = "general"):
    if category not in CATEGORY_QUERIES:
        category = "general"

    verified_results = []
    scanned_count = 0

    def event_generator():
        for depth in range(MAX_KEYWORD_DEPTH):
            for keyword in CATEGORY_QUERIES[category]:
                candidates = []
                # Call all search functions
                candidates.extend(search_cdiscount(keyword))
                candidates.extend(search_rakuten(keyword))
                candidates.extend(search_fnac(keyword))
                candidates.extend(search_boulanger(keyword))
                candidates.extend(search_amazon(keyword))
                candidates.extend(search_darty(keyword))
                candidates.extend(search_ldlc(keyword))
                candidates.extend(search_ebay(keyword))
                candidates.extend(search_veepree(keyword))
                candidates.extend(search_showroomprive(keyword))

                # Sort by score
                candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

                for item in candidates:
                    if len(verified_results) >= MAX_RESULTS:
                        break
                    scanned_count += 1
                    if verify_availability(item["buy_link"]):
                        item["available"] = True
                        verified_results.append(item)
                        # send live
                        yield f"data:{json.dumps({'item': item, 'progress': len(verified_results), 'keyword': keyword})}\n\n"
                    time.sleep(1)

                if len(verified_results) >= MAX_RESULTS:
                    break
                time.sleep(2)

            if len(verified_results) >= MAX_RESULTS:
                break

        # Final message
        yield f"data:{json.dumps({'finished': True, 'total_found': len(verified_results)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
