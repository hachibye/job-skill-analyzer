import random
import requests
import time
from urllib.parse import quote


def get_104_job_list(keyword: str, page: int = 1, max_jobs: int = 20) -> list:
    print(f"\n🔎 [104 API] 查詢關鍵字：{keyword}（第 {page} 頁）")

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
    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        print("❌ 查詢失敗")
        return []

    try:
        data = res.json()
    except Exception as e:
        print(f"❌ JSON 解析失敗：{e}")
        return []

    jobs = data.get("data", {}).get("list", [])
    if not jobs:
        print("⚠️ 查無職缺")
        return []

    job_summaries = []
    for job in jobs[:max_jobs]:
        raw_link = job.get("link", {}).get("job", "")
        # 修正：去掉完整 URL 路徑與查詢參數，保留純 job ID
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

    print(f"🔢 找到 {len(job_summaries)} 筆職缺 ID")
    return job_summaries


def get_104_job_detail(job_id: str, session: requests.Session) -> dict:
    url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://www.104.com.tw/job/{job_id}",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

    res = session.get(url, headers=headers)  # ✅ 用 session 發送

    if res.status_code != 200:
        print(f"❌ 無法取得職缺內容：{job_id}")
        return {}

    try:
        data = res.json().get("data", {})
    except Exception as e:
        print(f"❌ 職缺 {job_id} JSON 解析錯誤：{e}")
        return {}

    return {
        "job_id": job_id,
        "title": data.get("header", {}).get("jobName"),
        "company": data.get("header", {}).get("custName"),
        "description": data.get("jobDetail", {}).get("jobDescription"),
        "requirement": data.get("condition", {}).get("other"),
        "skills": [s["description"] for s in data.get("skills", [])],
        "url": f"https://www.104.com.tw/job/{job_id}"
    }


    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print(f"❌ 無法取得職缺內容：{job_id}")
        return {}

    try:
        data = res.json().get("data", {})
    except Exception as e:
        print(f"❌ 職缺 {job_id} JSON 解析錯誤：{e}")
        return {}

    return {
        "job_id": job_id,
        "title": data.get("header", {}).get("jobName"),
        "company": data.get("header", {}).get("custName"),
        "description": data.get("jobDetail", {}).get("jobDescription"),
        "requirement": data.get("condition", {}).get("other"),
        "skills": [s["description"] for s in data.get("skills", [])],
        "url": f"https://www.104.com.tw/job/{job_id}"
    }


def fetch_all_job_details(keyword: str, limit: int = 5) -> list:
    summaries = get_104_job_list(keyword=keyword, max_jobs=limit)

    session = requests.Session()  # ✅ 新增 session

    all_details = []
    for i, job in enumerate(summaries):
        job_id = job["id"]
        print(f"📄 解析職缺 {i + 1}/{len(summaries)}：{job_id}")
        detail = get_104_job_detail(job_id, session=session)  # ✅ 傳入 session
        if detail:
            all_details.append(detail)
        time.sleep(random.uniform(2, 5))  # ⏳ 防止請求過快

    print(f"\n📦 共收集到 {len(all_details)} 筆獨立職缺描述")
    return all_details

