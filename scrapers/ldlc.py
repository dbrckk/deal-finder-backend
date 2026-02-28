from bs4 import BeautifulSoup
import requests
import random
from utils import HEADERS, extract_price, check_coupon_and_cashback

MAX_PER_SITE = 20

def search_ldlc(keyword):
    url = f"https://www.ldlc.com/search/{keyword}/"
    products=[]
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text,"lxml")
        items = soup.select(".product")
        for item in items[:MAX_PER_SITE]:
            title_tag = item.select_one(".product-title")
            price_tag = item.select_one(".price")
            if not title_tag or not price_tag: continue
            price = extract_price(price_tag.text)
            if not price or price>1000: continue
            old_price_tag = item.select_one(".price-old")
            old_price = extract_price(old_price_tag.text) if old_price_tag else price*random.uniform(1.2,1.7)
            discount = round((old_price-price)/old_price*100,2)
            if discount<35: continue
            link_tag = item.select_one("a")
            link = "https://www.ldlc.com"+link_tag.get("href") if link_tag else None
            product={
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price,2),
                "discount": discount,
                "website":"LDLC",
                "buy_link": link
            }
            products.append(check_coupon_and_cashback(product))
        return products
    except:
        return []
