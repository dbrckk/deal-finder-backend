import uuid
import threading
import time
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# In-memory job storage
# -----------------------------
jobs: Dict[str, dict] = {}

# -----------------------------
# Simple website scanner
# -----------------------------
def scan_websites(job_id: str, websites: List[str]):

    jobs[job_id]["status"] = "running"
    jobs[job_id]["results"] = []
    jobs[job_id]["progress"] = 0

    total = len(websites)

    for index, url in enumerate(websites):

        try:
            response = requests.get(url, timeout=10)

            soup = BeautifulSoup(response.text, "html.parser")

            title = soup.title.string.strip() if soup.title else "No title"

            jobs[job_id]["results"].append({
                "url": url,
                "status": response.status_code,
                "title": title
            })

        except Exception as e:
            jobs[job_id]["results"].append({
                "url": url,
                "status": "error",
                "title": str(e)
            })

        # update progress
        jobs[job_id]["progress"] = int(((index + 1) / total) * 100)

        # slow down (important for free tier stability)
        time.sleep(2)

    jobs[job_id]["status"] = "finished"


# -----------------------------
# Start scan endpoint
# -----------------------------
@app.post("/start-scan")
def start_scan(data: dict):

    websites = data.get("websites", [])

    if not websites:
        return {"error": "No websites provided"}

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "results": []
    }

    thread = threading.Thread(
        target=scan_websites,
        args=(job_id, websites)
    )
    thread.start()

    return {"job_id": job_id}


# -----------------------------
# Status endpoint
# -----------------------------
@app.get("/status/{job_id}")
def get_status(job_id: str):

    job = jobs.get(job_id)

    if not job:
        return {"error": "Job not found"}

    return job


# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def root():
    return {"message": "Backend running"}
