import random
import requests
import time
import logging
from urllib.parse import quote
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def get_104_job_list(keyword: str, page: int = 1, max_jobs: int = 50) -> List[Dict]:
    logger.info(f"[104 API] 查詢關鍵字：{keyword}（第 {page} 頁）")

    encoded_keyword = quote(keyword)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.104.com.tw/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

    params = {
        "ro": "0",
        "kwop": "7",
        "keyword": keyword,
        "order": "15",
        "asc": "0",
        "page": page,
        "mode": "s",
        "jobsource": "2018indexpoc"
    }

    url = "https://www.104.com.tw/jobs/search/list"
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
    except Exception as e:
        logger.error(f"查詢失敗: {e}")
        return []

    try:
        data = res.json()
    except Exception as e:
        logger.error(f"JSON 解析失敗：{e}")
        return []

    jobs = data.get("data", {}).get("list", [])
    if not jobs:
        logger.warning("查無職缺")
        return []

    job_summaries = []
    for job in jobs[:max_jobs]:
        raw_link = job.get("link", {}).get("job", "")
        job_id = raw_link.strip().split("/")[-1].split("?")[0]
        job_title = job.get("jobName")
        company = job.get("company", {}).get("name")
        if job_id:
            job_summaries.append({
                "id": job_id,
                "title": job_title,
                "company": company,
                "url": f"https://www.104.com.tw/job/{job_id}"
            })

    logger.info(f"找到 {len(job_summaries)} 筆職缺 ID")
    return job_summaries


def get_104_job_detail(job_id: str, session: requests.Session) -> Optional[Dict]:
    url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.104.com.tw/job/{job_id}",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

    try:
        res = session.get(url, headers=headers)
        res.raise_for_status()
    except Exception as e:
        logger.error(f"無法取得職缺內容：{job_id}，錯誤：{e}")
        return None

    try:
        data = res.json().get("data", {})
    except Exception as e:
        logger.error(f"職缺 {job_id} JSON 解析錯誤：{e}")
        return None

    return {
        "job_id": job_id,
        "title": data.get("header", {}).get("jobName"),
        "company": data.get("header", {}).get("custName"),
        "description": data.get("jobDetail", {}).get("jobDescription"),
        "requirement": data.get("condition", {}).get("other"),
        "skills": [s["description"] for s in data.get("skills", [])],
        "url": f"https://www.104.com.tw/job/{job_id}"
    }


def fetch_all_job_details(keyword: str, limit: int = 5, sleep_range: tuple = (2, 5)) -> List[Dict]:
    summaries = get_104_job_list(keyword=keyword, max_jobs=limit)

    session = requests.Session()
    all_details = []
    for i, job in enumerate(summaries):
        job_id = job["id"]
        logger.info(f"解析職缺 {i + 1}/{len(summaries)}：{job_id}")
        detail = get_104_job_detail(job_id, session=session)
        if detail:
            all_details.append(detail)
        time.sleep(random.uniform(*sleep_range))  # 可調整 sleep 區間

    logger.info(f"共收集到 {len(all_details)} 筆獨立職缺描述")
    return all_details

