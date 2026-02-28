from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import json
import re
import time
from typing import List, Dict

app = FastAPI()

# ==============================
# CONFIG
# ==============================

FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_ITEMS_PER_SITE = 3
MAX_FINAL_ITEMS = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ==============================
# CATEGORY KEYWORDS
# ==============================

KEYWORDS_BY_CATEGORY = {
    "general": ["montre", "sac", "bijou", "chaussures", "parfum"],
    "tech": ["smartphone", "ordinateur", "casque", "tablette", "console"],
    "nearfree": ["porte clé", "coque téléphone", "mini gadget", "stylo"],
    "forher": ["sac à main", "bijou femme", "lingerie", "parfum femme"],
}

# ==============================
# HELPER FUNCTIONS
# ==============================

def clean_price(text: str) -> float:
    try:
        price = re.sub(r"[^\d,\.]", "", text)
        price = price.replace(",", ".")
        return float(price)
    except:
        return 0.0


def verify_product(link: str) -> bool:
    try:
        r = requests.get(link, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return False
        content = r.text.lower()
        if "indisponible" in content or "rupture" in content:
            return False
        return True
    except:
        return False


def build_item(title, price, old_price, link, website):
    discount = 0
    money_saved = 0

    if old_price > price:
        discount = round((old_price - price) / old_price * 100, 2)
        money_saved = round(old_price - price, 2)

    return {
        "title": title,
        "price": price,
        "old_price": old_price,
        "discount": discount,
        "money_saved": money_saved,
        "website": website,
        "buy_link": link,
        "available": True,
        "coupon": None,
        "cashback": None,
        "score": discount + money_saved
    }


# ==============================
# SCRAPERS
# ==============================

def scrape_amazon(keyword):
    url = f"https://www.amazon.fr/s?k={keyword}"
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for card in soup.select(".s-result-item")[:MAX_ITEMS_PER_SITE]:
            title_tag = card.select_one("h2 a span")
            price_whole = card.select_one(".a-price-whole")
            price_frac = card.select_one(".a-price-fraction")

            if not title_tag or not price_whole or not price_frac:
                continue

            title = title_tag.text.strip()
            price = clean_price(price_whole.text + "." + price_frac.text)
            link = "https://www.amazon.fr" + card.select_one("h2 a")["href"]

            item = build_item(title, price, price, link, "Amazon FR")
            items.append(item)

    except:
        pass

    return items


def scrape_ebay(keyword):
    url = f"https://www.ebay.fr/sch/i.html?_nkw={keyword}"
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for card in soup.select(".s-item")[:MAX_ITEMS_PER_SITE]:
            title_tag = card.select_one(".s-item__title")
            price_tag = card.select_one(".s-item__price")
            link_tag = card.select_one(".s-item__link")

            if not title_tag or not price_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            price = clean_price(price_tag.text)
            link = link_tag["href"]

            item = build_item(title, price, price, link, "eBay FR")
            items.append(item)

    except:
        pass

    return items


def scrape_cdiscount(keyword):
    url = f"https://www.cdiscount.com/search/10/{keyword}.html"
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for card in soup.select(".prdtBloc")[:MAX_ITEMS_PER_SITE]:
            title_tag = card.select_one(".prdtTitle a")
            price_tag = card.select_one(".price")

            if not title_tag or not price_tag:
                continue

            title = title_tag.text.strip()
            price = clean_price(price_tag.text)
            link = title_tag["href"]

            item = build_item(title, price, price, link, "Cdiscount")
            items.append(item)

    except:
        pass

    return items


# ==============================
# WEBSITE LIST
# ==============================

SCRAPERS = [
    scrape_amazon,
    scrape_ebay,
    scrape_cdiscount,
]

# ==============================
# SSE STREAM
# ==============================

def stream_results(category: str):

    keywords = KEYWORDS_BY_CATEGORY.get(category, KEYWORDS_BY_CATEGORY["general"])
    found_items = []

    for keyword in keywords:
        for scraper in SCRAPERS:

            results = scraper(keyword)

            for item in results:

                if not verify_product(item["buy_link"]):
                    continue

                found_items.append(item)

                # Sort best first
                found_items = sorted(
                    found_items,
                    key=lambda x: x["score"],
                    reverse=True
                )

                found_items = found_items[:MAX_FINAL_ITEMS]

                yield f"data:{json.dumps({'item': item})}\n\n"

                if len(found_items) >= MAX_FINAL_ITEMS:
                    break

            if len(found_items) >= MAX_FINAL_ITEMS:
                break

        if len(found_items) >= MAX_FINAL_ITEMS:
            break

    yield f"data:{json.dumps({'finished': True})}\n\n"


# ==============================
# ROUTES
# ==============================

@app.get("/search_stream")
async def search_stream(category: str = "general"):
    return StreamingResponse(
        stream_results(category),
        media_type="text/event-stream"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
