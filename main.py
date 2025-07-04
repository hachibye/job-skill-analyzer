from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import List
from collections import Counter
import logging

from job_sources import fetch_all_job_details
from skill_analyzer import analyze_skill_from_description

logger = logging.getLogger(__name__)

app = FastAPI(title="職缺技能分析 API")

# 掛載靜態資源
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=RedirectResponse)
def home():
    return "/static/index.html"

@app.get("/skills/json", response_class=JSONResponse)
def get_skills_json(
    keyword: str = Query(..., description="請輸入搜尋關鍵字（例如：SRE、DevOps）"),
    limit: int = Query(50, ge=1, le=50)
) -> JSONResponse:
    logger.info(f"接收到 keyword: {keyword}")

    all_jobs: List[dict] = []
    keywords = keyword.strip().split()

    try:
        for kw in keywords:
            logger.info(f"查詢關鍵字：{kw}")
            jobs = fetch_all_job_details(kw, limit=limit)
            logger.debug(f"取得 jobs: {jobs}")
            for job in jobs:
                text = f"{job.get('description','')}\n{job.get('requirement','')}"
                logger.debug(f"分析 job: {job}")
                logger.debug(f"分析 text: {text}")
                skills = analyze_skill_from_description(text)
                logger.debug(f"取得 skills: {skills}")
                job["skills"] = skills
            all_jobs.extend(jobs)
    except Exception as e:
        logger.error(f"API 處理過程發生錯誤: {e}", exc_info=True)
        logger.error(f"目前 all_jobs: {all_jobs}")
        logger.error(f"目前 keywords: {keywords}")
        raise HTTPException(status_code=500, detail=f"伺服器處理失敗: {e}")

    if not all_jobs:
        logger.warning("找不到任何職缺")
        return JSONResponse({"error": "找不到任何職缺"}, status_code=404)

    top_skills = analyze_top_skills(all_jobs)
    return JSONResponse({
        "keyword": keyword,
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "jobs": all_jobs
    })

def analyze_top_skills(jobs: List[dict], top_k: int = 10) -> List[tuple]:
    counter = Counter()
    for job in jobs:
        counter.update(job.get("skills", []))
    return counter.most_common(top_k)
