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
        
        if action[0] in ["purchase", "reserve"]:
            description = f"{category[1]} 상품을 쿠폰 적용하여 {action[1]}."
        else:
            description = f"이 도구는 {category[1]} 카테고리 상품의 {target[1]} {action[1]}."
        
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
    if total_count < 3: return [] 
    tools = generate_dummy_tools(total_count - 2)
    insert_idx = len(tools) // 2 if target_pos == "middle" else (0 if target_pos == "start" else len(tools))
    tools.insert(insert_idx, check_stock_tool)
    tools.insert(insert_idx + 1, purchase_tool)
    return tools

# ==========================================
# 2. 멀티턴 및 혼동(FP/FN) 평가 실행
# ==========================================
def run_multiturn_test(tools_list):
    models_to_test = [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview"
    ]
    
    # 🔥 프롬프트에 requires_tool 속성 추가
    prompts = [
        {
            "user": "검은색 무지 티셔츠 L 사이즈 재고 있어?",
            "requires_tool": True, # 도구 필수 (TP/FN 측정)
            "expected_pattern": "check_fashion_stock",
            "mock_response": {"status": "success", "item": "검은 티셔츠 L", "stock": 7},
            "turn": 1
        },
        {
            "user": "아 다행이다! 근데 나 오늘 기분이 좀 꿀꿀한데 재밌는 농담 하나만 해줄래?",
            "requires_tool": False, # 도구 불필요, 자연어 대답 (TN/FP 측정)
            "expected_pattern": None,
            "mock_response": None,
            "turn": 2
        },
        {
            "user": "ㅋㅋ 고마워. 그럼 아까 그거랑 같이 입을 흰색 M 사이즈도 재고 확인해줘.",
            "requires_tool": True, # 도구 필수 (TP/FN 측정)
            "expected_pattern": "check_fashion_stock",
            "mock_response": {"status": "success", "item": "흰 티셔츠 M", "stock": 4},
            "turn": 3
        },
        {
            "user": "둘 다 장바구니에 넣고 아까 말한 검은색만 10% 쿠폰 써서 바로 결제해줘!",
            "requires_tool": True, # 도구 필수 (TP/FN 측정)
            "expected_tool": "execute_direct_purchase",
            "mock_response": {"status": "success", "msg": "결제 완료"},
            "turn": 4
        }
    ]
    
    print("\n" + "="*70)
    print(f"[멀티턴 테스트] 도구 {len(tools_list)}개")
    print("="*70 + "\n")

    for model_name in models_to_test:
        print(f"▼ 모델: {model_name} ".ljust(70, "─"))
        
        # 모델별 측정 지표 초기화
        metrics = {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "WrongTool": 0}
        
        try:
            model = genai.GenerativeModel(model_name=model_name, tools=tools_list)
            chat = model.start_chat()
            all_success = True
            
            for p in prompts:
                turn, user_input = p['turn'], p['user']
                print(f"👤 T{turn} 사용자: '{user_input}'")
                
                response = chat.send_message(user_input)
                part = response.candidates[0].content.parts[0] if response.candidates else None
                is_tool_called = bool(part and part.function_call)
                
                # ==== [평가 로직] ====
                if p['requires_tool']: # 도구가 필요한 상황
                    if is_tool_called:
                        call_name = part.function_call.name
                        call_args = dict(part.function_call.args)
                        
                        # 도구 이름이 정답과 맞는지 확인
                        is_correct = False
                        if p.get('expected_pattern') and p['expected_pattern'] in call_name:
                            is_correct = True
                        elif p.get('expected_tool') and call_name == p['expected_tool']:
                            is_correct = True
                            
                        if is_correct:
                            print(f"│ ✅ 정상(TP) - 올바른 도구 호출: {call_name}")
                            metrics["TP"] += 1
                        else:
                            print(f"│ ❌ 오답(Wrong Tool) - 엉뚱한 도구 호출: {call_name}")
                            metrics["WrongTool"] += 1
                            all_success = False
                            
                        print(f"│ 파라미터: {call_args}")
                        
                        # 다음 턴을 위해 가짜 응답 넘겨주기
                        if p.get('mock_response'):
                            tool_res = {"function_response": {"name": call_name, "response": p['mock_response']}}
                            ai_reply = chat.send_message([tool_res])
                            if ai_reply.text:
                                print(f"│ AI : '{ai_reply.text.strip()}'")
                                
                    else: # 도구가 필요한데 안 쓴 경우
                        print(f"│ ❌ 오답(FN) - 도구를 써야 하는데 자연어로 대답함")
                        print(f"│ AI : '{response.text.strip()}'")
                        metrics["FN"] += 1
                        all_success = False

                else: # 도구가 필요 없는 상황 (일상 대화)
                    if not is_tool_called:
                        print(f"│ ✅ 정상(TN) - 도구 미호출 및 자연어 응답 성공")
                        print(f"│ AI : '{response.text.strip()}'")
                        metrics["TN"] += 1
                    else: # 도구가 필요 없는데 뜬금없이 호출한 경우
                        call_name = part.function_call.name
                        print(f"│ ❌ 오답(FP) - 일상 대화에 불필요한 도구 호출: {call_name}")
                        metrics["FP"] += 1
                        all_success = False
                print("│")
            
            # 모델별 최종 성적표 출력
            print(f"└─ [결과 요약] TP(정상호출):{metrics['TP']} | TN(정상대화):{metrics['TN']} | FP(과잉호출):{metrics['FP']} | FN(미호출):{metrics['FN']} | 오호출:{metrics['WrongTool']}")
            print(f"└─ 최종 결과: {'전체 성공!' if all_success else '일부 실패'}\n")
                
        except Exception as e:
            print(f"│ [에러] {e}")
            print("└" + "─"*69 + "\n")

if __name__ == "__main__":
    TOTAL_TOOL_COUNT = 300 # 도구 개수 조절
    final_tools = prepare_test_suite(TOTAL_TOOL_COUNT, "middle")
    
    for i in range(3):
        print(f"\n[{i+1}회차 반복 실행]")
        run_multiturn_test(final_tools)