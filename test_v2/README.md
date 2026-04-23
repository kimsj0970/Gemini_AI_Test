# Gemini AI 모델 비교 테스트 (Gemini AI Test)

이 프로젝트는 Google의 Generative AI 모델들을 활용하여 **CoT(Chain of Thought) 기법의 효과**와 **모델 간 성능 차이**를 나란히 비교하기 위한 데모 스크립트입니다.

## 비교 케이스 구성

| 케이스 | 모델 | CoT 프롬프트 | thinking_budget | 비교 목적 |
|:---:|---|:---:|:---:|---|
| **케이스 1** | `gemini-3-flash-preview` | 적용 | 1024 | CoT 기법이 Flash 모델에 주는 효과 확인 |
| **케이스 2** | `gemini-3-flash-preview` | 미적용 | 0 | 케이스 1과 동일 모델 — **CoT 유무만** 다름 |
| **케이스 3** | `gemini-3.1-pro-preview` | 미적용 | N/A | 케이스 2와 동일 조건 — **모델만** 고성능 Pro |

> **이렇게 읽으세요**
> - 케이스 1 vs 2 → CoT 프롬프트 자체의 효과 (같은 Flash, 프롬프트만 다름)
> - 케이스 2 vs 3 → Flash vs Pro 모델 성능 차이 (같은 일반 프롬프트)
> - 케이스 1 vs 3 → "CoT + Flash" vs "Pro" 중 어느 쪽이 더 효율적인지

## 주요 기능

- **3-케이스 순차 비교**: 위 표의 순서대로 자동 호출하여 결과를 출력합니다.
- **성능 지표 측정**: 각 케이스의 **응답 시간(Latency)**과 **사용 토큰 수(Tokens)**를 계산하여 출력합니다.
- **명확한 모듈화**: `run_model_comparison` 함수가 분리되어 있어, 향후 코드의 유지보수 및 재사용이 쉽게 구성되어 있습니다.

## 사전 준비 사항 (Prerequisites)

이 프로젝트를 실행하기 위해 다음 항목들이 필요합니다:

1. **Python 3.x 환경** (프로젝트 내 가상 환경 사용 권장)
2. **필수 패키지**: `google-generativeai`, `python-dotenv`
3. **Google Gemini API Key** (Google AI Studio에서 발급)

## 설치 및 실행 방법

1. **의존성 설치**
   터미널에서 아래 명령어를 실행하여 필수 패키지를 설치합니다:
   ```bash
   pip install google-generativeai python-dotenv
   ```

2. **환경 변수 설정 (.env)**
   프로젝트 폴더(스크립트와 같은 경로)에 `.env` 파일을 만들고 발급받은 API 키를 입력합니다.
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **스크립트 실행**
   ```bash
   uv run main.py
   ```

## 코드 설정 및 수정 (main.py)

`main.py` 파일 내의 `configs` 딕셔너리를 수정하여 모델 파라미터를 제어할 수 있습니다.
키는 `"모델명:variant"` 형태로 선언되며, 실제 API 호출 시엔 `:` 이후가 자동으로 제거됩니다.

```python
configs = {
    # [케이스 1] Flash + CoT 적용
    #   thinking_budget=1024 : 내부적으로 단계별 추론 수행
    "gemini-3-flash-preview:cot": types.GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=4096,
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
    ),

    # [케이스 2] Flash + CoT 미적용
    #   thinking_budget=1024 : 추론은 허용하되 CoT 유도 프롬프트 없이 바로 답변
    "gemini-3-flash-preview:no-cot": types.GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=4096,
        thinking_config=types.ThinkingConfig(thinking_budget=1024),
    ),

    # [케이스 3] Pro + CoT 미적용
    #   thinking_config 없음 : Pro 모델 기본 추론 능력 사용
    "gemini-3.1-pro-preview": types.GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=4096,
    ),
}
```

### 파라미터 설명

| 파라미터 | 설명 |
|---|---|
| `temperature` | 생성 결과의 무작위성 조절 (낮을수록 일관된 답변, 높을수록 다양한 답변) |
| `top_p` | 누적 확률 p 이하의 토큰 집합에서만 선택 (어휘 다양성 조절) |
| `max_output_tokens` | 생성할 수 있는 최대 출력 토큰 수 |
| `thinking_budget` | Flash 전용 — 내부 추론에 사용할 최대 토큰 수 (`0` = 비활성화, `-1` = 동적 자동 결정) |

### thinking_budget 기준표 (Flash 전용)

| 값 | 추론 수준 | 적합한 작업 |
|:---:|:---:|---|
| `0` | 비활성화 | 단순 질문, 빠른 응답 필요 시 |
| `1 ~ 1024` | 낮음 (low) | 간단한 논리 추론, 기본 수학 |
| `1025 ~ 8192` | 중간 (medium) | 복잡한 추론, 다단계 문제 |
| `8193 ~ 24576` | 높음 (high) | 고난도 수학, 심층 분석 |
| `-1` | 동적 | 모델이 문제 복잡도에 따라 자동 결정 |

## 주의 사항

- **Rate Limits (호출 제한)**: Pro 모델 등 특정 모델의 무과금 호출 한도(RPM)를 초과하지 않도록 코드 내에 대기 시간(`time.sleep(2)`)이 포함되어 있습니다. 빈번한 호출이 예상될 시 이를 조절해 주세요.
