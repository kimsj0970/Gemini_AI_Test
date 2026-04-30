# Tool Calling Chaining — 도구 설명 형식이 체이닝 정확도에 미치는 영향

## 실험 배경

LLM 기반 서비스를 만들 때 Tool Calling(도구 호출)은 핵심 기능입니다. 모델에게 도구 목록을 전달하면 모델이 상황에 맞는 도구를 골라 호출 요청을 보내고, 그 결과를 받아 다음 행동을 결정합니다.

그런데 실제로 구현하다 보면 자연스럽게 이런 의문이 생깁니다.

> "도구 설명(description)에 다음 도구 이름을 직접 써줘야 체인이 이어질까?"  
> "흐름만 암시해도 모델이 알아서 따라갈 수 있을까?"  
> "시스템 프롬프트의 역할은 얼마나 될까?"

이 프로젝트는 단순히 도구 하나를 고르는 게 아니라 **순서가 있는 체인**을 모델이 스스로 따라가게 만드는 상황에서, 도구 description과 시스템 프롬프트의 작성 방식에 따라 결과가 어떻게 달라지는지 실험합니다.

---

## 실험 구조

### 정답 체인 (4단계)

```
재고 확인 → 결제 처리 → 쿠폰 적용 → 배달 시작
check_fashion_stock → process_payment → apply_coupon_payment → start_delivery
```

### 비교 케이스

| 케이스 | 도구 description | 시스템 프롬프트 |
|--------|-----------------|----------------|
| 1 | 다음 도구 이름 명시 | 모호 (흐름만 설명) |
| 2 | 다음 도구 이름 미명시, 흐름만 암시 | 모호 (흐름만 설명) |
| 3 | 케이스 2 + 함수 응답에 다음 단계 재안내 메시지 추가 | 모호 (흐름만 설명) |

**도구 description 비교 예시** (`check_fashion_stock` 기준)

```
[명시적]
"재고가 있고 사용자가 구매를 원한다면 process_payment 도구를 호출하세요."

[모호]
"재고 확인 후 고객이 구매를 원하면 결제 단계로 넘어갑니다."
```

**시스템 프롬프트** (공통, 모호)
```
"재고가 있다면 사용자는 결제할 수 있습니다.
 결제에는 쿠폰을 적용할 수 있으며, 우린 배송도 가능합니다!"
```

### 노이즈 도구 (20개)

실제 도구 4개 외에 패션 쇼핑 주제의 관련 없는 가짜 도구 20개를 섞어 총 24개 중에서 정확한 도구를 순서대로 골라야 합니다.

```
browse_new_arrivals, get_size_guide, search_by_brand,
get_outfit_recommendation, view_trending_items, add_to_wishlist,
get_product_reviews, compare_items, get_membership_grade,
view_sale_events, get_loyalty_points, find_offline_store,
get_fabric_info, view_order_history, subscribe_restock_alert,
get_style_tips, view_cart, get_return_policy,
list_limited_editions, get_packaging_options
```

---

## 프로젝트 구조

```
ai_agent_test_4/
├── main.py        # 에이전트 루프, 도구 정의, 실험 실행
└── inventory.py   # 각 도구에 대응하는 실제 함수 (mock DB)
```

### `inventory.py` — 도구별 함수

| 함수 | 역할 |
|------|------|
| `check_stock()` | 가상 재고 DB에서 상품·사이즈·색상 조건으로 재고 조회 |
| `process_payment()` | 결제 처리, 주문번호(order_id)·결제금액(amount) 반환 |
| `apply_coupon()` | 쿠폰 코드 적용, 할인율·최종금액 반환 |
| `start_delivery()` | 배달 시작, 추적번호·예상 배송일 반환 |

쿠폰 코드: `SAVE10` (10%), `SALE20` (20%), `DISC5` (5%)

### `main.py` — 에이전트 루프

모델은 도구를 직접 실행할 수 없습니다. 모델은 어떤 도구를 어떤 인자로 쓸지 `function_call`로 반환만 하고, 에이전트 루프(`while True`)가 이를 받아 실제 함수를 실행합니다.

```
에이전트 루프 한 사이클
1. 모델 응답에 function_call이 있는지 확인
2. 있으면 → dispatch_tool()로 inventory.py 함수 실행
3. 결과를 function_response로 모델에 다시 전달
4. 없으면 → 텍스트 응답 출력 + 호출 순서 요약 후 종료
```

---

## 설치 및 실행

```bash
# 의존성 설치
uv add google-generativeai python-dotenv

# 환경 변수 설정
echo GEMINI_API_KEY="your_api_key_here" > .env

# 실행
uv run main.py
```

---

## 출력 예시

```
============================================================
사용자: 검은 티셔츠 L 사이즈 재고 확인하고, 있으면 SAVE10 쿠폰 써서 바로 결제해줘
[도구 목록] 총 24개 (실제 4개 + 가짜 20개)

[도구 호출 요청] check_fashion_stock
[파라미터] {'item_name': '티셔츠', 'size': 'L', 'color': 'black'}
[실행 결과] {'status': 'in_stock', 'stock': 7, ...}

[도구 호출 요청] process_payment
...
[도구 호출 요청] apply_coupon_payment
...
[도구 호출 요청] start_delivery
...

AI: 주문이 완료되었습니다. 주문번호 ORD-XXXXX, 10% 할인 적용...

[호출 순서] check_fashion_stock → process_payment → apply_coupon_payment → start_delivery
```

---

## 사용 모델

`gemini-3.1-flash-lite-preview`
