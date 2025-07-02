from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import List
from collections import Counter
import json

from job_sources import fetch_all_job_details
from skill_analyzer import analyze_skill_from_description

app = FastAPI(title="職缺技能分析 API")

# 掛載靜態資源
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=RedirectResponse)
def home():
    return "/static/index.html"

@app.get("/skills/json", response_class=JSONResponse)
def get_skills_json(
    keyword: str = Query(...),
    limit: int = Query(10, ge=1, le=50)
):
    all_jobs = []
    keywords = keyword.strip().split()

    for kw in keywords:
        jobs = fetch_all_job_details(kw, limit=limit)
        for job in jobs:
            text = f"{job.get('description','')}\n{job.get('requirement','')}"
            job["skills"] = analyze_skill_from_description(text)
        all_jobs.extend(jobs)

    if not all_jobs:
        return {"error": "找不到任何職缺"}

    top_skills = analyze_top_skills(all_jobs)
    return {
        "keyword": keyword,
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "jobs": all_jobs
    }


def analyze_top_skills(jobs: List[dict], top_k: int = 10):
    counter = Counter()
    for job in jobs:
        counter.update(job.get("skills", []))
    return counter.most_common(top_k)
