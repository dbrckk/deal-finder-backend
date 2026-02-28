import requests
from bs4 import BeautifulSoup
import random

HEADERS = {"User-Agent": "Mozilla/5.0"}
COUPON_SOURCES = ["https://www.igraal.com", "https://www.poulpeo.com", "https://www.ma-reduc.com", "https://www.radins.com"]

def extract_price(text):
    try:
        text = text.replace("€","").replace(",",".")
        text = ''.join(c for c in text if c.isdigit() or c==".")
        return float(text)
    except:
        return None

def verify_availability(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return False
        text = r.text.lower()
        if "indisponible" in text or "rupture" in text or "out of stock" in text:
            return False
        return True
    except:
        return False

def get_coupon_for_item(item):
    retailer = item["website"].lower()
    discount = None
    for source in COUPON_SOURCES:
        try:
            search_url = f"{source}/search?query={retailer}"
            r = requests.get(search_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "lxml")
            tag = soup.select_one(".coupon-discount,.reduction")
            if tag and "%" in tag.text:
                discount = int(''.join(c for c in tag.text if c.isdigit()))
                if discount > 0: break
        except:
            continue
    return discount

def get_cashback_for_item(item):
    # For now, random placeholder
    return random.choice([0,2,5,10])

def check_coupon_and_cashback(item):
    coupon = get_coupon_for_item(item)
    cashback = get_cashback_for_item(item)
    price_after_coupon = item["price"]
    if coupon:
        price_after_coupon *= (1 - coupon/100)
    total_saved = (item["old_price"] - price_after_coupon) + (cashback or 0)
    item["coupon"] = coupon
    item["cashback"] = cashback
    item["money_saved"] = round(total_saved,2)
    item["score"] = (item["discount"]*2) + (item["money_saved"]/10)
    return item
