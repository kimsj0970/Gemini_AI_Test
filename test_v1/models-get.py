import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. .env 파일 로드
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("에러: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")

    
else:
    genai.configure(api_key=api_key)

    print("--- 현재 키로 호출 가능한 모델 목록 ---")
    print("-" * 60)
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 'models/' 접두사를 제외한 순수 이름만 보기 좋게 출력
                clean_name = m.name.replace('models/', '')
                print(f"모델명: {clean_name}")
                print(f"설명: {m.description}")
                print("-" * 60)
    except Exception as e:
        print(f"목록을 가져오는 중 오류 발생: {e}")