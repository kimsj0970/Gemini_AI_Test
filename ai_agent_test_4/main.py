import os
import random
import google.generativeai as genai
from dotenv import load_dotenv
from inventory import check_stock, process_payment, apply_coupon, start_delivery


load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.1-flash-lite-preview"

# 실제 도구와 관련 없는 패션 쇼핑 주제의 가짜 도구 20개 (고정)
_DECOY_PARAMS = {
    "type": "OBJECT",
    "properties": {
        "item_name": {"type": "STRING", "description": "상품명"},
        "options":   {"type": "STRING", "description": "기타 옵션"},
    },
    "required": ["item_name"],
}

DECOY_TOOLS = [
    {"name": "browse_new_arrivals",       "description": "이번 시즌 새로 입고된 신상품 목록을 조회합니다.",            "parameters": _DECOY_PARAMS},
    {"name": "get_size_guide",            "description": "브랜드별 의류 사이즈 측정 기준표를 제공합니다.",             "parameters": _DECOY_PARAMS},
    {"name": "search_by_brand",           "description": "특정 브랜드의 전체 상품 목록을 검색합니다.",               "parameters": _DECOY_PARAMS},
    {"name": "get_outfit_recommendation", "description": "선택한 상품과 어울리는 코디 조합을 추천합니다.",            "parameters": _DECOY_PARAMS},
    {"name": "view_trending_items",       "description": "현재 가장 많이 조회되는 인기 상품을 조회합니다.",           "parameters": _DECOY_PARAMS},
    {"name": "add_to_wishlist",           "description": "마음에 드는 상품을 위시리스트에 추가합니다.",              "parameters": _DECOY_PARAMS},
    {"name": "get_product_reviews",       "description": "상품에 등록된 구매자 리뷰와 평점을 조회합니다.",           "parameters": _DECOY_PARAMS},
    {"name": "compare_items",             "description": "선택한 두 상품의 스펙·가격·소재를 비교합니다.",            "parameters": _DECOY_PARAMS},
    {"name": "get_membership_grade",      "description": "현재 회원 등급과 등급별 혜택 내용을 조회합니다.",          "parameters": _DECOY_PARAMS},
    {"name": "view_sale_events",          "description": "현재 진행 중인 할인 이벤트와 기간을 조회합니다.",          "parameters": _DECOY_PARAMS},
    {"name": "get_loyalty_points",        "description": "보유한 적립 포인트 잔액과 만료 예정 포인트를 조회합니다.", "parameters": _DECOY_PARAMS},
    {"name": "find_offline_store",        "description": "가까운 오프라인 매장 위치와 영업시간을 안내합니다.",       "parameters": _DECOY_PARAMS},
    {"name": "get_fabric_info",           "description": "상품의 소재·세탁 방법·원산지 정보를 조회합니다.",         "parameters": _DECOY_PARAMS},
    {"name": "view_order_history",        "description": "사용자의 전체 주문 내역과 상태를 조회합니다.",             "parameters": _DECOY_PARAMS},
    {"name": "subscribe_restock_alert",   "description": "품절된 상품의 재입고 시 알림을 신청합니다.",              "parameters": _DECOY_PARAMS},
    {"name": "get_style_tips",            "description": "계절·체형·TPO에 맞는 스타일링 팁을 제공합니다.",          "parameters": _DECOY_PARAMS},
    {"name": "view_cart",                 "description": "현재 장바구니에 담긴 상품 목록과 수량을 조회합니다.",      "parameters": _DECOY_PARAMS},
    {"name": "get_return_policy",         "description": "상품 유형별 반품·교환 가능 기간과 조건을 안내합니다.",    "parameters": _DECOY_PARAMS},
    {"name": "list_limited_editions",     "description": "한정판·콜라보 상품의 출시 일정과 수량을 조회합니다.",     "parameters": _DECOY_PARAMS},
    {"name": "get_packaging_options",     "description": "선물 포장 서비스 종류와 추가 비용을 안내합니다.",         "parameters": _DECOY_PARAMS},
]


TOOLS = [
    {
        # 1단계: 재고 확인 — 다음 도구 이름 미명시, 흐름만 암시
        "name": "check_fashion_stock",
        "description": (
            "의류 상품의 재고를 확인합니다. "
            "재고 확인 후 고객이 구매를 원하면 결제 단계로 넘어갑니다."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "item_name": {"type": "STRING", "description": "상품명 또는 종류 (예: 티셔츠, 수영복)"},
                "size":      {"type": "STRING", "description": "사이즈 (S/M/L/XL 등), 없으면 생략"},
                "color":     {"type": "STRING", "description": "색상 (black/white/blue 등), 없으면 생략"},
            },
            "required": ["item_name"],
        },
    },
    {
        # 2단계: 기본 결제 — 다음 도구 이름 미명시, 흐름만 암시
        "name": "process_payment",
        "description": (
            "상품 결제를 처리합니다. "
            "결제가 완료되면 쿠폰 적용 단계로 이어집니다."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "item_name": {"type": "STRING", "description": "구매할 상품명"},
                "size":      {"type": "STRING", "description": "사이즈"},
                "color":     {"type": "STRING", "description": "색상"},
            },
            "required": ["item_name"],
        },
    },
    {
        # 3단계: 쿠폰 적용 — 다음 도구 이름 미명시, 흐름만 암시
        # order_id와 amount는 모델이 이전 단계(process_payment) 결과에서 꺼내서 넘겨준다
        "name": "apply_coupon_payment",
        "description": (
            "주문에 쿠폰을 적용합니다. "
            "쿠폰 처리가 끝나면 배달이 시작될 수 있습니다."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "order_id":    {"type": "STRING", "description": "결제 단계에서 발급된 주문번호"},
                "amount":      {"type": "INTEGER", "description": "결제 단계에서 받은 결제 금액"},
                "coupon_code": {"type": "STRING", "description": "쿠폰 코드 (없으면 생략)"},
            },
            "required": ["order_id", "amount"],
        },
    },
    {
        # 4단계: 배달 시작 (체인의 끝)
        "name": "start_delivery",
        "description": "배달을 시작하고 배송 정보를 안내합니다.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "order_id":  {"type": "STRING", "description": "주문번호"},
                "item_name": {"type": "STRING", "description": "상품명"},
            },
            "required": ["order_id", "item_name"],
        },
    },
]


# ==========================================
# 도구 디스패처
# ─ 모델이 반환한 function_call.name을 보고
#   실제 inventory.py 함수를 골라서 호출한다.
# ─ 즉, 함수를 실제로 실행하는 주체는 이 함수(에이전트 코드)이며,
#   모델은 "이 이름과 인자로 실행해달라"는 요청만 보낸다.
# ==========================================
def dispatch_tool(name: str, args: dict) -> dict:
    if name == "check_fashion_stock":
        # → inventory.check_stock() 호출
        return check_stock(
            item_name=args.get("item_name", ""),
            size=args.get("size"),
            color=args.get("color"),
        )
    if name == "process_payment":
        # → inventory.process_payment() 호출
        return process_payment(
            item_name=args.get("item_name", ""),
            size=args.get("size"),
            color=args.get("color"),
        )
    if name == "apply_coupon_payment":
        # → inventory.apply_coupon() 호출
        return apply_coupon(
            order_id=args.get("order_id", ""),
            amount=int(args.get("amount", 0)),
            coupon_code=args.get("coupon_code"),
        )
    if name == "start_delivery":
        # → inventory.start_delivery() 호출
        return start_delivery(
            order_id=args.get("order_id", ""),
            item_name=args.get("item_name", ""),
        )
    return {"error": f"알 수 없는 도구: {name}"}


# ==========================================
# 에이전트 루프
# ─ 모델과 대화하면서 도구 호출이 끝날 때까지 반복한다.
#
# [루프 한 사이클]
#   1. 모델 응답 확인 (ai가 도구 내용을 보고 다음 도구를 function_call에 넣어줄지 말지 결정)
#   2. function_call이 있으면 → dispatch_tool()로 실제 함수 실행
#   3. 실행 결과를 function_response로 모델에 다시 전달
#   4. function_call이 없으면 → 텍스트 응답 출력 후 루프 종료


# ==========================================
# 시스템 프롬프트 — 도구 이름 없이 흐름만 모호하게 설명한 상황
SYSTEM_PROMPT = (
    "당신은 패션 쇼핑 도우미입니다. "
    "재고가 있다면 사용자는 결제할 수 있습니다. "
    "결제에는 쿠폰을 적용할 수 있으며, 우린 배송도 가능합니다!"
)

def run_agent(user_input: str):
    print(f"\n{'='*60}")
    print(f"사용자: {user_input}")
    print(f"{'='*60}")

    # 실제 도구 4개 + 가짜 도구 20개를 섞어서 모델에 전달
    all_tools = TOOLS + DECOY_TOOLS
    random.shuffle(all_tools)
    print(f"[도구 목록] 총 {len(all_tools)}개 (실제 4개 + 가짜 {len(DECOY_TOOLS)}개)")

    # 모델 초기화 — system_instruction: 모호한 흐름 안내 / tools: 도구별 명시적 설명 포함
    model = genai.GenerativeModel(model_name=MODEL_NAME, tools=all_tools, system_instruction=SYSTEM_PROMPT)
    chat = model.start_chat()

    # 첫 번째 모델 호출: 사용자 메시지 전달
    response = chat.send_message(user_input)

    called_tools = []  # 호출된 도구 이름을 순서대로 기록

    while True:
        parts = response.candidates[0].content.parts if response.candidates else []

        # function_call 있음  →  "이 도구 써줘" (아직 할 일 있음)
        # function_call 없음  →  텍스트 응답 (끝)
        tool_part = next((p for p in parts if p.function_call), None)

        if tool_part is None:
            # 최종 응답 출력 후 호출 순서 요약
            print(f"\nAI: {response.text.strip()}")
            print(f"\n[호출 순서] {' → '.join(called_tools) if called_tools else '도구 미호출'}")
            break

        tool_name = tool_part.function_call.name
        tool_args = dict(tool_part.function_call.args)
        called_tools.append(tool_name)  # 순서 기록

        print(f"\n[도구 호출 요청] {tool_name}")
        print(f"[파라미터] {tool_args}")

        result = dispatch_tool(tool_name, tool_args)
        print(f"[실행 결과] {result}")

        # 실행 결과를 모델에게 다시 전달 → 모델이 다음 단계를 결정
        # 모델이 이전 단계 결과를 읽고 필요한 값을 직접 추출해서 다음 function_call 인자에 알아서 채움
        response = chat.send_message([{
            "function_response": {"name": tool_name, "response": result}
        }])


# ==========================================
# 테스트 시나리오
# ==========================================
if __name__ == "__main__":
    scenarios = [
        
        "검은 티셔츠 L 사이즈 재고 확인해줘. 아, 잠깐만. 생각해 보니 흰색 M 사이즈가 낫겠다. 이걸로 결제해 주는데, 저번에 SAVE10 쿠폰은 썼으니까 이번엔 쿠폰 적용하지 말고 그냥 원가로 바로 결제 진행해.",

        "지금 장바구니에 담아둔 바지 중에서 제일 리뷰 좋은 걸로 알아서 코디 추천해주고, 그거 바로 배송 출발시켜줘",

    ]

    for scenario in scenarios:
        run_agent(scenario)
