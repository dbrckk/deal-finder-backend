from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import re

app = FastAPI()

MAX_PRICE = 1000
MAX_RESULTS = 6

class CategoryRequest(BaseModel):
    category: str


# ---------------- KEYWORDS ---------------- #

def generate_keywords(category):
    if category.lower() == "perfume":
        return [
            "parfum soldes",
            "parfum promotion",
            "eau de parfum reduction",
            "fragrance clearance",
            "luxury perfume discount",
            "parfum 50%",
            "parfum -40%"
        ]
    if category.lower() == "jewelry":
        return [
            "bijoux soldes",
            "collier or promotion",
            "bracelet argent reduction",
            "bague diamant soldes",
            "luxury jewelry discount",
            "montre luxe -40%"
        ]
    return [category]


# ---------------- HELPERS ---------------- #

def extract_price(text):
    try:
        text = text.replace(",", ".")
        match = re.search(r"\d+\.?\d*", text)
        if match:
            return float(match.group())
    except:
        pass
    return None


def evaluate_deal(price, old_price):
    if not price or not old_price:
        return None
    
    if price > MAX_PRICE:
        return None

    saving = old_price - price
    discount = (saving / old_price) * 100

    if discount >= 40 or saving >= 300:
        return {
            "price": price,
            "original_price": old_price,
            "saving": round(saving, 2),
            "discount_percent": round(discount, 2)
        }

    return None


# ---------------- SCRAPERS ---------------- #

def search_notino(keyword):
    url = f"https://www.notino.fr/search.asp?exps={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")

    results = []

    products = soup.select(".product-item")

    for p in products[:10]:
        try:
            title = p.select_one(".product-item-title").text.strip()
            prices = p.select(".price")

            if len(prices) >= 2:
                old_price = extract_price(prices[0].text)
                price = extract_price(prices[1].text)
            else:
                continue

            deal = evaluate_deal(price, old_price)
            if deal:
                results.append({
                    "title": title,
                    "link": "https://www.notino.fr",
                    **deal
                })

        except:
            continue

    return results


def search_zalando(keyword):
    url = f"https://www.zalando.fr/catalog/?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")

    results = []
    products = soup.select("article")

    for p in products[:10]:
        try:
            title = p.text[:80]
            prices = re.findall(r"\d+,\d+", p.text)

            if len(prices) >= 2:
                old_price = float(prices[0].replace(",", "."))
                price = float(prices[1].replace(",", "."))
            else:
                continue

            deal = evaluate_deal(price, old_price)
            if deal:
                results.append({
                    "title": title,
                    "link": "https://www.zalando.fr",
                    **deal
                })

        except:
            continue

    return results


# ---------------- MAIN ROUTE ---------------- #

@app.get("/")
def root():
    return {"status": "Deal Finder API running"}


@app.post("/search")
def search_deals(data: CategoryRequest):
    keywords = generate_keywords(data.category)

    all_results = []

    def run_search(keyword):
        return search_notino(keyword) + search_zalando(keyword)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_search, kw) for kw in keywords]
