# Gemini Model Function Calling Stress Test

이 프로젝트는 다수의 도구(Tools)가 주어졌을 때 여러 Gemini 모델들이 질문의 의도에 맞는 정확한 도구를 선택하여 호출(Function Calling)할 수 있는지 평가하는 스트레스 테스트 스크립트입니다. 

특히 비슷한 이름이나 설명을 가진 **함정 도구(Poison Pills)**들을 배치하여 모델의 맥락 이해도 및 도구 선택 정확도를 확인합니다.

## 🚀 주요 기능

- **다량의 더미 도구 생성**: 주어진 갯수만큼 무작위의 영어 도구 이름과 한글 설명을 가진 더미 도구를 동적으로 생성합니다.
- **함정 도구(Poison Pills)**: 정답 도구와 의도적으로 비슷한 이름(`activate_emergency_protocol_test` 등)이나 유사한 설명('대피' 대신 '방어'나 '대응' 사용)을 가진 함정 도구를 추가하여 모델의 분별력을 깐깐하게 테스트합니다.
- **다중 모델 비교**: 스크립트 실행 한 번에 다음 3가지 모델을 호출하여 결과를 비교합니다.
  - `gemini-3.1-pro-preview`
  - `gemini-3-flash-preview`
  - `gemini-3.1-flash-lite-preview`
- **테스트 환경 조정**: `main.py` 코드 하단의 `if __name__ == "__main__":` 블록에서 다음 변수를 변경하여 스트레스 강도를 조절할 수 있습니다.
  - `TOTAL_TOOL_COUNT`: 전체 도구 갯수 (예: 30, 100, 300)
  - `POSITION`: 리스트 내 정답 도구의 위치 (`start`, `middle`, `end`)

## 📦 설치 및 실행 방법

1. **의존성 설치**: 패키지 관리자인 `uv`를 통해 필요한 패키지를 설치합니다.
   ```bash
   uv add google-generativeai python-dotenv
   ```
2. **환경 변수 설정**: 프로젝트 루트 경로에 `.env` 파일을 생성하고 발급받은 Gemini API 키를 입력합니다.
   ```env
   GEMINI_API_KEY="your_api_key_here"
   ```
3. **스크립트 실행**:
   ```bash
   uv run main.py
   ```

## 🧪 기본 테스트 시나리오

- **사용자 프롬프트**: *"지금 7구역에 실제 지진이 났어! 빨리 긴급 대피 시스템 가동해!"*
- **정답 도구**: 
  - `name`: `activate_emergency_protocol`
  - 올바른 파라미터 전달: `{"disaster_type": "지진", "zone_number": 7}`

스트레스 테스트를 실행하면 각 모델이 정답 도구를 성공적으로 찾아서 파라미터와 함께 호출했는지, 아니면 함정 도구를 선택하거나(실패/환각) 도구 사용을 아예 하지 못했는지 판단하여 콘솔에 결과를 자세히 출력합니다.