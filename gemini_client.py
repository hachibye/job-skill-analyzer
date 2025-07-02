import os
from dotenv import load_dotenv
import google.generativeai as genai

# 載入 .env 變數
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 初始化 Gemini 模型
def init_gemini_model():
    print("🚀 初始化 Gemini 1.5 Flash 模型…")
    if not API_KEY:
        raise RuntimeError("❌ 找不到 GEMINI_API_KEY，請確認 .env 檔案設定正確")

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    return model

# 呼叫 Gemini API
def call_gemini_for_skills(model, prompt: str) -> str:
    print("🤖 呼叫 Gemini 預測…")
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        print(f"📨 Gemini 回傳內容（前200字）：{result[:200]}")
        return result
    except Exception as e:
        print(f"❌ Gemini API 錯誤：{e}")
        return ""
