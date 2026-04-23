import os
import random
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# ==========================================
# 1. 도구 생성 및 조립 (B2C 쇼핑몰 멀티턴 시나리오)
# ==========================================
def generate_dummy_tools(count):
    dummy_tools = []
    
    # [쇼핑몰 맞춤형 단어]
    actions = [("search", "검색합니다"), ("check", "확인합니다"), ("compare", "비교합니다"), 
               ("review", "평가 및 리뷰를 조회합니다"), ("bookmark", "찜 목록에 추가합니다"), ("track", "배송 상태를 추적합니다")]
    categories = [("fashion", "의류/패션"), ("electronics", "가전제품"), ("food", "식품"), 
                  ("beauty", "화장품"), ("furniture", "가구"), ("sports", "스포츠용품")]
    targets = [("price", "가격을"), ("stock", "재고 수량을"), ("spec", "상세 스펙을"), 
               ("delivery", "배송 정보를"), ("discount", "할인율을")]
    
    while len(dummy_tools) < count:
        action = random.choice(actions)
        category = random.choice(categories)
        target = random.choice(targets)

        tool_name = f"{action[0]}_{category[0]}_{target[0]}_{len(dummy_tools)}"
        description = f"이 도구는 {category[1]} 카테고리 상품의 {target[1]} {action[1]}. 쇼핑몰 탐색에 사용됩니다."
        
        # 자연어 검색어를 받을 수 있도록 파라미터 구조 수정
        tool = {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "item_name": {"type": "STRING", "description": "조회할 상품명 또는 키워드"},
                    "options": {"type": "STRING", "description": "사이즈, 색상 등 추가 옵션 정보"},
                    "user_id": {"type": "STRING", "description": "사용자 ID (선택사항)"}
                },
                "required": ["item_name"]
            }
        }
        dummy_tools.append(tool)
        
    return dummy_tools

# [정답 도구] - 최종 결제 목적지
target_tool = {
    "name": "execute_direct_purchase",
    "description": "선택한 상품(옵션 포함)에 쿠폰/포인트를 적용하여 즉시 실제 결제를 진행하고 주문을 완료합니다.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "item_name": {"type": "STRING", "description": "구매할 상품명"},
            "size": {"type": "STRING", "description": "상품 사이즈"},
            "color": {"type": "STRING", "description": "상품 색상"},
            "coupon_code": {"type": "STRING", "description": "적용할 할인 쿠폰"}
        },
        "required": ["item_name"]
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
# 2. 멀티턴 실행 및 결과 출력 함수 (에러 수정본)
# ==========================================
def run_multiturn_test(tools_list):
    # 테스트할 모델 목록
    models_to_test = [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview", 
        "gemini-3.1-flash-lite-preview"
    ]
    
    turn_1_prompt = "내 장바구니에 검은색 무지 티셔츠 L 사이즈 담아둔 거 재고 확인 좀 해줄래?"
    turn_2_prompt = "좋아, 그거 10% 할인 쿠폰 먹여서 지금 바로 결제해줘!"
    
    print("\n" + "="*65)
    print(f"[B2C 멀티턴 스트레스 테스트 시작] 총 도구 개수: {len(tools_list)}개")
    print(f"정답 도구(결제) 인덱스 위치: {tools_list.index(target_tool)}")
    print("="*65 + "\n")

    for model_name in models_to_test:
        print(f"▼ 모델: {model_name} ".ljust(65, "─"))
        try:
            model = genai.GenerativeModel(model_name=model_name, tools=tools_list)
            chat = model.start_chat()
            
            # ----------------------------------------------------
            # [Turn 1] 탐색 요청
            # ----------------------------------------------------
            print(f"👤 사용자: '{turn_1_prompt}'")
            response1 = chat.send_message(turn_1_prompt)
            
            # 응답 객체에서 올바르게 function_call 추출
            part1 = response1.candidates[0].content.parts[0] if response1.candidates and response1.candidates[0].content.parts else None
            
            first_tool_called = None
            if part1 and part1.function_call:
                first_tool_called = part1.function_call.name
                args1 = dict(part1.function_call.args)
                print(f"│ 🔍 [탐색 도구 호출됨] {first_tool_called}")
                print(f"│ 📦 전달된 파라미터: {args1}")
                
                # 시스템의 가짜 응답을 AI에게 주입
                tool_response_msg = {
                    "function_response": {
                        "name": first_tool_called,
                        "response": {"status": "success", "stock": 5}
                    }
                }
                print(f"│ 💻 [시스템] AI에게 '재고 5개 있음' 데이터를 전달합니다...")
                
                # AI가 데이터를 바탕으로 사용자에게 자연어로 답변
                ai_middle_response = chat.send_message([tool_response_msg])
                if ai_middle_response.text:
                    print(f"│ 🤖 AI 비서: '{ai_middle_response.text.strip()}'")
                else:
                    print(f"│ 🤖 AI 비서: (답변 생략)")
            else:
                print(f"│ ⚠️ Turn 1에서 도구를 호출하지 않고 답변했습니다: {response1.text}")

            # ----------------------------------------------------
            # [Turn 2] 결제 요청 (문맥 파악 테스트)
            # ----------------------------------------------------
            print(f"\n👤 사용자: '{turn_2_prompt}'")
            response2 = chat.send_message(turn_2_prompt)
            
            # 2턴 응답 객체에서도 올바르게 function_call 추출
            part2 = response2.candidates[0].content.parts[0] if response2.candidates and response2.candidates[0].content.parts else None
            
            if part2 and part2.function_call:
                final_called_name = part2.function_call.name
                final_args = dict(part2.function_call.args)
                
                if final_called_name == "execute_direct_purchase":
                    print(f"│ ✅ [최종 성공] 정답 도구(결제)를 정확히 호출했습니다!")
                else:
                    print(f"│ ❌ [실패/환각] 엉뚱한 도구를 호출했습니다.")
                    
                print(f"│ 🛠️ 최종 호출 도구: {final_called_name}")
                print(f"│ 📦 전달된 파라미터: {final_args}")
            else:
                print(f"│ ⚠️ [최종 실패] 도구를 사용하지 않고 텍스트로만 답변했습니다.")
                print(f"│ 📝 답변 내용: {response2.text.strip() if response2.text else '응답 없음'}")
                
        except Exception as e:
            print(f"│ [에러 발생] {e}")
            
        print("└" + "─"*64 + "\n")


# ==========================================
# 3. 실행
# ==========================================
if __name__ == "__main__":
    TOTAL_TOOL_COUNT = 100  # 여기서 도구 개수를 조절하며 모델의 한계를 테스트하세요.
    POSITION = "middle"
    
    final_tools = prepare_test_suite(TOTAL_TOOL_COUNT, POSITION)
    run_multiturn_test(final_tools)