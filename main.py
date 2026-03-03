from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import re
import uuid
import time
from typing import Dict, List

app = FastAPI()

FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_ITEMS = 5

# In-memory job storage
jobs: Dict[str, Dict] = {}

# ======================
# UTILITIES
# ======================

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
        if "indisponible" in r.text.lower():
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
        "score": discount + money_saved
    }

# ======================
# SCRAPERS
# ======================

def scrape_amazon(keyword):
    items = []
    try:
        url = f"https://www.amazon.fr/s?k={keyword}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for card in soup.select(".s-result-item")[:3]:
            title_tag = card.select_one("h2 a span")
            price_whole = card.select_one(".a-price-whole")
            price_frac = card.select_one(".a-price-fraction")

            if not title_tag or not price_whole or not price_frac:
                continue

            title = title_tag.text.strip()
            price = clean_price(price_whole.text + "." + price_frac.text)
            link = "https://www.amazon.fr" + card.select_one("h2 a")["href"]

            items.append(build_item(title, price, price, link, "Amazon FR"))

    except:
        pass

    return items


def scrape_ebay(keyword):
    items = []
    try:
        url = f"https://www.ebay.fr/sch/i.html?_nkw={keyword}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "lxml")

        for card in soup.select(".s-item")[:3]:
            title_tag = card.select_one(".s-item__title")
            price_tag = card.select_one(".s-item__price")
            link_tag = card.select_one(".s-item__link")

            if not title_tag or not price_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            price = clean_price(price_tag.text)
            link = link_tag["href"]

            items.append(build_item(title, price, price, link, "eBay FR"))

    except:
        pass

    return items

SCRAPERS = [scrape_amazon, scrape_ebay]

KEYWORDS = ["montre", "sac", "bijou", "chaussures", "parfum"]

# ======================
# BACKGROUND SCAN
# ======================

def run_scan(job_id: str):
    found_items: List[Dict] = []

    for keyword in KEYWORDS:
        for scraper in SCRAPERS:

            results = scraper(keyword)

            for item in results:

                if not verify_product(item["buy_link"]):
                    continue

                found_items.append(item)

                found_items = sorted(
                    found_items,
                    key=lambda x: x["score"],
                    reverse=True
                )[:MAX_ITEMS]

                jobs[job_id]["items"] = found_items

                time.sleep(2)  # slow scan intentionally

    jobs[job_id]["finished"] = True

# ======================
# ROUTES
# ======================

@app.post("/start_scan")
def start_scan(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "items": [],
        "finished": False
    }

    background_tasks.add_task(run_scan, job_id)

    return {"job_id": job_id}


@app.get("/scan_status/{job_id}")
def scan_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}

    return jobs[job_id]


@app.get("/health")
def health():
    return {"status": "ok"}
