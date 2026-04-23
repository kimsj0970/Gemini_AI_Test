import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_model_comparison(prompt, model_name):
    # temperature값을 조절하여 모델 별 온도 값을 조절 가능합니다.

    # [Flash 전용] thinking_budget: 모델이 답변 생성 전 추론에 사용할 최대 토큰 수를 지정합니다.
    #   0          → 추론 비활성화 (가장 빠름, 단순 질문에 적합)
    #   1 ~ 1024   → 낮은 추론 수준 (low) : 간단한 논리 추론, 기본 수학 문제
    #   1025 ~ 8192 → 중간 추론 수준 (medium) : 복잡한 추론, 다단계 문제
    #   8193 ~ 24576 → 높은 추론 수준 (high) : 고난도 수학, 심층 분석
    #   -1         → 동적 추론 (모델이 문제 복잡도에 따라 자동으로 추론량을 결정)
    configs = {
        # [케이스 1] Flash + CoT 적용
        #    - thinking_budget=1024 : 추론 토큰을 1024개까지 허용하여 내부적으로 단계별 추론 수행
        #    - 프롬프트에서 단계별 사고를 명시적으로 유도 (CoT 기법)
        "gemini-3-flash-preview:cot": types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
        ),

        # [케이스 2] Flash + CoT 미적용
        #    - thinking_budget=0 : 추론 단계 비활성화 (순수 생성 모드)
        #    - 동일한 Flash 모델이지만 단계별 사고 유도 없이 바로 답변
        #    - 케이스 1과 비교 시 → CoT 기법 자체의 효과를 순수하게 측정 가능
        "gemini-3-flash-preview:no-cot": types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
        ),

        # [케이스 3] Pro + CoT 미적용
        #    - thinking_config 없음 : Pro 모델은 기본적으로 더 강력한 추론 능력 보유
        #    - 케이스 2와 비교 시 → 같은 CoT 없는 조건에서 Flash vs Pro 모델 성능 차이 측정 가능
        #    - 케이스 1과 비교 시 → CoT 적용 Flash vs 고성능 Pro 중 어느 쪽이 효율적인지 비교 가능
        "gemini-3.1-pro-preview": types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
            max_output_tokens=4096,
        ),
    }

    # configs 키는 "모델명:variant" 형태를 사용하므로, 실제 API 호출 시엔 ":" 이후를 제거
    config_key = model_name
    api_model_name = model_name.split(":")[0]
    config = configs.get(config_key)

    print(f"\n{'='*20} {model_name} 테스트 시작 {'='*20}")

    
    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=api_model_name,  # ":cot" / ":no-cot" 같은 variant 접미사 제거 후 호출
            contents=prompt,
            config=config,
        )
        end_time = time.time()

        latency = end_time - start_time
        tokens = response.usage_metadata.total_token_count
        answer = response.text.strip()

        print(f"    모델명: {api_model_name}")
        print(f"⏱  응답시간: {latency:.2f}초")
        print(f"   사용토큰: {tokens}")
        print(f"   응답결과: {answer}")

        # Pro 모델의 호출 제한(RPM)을 피하기 위해 약간의 대기시간 추가
        if "pro" in api_model_name:
            time.sleep(2)

    except Exception as e:
        print(f"{model_name} 호출 중 에러 발생: {e}")
    
    print("-" * 70)

# main 파일이 실행되는 경우에만 이 명령을 실행 (다른 파일에서도 사용 되도록 재사용성 증가)
if __name__ == "__main__":
    
    # ──────────────────────────────────────────────────────────────
    # 비교 목적 : 동일한 베이즈 정리 문제를 세 가지 방식으로 호출하여
    #            CoT 기법의 효과와 모델 간 성능 차이를 나란히 비교
    #
    #  [케이스 1] Flash  + CoT 적용   → CoT 기법이 Flash 모델에 주는 효과 확인
    #  [케이스 2] Flash  + CoT 미적용 → 케이스1과 동일 모델, CoT 유무만 다름
    #  [케이스 3] Pro    + CoT 미적용 → 케이스2와 동일 조건, 모델만 고성능 Pro
    # ──────────────────────────────────────────────────────────────

    # 공통 문제 (세 케이스 모두 동일하게 사용)
    base_question = """맥스웰 방정식 4개로부터 진공에서의 전자기파 전파 속도 c = 1/√(ε₀μ₀)를 유도해줘. 패러데이 법칙 ∇×E = -∂B/∂t와 앙페르-맥스웰 법칙 ∇×B = μ₀ε₀∂E/∂t, 벡터 항등식 ∇×(∇×E) = ∇(∇·E) - ∇²E를 사용하고, ε₀ = 8.854×10⁻¹² F/m, μ₀ = 4π×10⁻⁷ H/m을 대입해서 최종 광속값까지 계산 과정을 보여줘."""

    # ─── 케이스별 프롬프트 정의 ───────────────────────────────────
    prompts = {
        # [케이스 1] CoT 프롬프트 : 단계별 사고 과정을 명시적으로 유도
        "[케이스 1] Flash + CoT 적용": """맥스웰 방정식 4개로부터 전자기파의 전파 속도 c = 1/√(ε₀μ₀)를 유도하고 실제 광속값과 비교해줘. 단, 답을 바로 내리지 말고 아래 방식으로 사고해줘. 먼저 맥스웰 방정식 4개(가우스 법칙, 자기 가우스 법칙, 패러데이 법칙, 앙페르-맥스웰 법칙)가 각각 물리적으로 무엇을 의미하는지 네 언어로 설명해봐. 그 다음 진공에서 자유전하와 전류가 없는 경우(ρ=0, J=0) 맥스웰 방정식이 어떻게 단순화되는지 보여줘. 거기서 이어서 패러데이 법칙 ∇×E = -∂B/∂t의 양변에 curl 연산자를 적용하고 벡터 항등식 ∇×(∇×E) = ∇(∇·E) - ∇²E를 이용해서 전기장 E에 대한 파동방정식을 유도해봐. 그 다음 같은 방식으로 자기장 B에 대한 파동방정식도 유도하고 두 파동방정식에서 전파 속도 c = 1/√(ε₀μ₀)가 어떻게 나오는지 보여줘. 마지막으로 ε₀ = 8.854×10⁻¹²  F/m, μ₀ = 4π×10⁻⁷ H/m을 대입해서 c를 직접 계산하고 실제 광속 2.998×10⁸ m/s와 비교해서 이 결과가 갖는 물리적 의미를 결론으로 내려줘. 중간 수식 전개와 추론을 생략하지 말고 전부 보여줘.""",

        # [케이스 2] CoT 없는 동일 Flash 모델 : 추론 유도 없이 직접 답변 요청
        "[케이스 2] Flash + CoT 미적용": base_question,

        # [케이스 3] CoT 없는 Pro 모델 : 케이스 2와 동일 프롬프트, 더 강력한 모델 사용
        "[케이스 3] Pro + CoT 미적용": base_question,
    }

    # ─── 케이스 순서대로 실행 ──────────────────────────────────────
    for case_name, prompt_text in prompts.items():
        print(f"\n{'#'*60}")
        print(f"  {case_name}")
        print(f"{'#'*60}")

        if case_name == "[케이스 1] Flash + CoT 적용":
            # Flash 모델 + thinking_budget=1024 (내부 추론 활성화) + CoT 유도 프롬프트
            run_model_comparison(prompt_text, "gemini-3-flash-preview:cot")

        elif case_name == "[케이스 2] Flash + CoT 미적용":
            # Flash 모델 + thinking_budget=0 (내부 추론 비활성화) + 일반 프롬프트
            run_model_comparison(prompt_text, "gemini-3-flash-preview:no-cot")

        else:  # [케이스 3] Pro + CoT 미적용
            # Pro 모델 + thinking_config 없음 + 일반 프롬프트
            run_model_comparison(prompt_text, "gemini-3.1-pro-preview")

