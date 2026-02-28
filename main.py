from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
from typing import Dict, Any

app = FastAPI()

# Replace with your actual front-end URL
FRONTEND_URL = "https://glitchprice-finder-2oxjrj3s6-dbrckks-projects.vercel.app"

# Enable CORS so front-end can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Replace this with your real scrapers
def get_items(category: str):
    # Example: 10 items, will simulate live search
    sample_items = [
        {
            "title": f"{category} Item {i+1}",
            "price": 100 - i*5,
            "old_price": 200 - i*5,
            "discount": 50,
            "coupon": 10,
            "cashback": 5,
            "money_saved": 105.0 - i*5,
            "score": 100,
            "website": "ExampleShop",
            "buy_link": "https://example.com/item",
            "available": True
        }
        for i in range(10)
    ]
    
    for idx, item in enumerate(sample_items):
        # Simulate search delay (replace with real scraping)
        time.sleep(2)
        yield {"item": item, "progress": idx + 1, "keyword": category}
    
    # Signal search finished
    yield {"finished": True, "total_found": 5}

# SSE endpoint for live streaming
@app.get("/search_stream")
async def search_stream(category: str = "general"):
    def event_generator():
        for event in get_items(category):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}
