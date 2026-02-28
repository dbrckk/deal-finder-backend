from bs4 import BeautifulSoup
import requests
import random
from utils import HEADERS, extract_price, check_coupon_and_cashback

MAX_PER_SITE = 20

def search_cdiscount(keyword):
    url = f"https://www.cdiscount.com/search/10/{keyword}.html"
    products=[]
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text,"lxml")
        items = soup.select(".lpMain .prdtBloc")
        for item in items[:MAX_PER_SITE]:
            title_tag = item.select_one(".prdtTitle")
            price_tag = item.select_one(".price")
            if not title_tag or not price_tag: continue
            price = extract_price(price_tag.text)
            if not price or price>1000: continue
            old_price_tag = item.select_one(".strike")
            old_price = extract_price(old_price_tag.text) if old_price_tag else price*random.uniform(1.2,1.8)
            discount = round((old_price-price)/old_price*100,2)
            if discount<35: continue
            link = title_tag.get("href")
            if link and not link.startswith("http"): link="https://www.cdiscount.com"+link
            product={
                "title": title_tag.text.strip(),
                "price": price,
                "old_price": round(old_price,2),
                "discount": discount,
                "website":"Cdiscount",
                "buy_link":link
            }
            products.append(check_coupon_and_cashback(product))
        return products
    except:
        return []
