import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_model_comparison(prompt):
    # temperature값을 조절하여 모델 별 온도 값을 조절 가능합니다.
    configs = {
        "gemini-3.1-pro-preview": {"temperature": 1.0, "top_p": 0.95, "max_output_tokens": 200},
        "gemini-3.1-flash-lite-preview": {"temperature": 1.0, "top_p": 0.95, "max_output_tokens": 200},
        "gemini-2.5-flash": {"temperature": 1.0, "top_p": 0.95, "max_output_tokens": 200},
        "gemma-4-31b-it": {"temperature": 1.0, "top_p": 0.9, "top_k": 40, "max_output_tokens": 200}
    }


    for model_name, config in configs.items():

        print(f"\n{'='*20} {model_name} 테스트 시작 {'='*20}")
        
        try:
            # 모델 인스턴스 생성 (각기 다른 설정값 적용)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=config
            )

            start_time = time.time()
            response = model.generate_content(prompt)
            end_time = time.time()

            latency = end_time - start_time
            tokens = response.usage_metadata.total_token_count
            answer = response.text.strip()

            print(f"    모델명: {model_name}")
            print(f"⏱  응답시간: {latency:.2f}초")
            print(f"   사용토큰: {tokens}")
            print(f"   응답결과: {answer}")

            # Pro 모델의 호출 제한(RPM)을 피하기 위해 약간의 대기시간 추가
            if "pro" in model_name:
                time.sleep(2)

        except Exception as e:
            print(f"{model_name} 호출 중 에러 발생: {e}")
        
        print("-" * 70)

if __name__ == "__main__":
    # 질문
    user_prompt = "A는 사과 10개를 가지고 있고, B에게 3개를 줬어. 그 후 C가 A에게 사과를 2배로 만들어줬고, 마지막으로 A가 사과 4개를 먹었어. 현재 A가 가진 사과는 몇 개야? 숫자만 답해줘."
    run_model_comparison(user_prompt)