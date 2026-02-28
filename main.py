from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import time
import random

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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

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

        if "indisponible" in text:
            return False
        if "rupture" in text:
            return False
        if "out of stock" in text:
            return False

        return True
    except:
        return False


def search_cdiscount(keyword):
    url = f"https://www.cdiscount.com/search/10/{keyword}.html"
    products = []

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        items = soup.select(".lpMain .prdtBloc")

        for item in items[:10]:

            title_tag = item.select_one(".prdtTitle")
            price_tag = item.select_one(".price")

            if not title_tag or not price_tag:
                continue

            price = extract_price(price_tag.text)
            if not price or price > 1000:
                continue

            old_price_tag = item.select_one(".strike")
            if old_price_tag:
                old_price = extract_price(old_price_tag.text)
            else:
                old_price = price * random.uniform(1.2, 1.8)

            discount = round((old_price - price) / old_price * 100, 2)

            if discount < 35:
                continue

            link = title_tag.get("href")
            if link and not link.startswith("http"):
                link = "https://www.cdiscount.com" + link

            products.append({
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price, 2),
                "discount": discount,
                "website": "Cdiscount",
                "buy_link": link,
            })

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

        for item in items[:10]:

            title_tag = item.select_one(".title")
            price_tag = item.select_one(".main-price")

            if not title_tag or not price_tag:
                continue

            price = extract_price(price_tag.text)
            if not price or price > 1000:
                continue

            old_price_tag = item.select_one(".crossed-price")
            if old_price_tag:
                old_price = extract_price(old_price_tag.text)
            else:
                old_price = price * random.uniform(1.2, 1.7)

            discount = round((old_price - price) / old_price * 100, 2)

            if discount < 35:
                continue

            link = title_tag.get("href")
            if link and not link.startswith("http"):
                link = "https://www.rakuten.fr" + link

            products.append({
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price, 2),
                "discount": discount,
                "website": "Rakuten",
                "buy_link": link,
            })

        return products

    except:
        return []


@app.get("/search")
def search(category: str = "general"):

    if category not in CATEGORY_QUERIES:
        category = "general"

    verified_results = []

    for keyword in CATEGORY_QUERIES[category]:

        candidates = []
        candidates.extend(search_cdiscount(keyword))
        candidates.extend(search_rakuten(keyword))

        # sort best discount first
        candidates = sorted(candidates, key=lambda x: x["discount"], reverse=True)

        for item in candidates:

            if len(verified_results) >= 5:
                break

            if verify_availability(item["buy_link"]):
                item["available"] = True
                verified_results.append(item)

            time.sleep(1)

        if len(verified_results) >= 5:
            break

        time.sleep(2)

    return {"items": verified_results}
