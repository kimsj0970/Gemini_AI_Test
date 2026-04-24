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
    actions = [
        ("search", "검색합니다"), ("check", "확인합니다"), ("compare", "비교합니다"), 
        ("reserve", "예약합니다"), ("register", "등록합니다"), ("purchase", "결제합니다"),
        ("review", "리뷰 조회"), ("bookmark", "찜하기"), ("track", "배송추적")
    ]
    categories = [("fashion", "의류"), ("electronics", "가전"), ("food", "식품"), 
                  ("beauty", "뷰티"), ("furniture", "가구"), ("sports", "스포츠")]
    targets = [("price", "가격"), ("stock", "재고"), ("spec", "스펙"), 
               ("delivery", "배송정보"), ("discount", "할인율")]
    
    while len(dummy_tools) < count:
        action = random.choice(actions)
        category = random.choice(categories)
        target = random.choice(targets)

        tool_name = f"{action[0]}_{category[0]}_{target[0]}_{len(dummy_tools)}"
        
        # purchase/reserve 도구는 자연스러운 description
        if action[0] in ["purchase", "reserve"]:
            description = f"{category[1]} 상품을 쿠폰 적용하여 {action[1]}."
        else:
            description = f"이 도구는 {category[1]} 카테고리 상품의 {target[1]} {action[1]}."
        
        # 결제,예약,등록 도구는 30% 확률로 정답과 비슷한 파라미터 구조를 가진 도구 제작
        if random.random() < 0.3 and action[0] in ["purchase", "reserve", "register"]:
            parameters = {
                "type": "OBJECT",
                "properties": {
                    "item_name": {"type": "STRING", "description": "상품명"},
                    "size": {"type": "STRING", "description": "상품 사이즈"},
                    "color": {"type": "STRING", "description": "상품 색상"},
                    "coupon_code": {"type": "STRING", "description": "쿠폰 코드"}
                },
                "required": ["item_name"]
            }
        else:
            parameters = {
                "type": "OBJECT",
                "properties": {
                    "item_name": {"type": "STRING", "description": "상품명 또는 키워드"},
                    "options": {"type": "STRING", "description": "사이즈, 색상 등 옵션"},
                    "user_id": {"type": "STRING", "description": "사용자 ID"}
                },
                "required": ["item_name"]
            }
        
        dummy_tools.append({
            "name": tool_name,
            "description": description,
            "parameters": parameters
        })
    return dummy_tools

# 🔥 Turn 1, 2용 정답 도구 (재고 확인)
check_stock_tool = {
    "name": "check_fashion_stock",
    "description": "이 도구는 의류 카테고리 상품의 재고 확인합니다.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "item_name": {"type": "STRING", "description": "상품명 또는 키워드"},
            "options": {"type": "STRING", "description": "사이즈, 색상 등 옵션"},
            "user_id": {"type": "STRING", "description": "사용자 ID"}
        },
        "required": ["item_name"]
    }
}

# Turn 3용 정답 도구 (결제)
purchase_tool = {
    "name": "execute_direct_purchase",
    "description": "의류 상품을 쿠폰 적용하여 결제하고 주문을 진행합니다.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "item_name": {"type": "STRING", "description": "구매할 상품명"},
            "size": {"type": "STRING", "description": "상품 사이즈"},
            "color": {"type": "STRING", "description": "상품 색상"},
            "coupon_code": {"type": "STRING", "description": "할인 쿠폰"}
        },
        "required": ["item_name"]
    }
}

def prepare_test_suite(total_count, target_pos="middle"):
    if total_count < 3: return []  # 최소 3개 필요 (더미 + 재고확인 + 결제)
    
    # 더미 도구 생성 (total - 2개, 재고확인/결제 도구 제외)
    tools = generate_dummy_tools(total_count - 2)
    
    # 중간 위치 계산
    insert_idx = len(tools) // 2 if target_pos == "middle" else (0 if target_pos == "start" else len(tools))
    
    # 정답 도구 2개 추가 (재고확인, 결제)
    tools.insert(insert_idx, check_stock_tool)
    tools.insert(insert_idx + 1, purchase_tool)
    
    return tools

# ==========================================
# 2. 멀티턴 실행 및 결과 출력
# ==========================================
def run_multiturn_test(tools_list):
    models_to_test = [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview"
    ]
    
    prompts = [
        {
            "user": "검은색 무지 티셔츠 L 사이즈 재고 있어?",
            "expected_pattern": "check_fashion_stock",
            "mock_response": {"status": "success", "item": "검은 티셔츠 L", "stock": 7},
            "turn": 1
        },
        {
            "user": "좋아, 그럼 그거랑 같이 입을 흰색 M 사이즈도 재고 확인해줘.",
            "expected_pattern": "check_fashion_stock",
            "mock_response": {"status": "success", "item": "흰 티셔츠 M", "stock": 4},
            "turn": 2
        },
        {
            "user": "둘 다 장바구니에 넣고 아까 말한 검은색만 10% 쿠폰 써서 바로 결제해줘!",
            "expected_tool": "execute_direct_purchase",
            "turn": 3
        }
    ]
    
    print("\n" + "="*70)
    print(f"[멀티턴 테스트] 도구 {len(tools_list)}개")
    
    # 🔥 확인: 정답 도구들이 포함되었는지
    check_tools = [t for t in tools_list if 'check_fashion_stock' in t['name']]
    purchase_tools = [t for t in tools_list if 'purchase' in t['name']]
    coupon_tools = [t for t in tools_list if 'coupon_code' in t['parameters'].get('properties', {})]
    
    print(f"- 'check_fashion_stock' 도구: {len(check_tools)}개")
    print(f"- 'purchase' 포함 도구: {len(purchase_tools)}개")
    print(f"- 'coupon_code' 파라미터 도구: {len(coupon_tools)}개")
    print("="*70 + "\n")

    for model_name in models_to_test:
        print(f"▼ 모델: {model_name} ".ljust(70, "─"))
        try:
            model = genai.GenerativeModel(model_name=model_name, tools=tools_list)
            chat = model.start_chat()
            all_success = True
            
            for p in prompts:
                turn, user_input = p['turn'], p['user']
                print(f"👤 T{turn} 사용자: '{user_input}'")
                response = chat.send_message(user_input)
                part = response.candidates[0].content.parts[0] if response.candidates else None
                
                if part and part.function_call:
                    call_name = part.function_call.name
                    call_args = dict(part.function_call.args)
                    
                    # 검증
                    if turn in [1, 2]:
                        is_correct = p['expected_pattern'] in call_name
                        status = "✅ 정답" if is_correct else f"❌ 오답 (예상: {p['expected_pattern']} 패턴)"
                    else:
                        is_correct = call_name == p['expected_tool']
                        status = "✅ 정답" if is_correct else f"❌ 오답 (예상: {p['expected_tool']})"
                    
                    if not is_correct:
                        all_success = False
                    
                    print(f"│ {status}")
                    print(f"│ 호출 도구: {call_name}")
                    print(f"│ 파라미터: {call_args}")
                    
                    # Turn 1, 2는 미리 정의한 mock 응답 전달
                    if turn < 3:
                        tool_res = {
                            "function_response": {
                                "name": call_name,
                                "response": p['mock_response']
                            }
                        }
                        ai_reply = chat.send_message([tool_res])
                        if ai_reply.text:
                            print(f"│ AI 비서: '{ai_reply.text.strip()}'")
                else:
                    print(f"│ 도구 미사용: {response.text.strip() if response.text else '응답 없음'}")
                    all_success = False
                print("│")
            
            print(f"└─ 최종 결과: {'전체 성공!' if all_success else '일부 실패'}")
                
        except Exception as e:
            print(f"│ [에러] {e}")
        print("└" + "─"*69 + "\n")

if __name__ == "__main__":
    TOTAL_TOOL_COUNT = 100
    final_tools = prepare_test_suite(TOTAL_TOOL_COUNT, "middle")
    
    for i in range(3):
        print(f"\n[{i+1}회차 반복 실행]")
        run_multiturn_test(final_tools)