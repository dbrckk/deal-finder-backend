from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from scrapers.cdiscount import search_cdiscount
from scrapers.rakuten import search_rakuten
from scrapers.fnac import search_fnac
from scrapers.amazon import search_amazon
from scrapers.boulanger import search_boulanger
from scrapers.darty import search_darty
from scrapers.ldlc import search_ldlc
from scrapers.ebay import search_ebay
from scrapers.showroomprive import search_showroomprive
from scrapers.veepree import search_veepree
from utils import verify_availability
import json, time

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORY_QUERIES = {
    "general": ["montre","sac","chaussure","écouteurs","parfum"],
    "tech":["iphone","pc portable","airpods","samsung","tablette"],
    "outfit":["sneakers","sac cuir","veste","robe","lunettes"],
    "jewelry":["bague","collier","bracelet","montre luxe","parfum"],
    "nearfree":["accessoire","destockage","clearance","fin de serie","promo"],
    "hugesaving":["pc portable","tv 4k","iphone","robot cuisine","console"],
    "forher":["sac femme","chaussures femme","lingerie","bijoux femme","robe"]
}

MAX_RESULTS = 5
MAX_KEYWORD_DEPTH = 3

@app.get("/search_stream")
def search_stream(category:str="general"):
    if category not in CATEGORY_QUERIES: category="general"
    verified_results=[]

    def event_generator():
        for depth in range(MAX_KEYWORD_DEPTH):
            for keyword in CATEGORY_QUERIES[category]:
                candidates=[]
                # aggregate all searches
                candidates.extend(search_cdiscount(keyword))
                candidates.extend(search_rakuten(keyword))
                candidates.extend(search_fnac(keyword))
                candidates.extend(search_amazon(keyword))
                candidates.extend(search_boulanger(keyword))
                candidates.extend(search_darty(keyword))
                candidates.extend(search_ldlc(keyword))
                candidates.extend(search_ebay(keyword))
                candidates.extend(search_veepree(keyword))
                candidates.extend(search_showroomprive(keyword))

                candidates = sorted(candidates, key=lambda x:x["score"], reverse=True)
                for item in candidates:
                    if len(verified_results)>=MAX_RESULTS: break
                    if verify_availability(item["buy_link"]):
                        item["available"]=True
                        verified_results.append(item)
                        yield f"data:{json.dumps({'item':item,'progress':len(verified_results),'keyword':keyword})}\n\n"
                    time.sleep(1)
                if len(verified_results)>=MAX_RESULTS: break
                time.sleep(2)
            if len(verified_results)>=MAX_RESULTS: break
        yield f"data:{json.dumps({'finished':True,'total_found':len(verified_results)})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
