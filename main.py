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
            "parfum soldes", "parfum promotion", "eau de parfum reduction",
            "fragrance clearance", "luxury perfume discount",
            "parfum 50%", "parfum -40%"
        ]
    if category.lower() == "jewelry":
        return [
            "bijoux soldes", "collier or promotion", "bracelet argent reduction",
            "bague diamant soldes", "luxury jewelry discount", "montre luxe -40%"
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
    return {
        "price": price,
        "original_price": old_price,
        "saving": round(saving, 2),
        "discount_percent": round(discount, 2)
    }

def is_available(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(link, headers=headers, timeout=10)
        if "Out of stock" in r.text or "Indisponible" in r.text:
            return False
        return True
    except:
        return False

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
            title_tag = p.select_one(".product-item-title")
            prices = p.select(".price")
            if title_tag and len(prices) >= 2:
                title = title_tag.text.strip()
                old_price = extract_price(prices[0].text)
                price = extract_price(prices[1].text)
                link = "https://www.notino.fr"
                deal = evaluate_deal(price, old_price)
                if deal and is_available(link):
                    results.append({"title": title, "link": link, **deal})
        except:
            continue
    return results

def search_sephora(keyword):
    url = f"https://www.sephora.fr/search?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")
    results = []
    products = soup.select("div.ProductTile")
    for p in products[:10]:
        try:
            title_tag = p.select_one("a.ProductTile-link")
            price_tag = p.select_one("span.ProductTile-price")
            if title_tag and price_tag:
                title = title_tag.text.strip()
                prices = re.findall(r"\d+,\d+", price_tag.text)
                if len(prices) >= 2:
                    old_price = float(prices[0].replace(",", "."))
                    price = float(prices[1].replace(",", "."))
                    link = "https://www.sephora.fr"
                    deal = evaluate_deal(price, old_price)
                    if deal and is_available(link):
                        results.append({"title": title, "link": link, **deal})
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
                link = "https://www.zalando.fr"
                deal = evaluate_deal(price, old_price)
                if deal and is_available(link):
                    results.append({"title": title, "link": link, **deal})
        except:
            continue
    return results

def search_marionnaud(keyword):
    url = f"https://www.marionnaud.fr/search?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")
    results = []
    products = soup.select("div.product-tile")
    for p in products[:10]:
        try:
            title_tag = p.select_one("a.product-name")
            price_tag = p.select_one("span.price")
            old_price_tag = p.select_one("span.price-old")
            if title_tag and price_tag and old_price_tag:
                title = title_tag.text.strip()
                price = extract_price(price_tag.text)
                old_price = extract_price(old_price_tag.text)
                link = "https://www.marionnaud.fr"
                deal = evaluate_deal(price, old_price)
                if deal and is_available(link):
                    results.append({"title": title, "link": link, **deal})
        except:
            continue
    return results

def search_nocibe(keyword):
    url = f"https://www.nocibe.fr/search?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "lxml")
    results = []
    products = soup.select("div.product-item")
    for p in products[:10]:
        try:
            title_tag = p.select_one("a.product-title")
            price_tag = p.select_one("span.price")
            old_price_tag = p.select_one("span.price-old")
            if title_tag and price_tag and old_price_tag:
                title = title_tag.text.strip()
                price = extract_price(price_tag.text)
                old_price = extract_price(old_price_tag.text)
                link = "https://www.nocibe.fr"
                deal = evaluate_deal(price, old_price)
                if deal and is_available(link):
                    results.append({"title": title, "link": link, **deal})
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
        return (
            search_notino(keyword) + 
            search_sephora(keyword) + 
            search_zalando(keyword) +
            search_marionnaud(keyword) +
            search_nocibe(keyword)
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_search, kw) for kw in keywords]
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())

    # sort by saving descending
    all_results = sorted(all_results, key=lambda x: x["saving"], reverse=True)

    return {"category": data.category, "results": all_results[:MAX_RESULTS]}
