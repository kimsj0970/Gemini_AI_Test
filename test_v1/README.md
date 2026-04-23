# Gemini AI 모델 비교 테스트 (Gemini AI Test)

이 프로젝트는 Google의 다양한 Generative AI 모델들을 동일한 프롬프트로 실행하고, 성능(응답 시간, 사용 토큰)과 응답 결과를 비교하기 위한 데모 스크립트입니다.

## 주요 기능
- **다중 모델 비교**: `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite-preview`, `gemini-2.5-flash`, `gemma-4-31b-it` 등 여러 모델을 순차적으로 호출하여 결과를 비교합니다.
- **성능 지표 측정**: 각 모델의 작업 완료까지 걸린 **응답 시간(Latency)**과 **사용 토큰 수(Tokens)**를 계산하여 출력합니다.
- **Gemini 3.1 추론 수준 (thinking_level) 설정**: Gemini 3.1 시리즈부터 지원되는 `thinking_level` 옵션(`minimal`, `low`, `medium`, `high`)을 코드에서 직접 제어해 볼 수 있습니다.

## 사전 준비 사항 (Prerequisites)

이 프로젝트를 실행하기 위해 다음 항목들이 필요합니다:

1. **Python 3.x 환경** (프로젝트 내 `.venv` 가상 환경 사용 권장)
2. **필수 패키지**: `google-generativeai`, `python-dotenv`
3. **Google Gemini API Key** (Google AI Studio에서 발급)

## 설치 및 실행 방법

1. **의존성 설치**
   `pyproject.toml` 또는 `uv.lock` 파일이 준비된 환경이라면 (예: `uv` 패키지 매니저 사용 등) 패키지를 설치합니다.
   (또는 `pip install google-generativeai python-dotenv`를 통해 직접 설치할 수 있습니다)

2. **환경 변수 설정 (.env)**
   프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 발급받은 API 키를 입력합니다.
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **스크립트 실행**
   ```bash
   uv run main.py
   ```

## 코드 설정 및 수정 (main.py)

`main.py` 파일 내의 `configs` 딕셔너리를 통해 각 모델별 세부 설정(Generation Config)을 수정할 수 있습니다.

```python
configs = {
    "gemini-3.1-pro-preview": {"temperature": 1.0, "top_p": 0.95, "max_output_tokens": 200, "thinking_level": "medium"},
    # 필요한 모델과 파라미터(추론 수준 등)를 수정하여 테스트하세요.
}
```

* **temperature**: 생성 결과의 다양성 (낮을수록 일관된 답변, 높을수록 창의적인 답변)
* **thinking_level**: (Gemini 3.1 전용) 모델이 답변을 생성하기 전에 생각하는 깊이 (`minimal`, `low`, `medium`, `high`)

## 주의 사항
* **Rate Limits (호출 제한)**: Pro 모델 등 일부 모델의 호출 당 분당 요청 제한(RPM)에 걸리지 않도록 코드 내에 대기 시간(`time.sleep(2)`)이 포함되어 있습니다. 필요에 따라 조절해 주세요.
