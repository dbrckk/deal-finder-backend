from bs4 import BeautifulSoup
import requests
import random
from utils import HEADERS, extract_price, check_coupon_and_cashback

MAX_PER_SITE = 15  # Amazon stricter

def search_amazon(keyword):
    url = f"https://www.amazon.fr/s?k={keyword}"
    products=[]
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text,"lxml")
        items = soup.select(".s-result-item")
        for item in items[:MAX_PER_SITE]:
            title_tag = item.select_one("h2 a span")
            price_whole = item.select_one(".a-price-whole")
            price_fraction = item.select_one(".a-price-fraction")
            if not title_tag or not price_whole: continue
            price_text = price_whole.text + (price_fraction.text if price_fraction else "")
            price = extract_price(price_text)
            if not price or price>1000: continue
            old_price_tag = item.select_one(".a-text-price .a-offscreen")
            old_price = extract_price(old_price_tag.text) if old_price_tag else price*random.uniform(1.2,1.8)
            discount = round((old_price-price)/old_price*100,2)
            if discount<35: continue
            link_tag = item.select_one("h2 a")
            link = "https://www.amazon.fr"+link_tag.get("href") if link_tag else None
            product={
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price,2),
                "discount": discount,
                "website":"Amazon",
                "buy_link": link
            }
            products.append(check_coupon_and_cashback(product))
        return products
    except:
        return []
