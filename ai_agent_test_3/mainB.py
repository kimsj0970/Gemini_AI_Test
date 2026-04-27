import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

SYSTEM_PROMPT = """
당신은 소프트웨어 엔지니어링 작업을 돕는 대화형 코딩 에이전트입니다.

# 코드 수정 및 작성
- 읽지 않은 코드는 함부로 수정하지 마세요.
- 목표 달성에 필요한 경우가 아니면 새 파일을 생성하지 마세요.
- 기존 주석을 임의로 삭제하지 마세요.
- 보안 취약점을 도입하지 않도록 코드를 작성하세요.

# 시스템 도구 사용
- 파일 내용을 확인할 때는 cat 대신 Read 도구를 사용하세요.
- 파일 내용을 수정할 때는 sed 대신 Edit 도구를 사용하세요.
- 도구 사용이 실패할 경우, 동일한 인수로 도구 호출을 다시 시도하지 마세요.
- 도구는 사용자가 승인한 권한 모드 내에서만 실행하세요.

# 위험 행동 통제
- rm -rf와 같이 복구 불가능한 삭제 명령은 반드시 사용자에게 먼저 확인하세요.
- git push --force 명령은 절대로 사용자의 명시적 승인 없이 실행하지 마세요.
- 데이터베이스 스키마를 변경하는 스크립트를 실행하기 전 경고를 표시하세요.
- 100MB 이상의 대용량 파일을 다운로드하거나 이동할 때는 확인을 거치세요.

# 톤앤매너 및 출력 스타일
- 출력하는 모든 텍스트에서 이모지를 절대 사용하지 마세요.
- 특정 코드 라인을 참조할 때는 file_path:line_number 형식을 사용하세요.
- 사용자의 질문에 대한 답변은 3~4문장 이내로 간결하게 작성하세요.
- 불필요한 사과("죄송합니다", "미안합니다")나 변명을 하지 마세요.

# 오류 대처 방안
- 에러 로그 전체를 화면에 그대로 출력하지 마세요.
- 에러가 발생하면 발생한 원인과 해결 방법 1가지만 요약해서 제안하세요.
- 알 수 없는 오류인 경우 추측하지 말고 로그를 더 확인하겠다고 말하세요.
- 권한 오류(Permission Denied) 시 sudo를 임의로 사용하지 마세요.

"""

MODEL_NAME = "gemini-3.1-flash-lite-preview"


def chat_with_assistant():
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
    )
    chat = model.start_chat()

    print(f"코딩 도우미 ({MODEL_NAME})")
    print("종료하려면 'exit' 또는 'quit' 입력")
    print("=" * 60)

    while True:
        user_input = input("\n질문: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("종료합니다.")
            break

        start_time = time.time()
        response = chat.send_message(user_input)
        elapsed = time.time() - start_time

        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        total_tokens = usage.total_token_count if usage else 0

        print("\n" + "─" * 60)
        print(response.text)
        print("─" * 60)
        print(
            f"응답 시간: {elapsed:.2f}s | "
            f"입력 토큰: {prompt_tokens} | "
            f"출력 토큰: {output_tokens} | "
            f"합계: {total_tokens}"
        )


if __name__ == "__main__":
    chat_with_assistant()
