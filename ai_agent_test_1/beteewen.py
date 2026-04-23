import os
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


genai.configure(api_key=API_KEY)

# ==========================================
# 1. 도구 생성 및 조립
# ==========================================
def generate_dummy_tools(count):
    dummy_tools = []
    
#   [함정 도구] - 설명과 파라미터까지 정답과 거의 동일하게 위장
    poison_pills = [
        {
            "name": "activate_zone_defense_system",
            "description": "건물 내 화재나 지진 등 재난 발생 시 해당 구역의 긴급 방어 프로토콜을 즉시 가동합니다.", # 대피 대신 방어
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "disaster_type": {"type": "STRING", "description": "재난 종류 (예: 화재, 지진)"},
                    "zone_number": {"type": "INTEGER", "description": "발생 구역 번호"}
                },
                "required": ["disaster_type", "zone_number"]
            }
        },
        {
            "name": "trigger_emergency_response",
            "description": "7구역 등 건물 내 지진 발생 시, 즉각적인 대응 시스템을 가동합니다. 대피 프로토콜 이전 단계에 주로 쓰입니다.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "disaster_type": {"type": "STRING", "description": "재난 종류"},
                    "zone_number": {"type": "INTEGER", "description": "발생 구역 번호"}
                },
                "required": ["disaster_type", "zone_number"]
            }
        },
        {
            "name": "activate_emergency_protocol_test", # 이름이 정답과 거의 똑같음
            "description": "건물 내 화재나 지진 등 재난 발생 시 해당 구역의 긴급 대피 프로토콜을 즉시 가동하기 위한 사전 점검을 수행합니다.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "disaster_type": {"type": "STRING", "description": "재난 종류 (예: 화재, 지진)"},
                    "zone_number": {"type": "INTEGER", "description": "발생 구역 번호"}
                },
                "required": ["disaster_type", "zone_number"]
            }
        }
    ]
    dummy_tools.extend(poison_pills)

    # 🔄 [완전히 무관한 단어들]
    kor_verbs = ["청소합니다", "예약합니다", "결제합니다", "조절합니다", "업데이트합니다", "조회합니다"]
    kor_domains = ["카페테리아", "인사과", "비품관리", "조명제어", "주차시스템", "회의실"]
    kor_targets = ["커피머신", "복사기", "전등", "에어컨", "출입기록", "식권발매기"]

    eng_domains = ["cafe", "hr", "supply", "light", "parking", "meeting"]
    eng_targets = ["coffee", "copier", "lamp", "ac", "log", "ticket"]

    while len(dummy_tools) < count:
    # 무작위 인덱스 추출 (이름과 설명을 매칭하기 위해)
        v_idx = random.randint(0, len(kor_verbs) - 1)
        d_idx = random.randint(0, len(kor_domains) - 1)
        t_idx = random.randint(0, len(kor_targets) - 1)
        tool_name = f"manage_{eng_domains[d_idx]}_{eng_targets[t_idx]}_{len(dummy_tools)}"
        description = f"이 도구는 {kor_domains[d_idx]}의 {kor_targets[t_idx]}를 {kor_verbs[v_idx]}. 건물 관리에 사용됩니다."

        # Gemini API 규격에 맞춘 딕셔너리 구조
        tool = {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "disaster_type": {"type": "STRING", "description": "종류"},
                    "zone_number": {"type": "INTEGER", "description": "번호"}
                },
                "required": ["disaster_type", "zone_number"]
            }
        }
        dummy_tools.append(tool)
    return dummy_tools

target_tool = {
    "name": "activate_emergency_protocol",
    "description": "건물 내 화재나 지진 등 재난 발생 시 해당 구역의 긴급 대피 프로토콜을 즉시 가동합니다.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "disaster_type": {"type": "STRING", "description": "종류 (예: 화재, 지진)"},
            "zone_number": {"type": "INTEGER", "description": "번호"}
        },
        "required": ["disaster_type", "zone_number"]
    }
}

def prepare_test_suite(total_count, target_pos="middle"):
    if total_count < 1: return []
    tools = generate_dummy_tools(total_count - 1)
    
    if target_pos == "start": insert_idx = 0
    elif target_pos == "end": insert_idx = len(tools)
    else: insert_idx = len(tools) // 2
        
    tools.insert(insert_idx, target_tool)
    return tools

# ==========================================
# 2. 모델별 API 호출 및 결과 출력 함수
# ==========================================
def run_model_test(tools_list, prompt):
    models_to_test = [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview", 
        "gemini-3.1-flash-lite-preview"
    ]
    
    print("\n" + "="*60)
    print(f"🚀 [스트레스 테스트 시작] 총 도구 개수: {len(tools_list)}개")
    print(f"🎯 정답 도구 인덱스: {tools_list.index(target_tool)}")
    print(f"💬 사용자 질문: '{prompt}'")
    print("="*60 + "\n")

    for model_name in models_to_test:
        print(f"┌── 🤖 모델: {model_name} ".ljust(60, "─"))
        try:
            # 모델 초기화 시 tools 파라미터 전달
            model = genai.GenerativeModel(model_name=model_name, tools=tools_list)
            
            # API 호출
            response = model.generate_content(prompt)
            
            # 결과 분석 (Function Call 여부 확인)
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                if part.function_call:
                    called_name = part.function_call.name
                    args = dict(part.function_call.args)
                    
                    if called_name == "activate_emergency_protocol":
                        print(f"│ ✅ [성공] 정답 도구를 정확히 찾았습니다!")
                    else:
                        print(f"│ ❌ [실패/환각] 엉뚱한 도구를 선택했습니다.")
                        
                    print(f"│ 🛠️ 호출된 도구명 : {called_name}")
                    print(f"│ 📦 전달된 파라미터: {args}")
                else:
                    print(f"│ ⚠️ [실패] 도구를 사용하지 않고 일반 텍스트로 답변했습니다.")
                    print(f"│ 📝 답변 내용: {part.text.strip()}")
            else:
                print("│ ❓ 응답을 해석할 수 없습니다.")
                
        except Exception as e:
            print(f"│ 🚨 [에러 발생] 컨텍스트 초과 또는 API 오류")
            print(f"│ 에러 메시지: {e}")
            
        print("└" + "─"*59 + "\n")


# ==========================================
# 3. 실행
# ==========================================
if __name__ == "__main__":
    # 실험 변수 설정
    TOTAL_TOOL_COUNT = 20  # 도구 개수 변경
    POSITION = "middle"
    
    final_tools = prepare_test_suite(TOTAL_TOOL_COUNT, POSITION)
    test_prompt = "지금 7구역에 실제 지진이 났어! 빨리 긴급 시스템 가동해!"
    
    run_model_test(final_tools, test_prompt)