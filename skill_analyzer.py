import re
import json
from typing import List, Dict, Optional
from collections import Counter
from gemini_client import init_gemini_model, call_gemini_for_skills
from tabulate import tabulate
import logging

logger = logging.getLogger(__name__)

_model = None

def get_gemini_model():
    global _model
    if _model is None:
        logger.info("初始化 Gemini 模型…")
        _model = init_gemini_model()
    return _model

def clean_job_text(description: str, requirement: str) -> str:
    logger.debug("清洗職缺描述與需求內容…")
    text = f"{description}\n{requirement}"
    cleaned_text = re.sub(r'<[^>]+>', '', text)
    cleaned_text = cleaned_text.strip()
    logger.debug(f"清洗後內容（前100字）：{cleaned_text[:100]}")
    return cleaned_text

def analyze_skill_from_description(text: str) -> List[str]:
    logger.info("準備 Gemini Prompt…")
    prompt = f"""
請根據以下職缺描述，列出出現頻率最高的前 10 個核心技能，回傳格式為 JSON 陣列：
{text}

格式範例：
[
  "Python",
  "AWS",
  "Docker"
]
"""
    model = get_gemini_model()
    result_text = call_gemini_for_skills(model, prompt)
    skills = extract_skills_from_response(result_text)
    logger.info(f"擷取技能：{skills}")
    return skills

def extract_skills_from_response(response_text: str) -> List[str]:
    logger.debug("解析 Gemini 回傳內容…")
    response_text = response_text.strip().strip("`")
    response_text = re.sub(r"^json", "", response_text).strip()

    try:
        skills = json.loads(response_text)
        if isinstance(skills, list):
            skills = [s.strip() for s in skills if isinstance(s, str)]
    except Exception as e:
        logger.warning(f"JSON 解析失敗，嘗試正則擷取：{e}")
        skills = re.split(r"[\n,]", response_text)
        skills = [s.strip() for s in skills if s.strip()]

    cleaned_skills = []
    for s in skills:
        s = re.sub(r"\(.*?\)", "", s)
        s = re.sub(r"[^a-zA-Z0-9+\-/ .#\u4e00-\u9fff]", "", s).strip()
        if 1 < len(s) <= 40:
            cleaned_skills.append(s)

    unique_skills = sorted(set(cleaned_skills), key=cleaned_skills.index)
    logger.debug(f"擷取技能（共 {len(unique_skills)} 項）：{unique_skills[:10]} ...")
    return unique_skills

def summarize_jobs_with_skills(jobs: List[Dict]) -> None:
    result = []

    for job in jobs:
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        desc = job.get("description", "")
        req = job.get("requirement", "")

        cleaned = clean_job_text(desc, req)
        skills = analyze_skill_from_description(cleaned)

        result.append({
            "title": title,
            "company": company,
            "top_skills": skills[:10]
        })

    logger.info("\n技能摘要總表：")
    print(tabulate(
        [(job["title"], job["company"], ", ".join(job["top_skills"])) for job in result],
        headers=["職缺標題", "公司名稱", "Gemini 技能摘要"],
        tablefmt="github"
    ))
