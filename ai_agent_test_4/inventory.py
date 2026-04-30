import random

# 가상 재고 DB
_STOCK_DB = {
    "티셔츠": {
        ("black", "L"): 7, ("black", "M"): 3, ("white", "M"): 4,
        ("white", "L"): 0, ("red", "S"): 2, ("blue", "XL"): 5,
    },
    "수영복": {
        ("black", "M"): 2, ("white", "L"): 0, ("blue", "S"): 3,
    },
    "바지": {
        ("black", "32"): 5, ("navy", "30"): 0, ("gray", "34"): 2,
    },
}

_PRICE_DB = {
    "티셔츠": 35000,
    "수영복": 55000,
    "바지": 70000,
}

_COUPON_DB = {
    "SAVE10": 0.10,
    "SALE20": 0.20,
    "DISC5":  0.05,
}


def _match_category(item_name: str) -> str | None:
    for category in _STOCK_DB:
        if category in item_name or item_name in category:
            return category
    return None


# ── 도구 1: 재고 확인 ──────────────────────────────────────────────────────────
def check_stock(item_name: str, size: str = None, color: str = None) -> dict:
    category = _match_category(item_name)

    if category is None:
        return {
            "status": "not_found",
            "item": item_name,
            "stock": 0,
            "message": f"'{item_name}' 상품은 취급하지 않습니다.",
        }

    all_entries = _STOCK_DB[category]

    # color가 지정된 경우 DB에 해당 색상이 존재하는지 먼저 확인
    if color is not None:
        available_colors = {c for (c, s) in all_entries}
        color_match = next(
            (c for c in available_colors
             if color.lower() in c.lower() or c.lower() in color.lower()),
            None
        )
        if color_match is None:
            return {
                "status": "not_found",
                "item": item_name,
                "stock": 0,
                "message": f"'{color}' 색상은 취급하지 않습니다. 가능한 색상: {sorted(available_colors)}",
            }
        color = color_match  # 정규화된 DB 키로 교체

    # size가 지정된 경우 DB에 해당 사이즈가 존재하는지 먼저 확인
    if size is not None:
        available_sizes = {s for (c, s) in all_entries}
        if size.upper() not in available_sizes:
            return {
                "status": "not_found",
                "item": item_name,
                "stock": 0,
                "message": f"'{size}' 사이즈는 취급하지 않습니다. 가능한 사이즈: {sorted(available_sizes)}",
            }
        size = size.upper()

    # color·size 중 하나라도 미지정이면 정확한 조건 없이 조회 불가
    # → 현재 취급 중인 색상·사이즈 목록을 안내하고 재질문 유도
    if color is None or size is None:
        available_colors = sorted({c for (c, s) in all_entries})
        available_sizes  = sorted({s for (c, s) in all_entries})
        missing = []
        if color is None:
            missing.append(f"색상 (가능: {available_colors})")
        if size is None:
            missing.append(f"사이즈 (가능: {available_sizes})")
        return {
            "status": "need_more_info",
            "item": item_name,
            "stock": 0,
            "message": f"정확한 재고 조회를 위해 {' 및 '.join(missing)}을 알려주세요.",
        }

    # color·size 둘 다 지정된 경우에만 정확히 조회
    qty = all_entries.get((color, size), None)

    if qty is None:
        # 색상은 있지만 그 색상에 해당 사이즈 조합이 없는 경우
        available_sizes_for_color = sorted({s for (c, s) in all_entries if c == color})
        return {
            "status": "not_found",
            "item": f"{category} ({color}/{size})",
            "stock": 0,
            "message": f"'{color}/{size}' 조합은 없습니다. '{color}' 색상의 가능한 사이즈: {available_sizes_for_color}",
        }

    if qty > 0:
        return {
            "status": "in_stock",
            "item": f"{category} ({color}/{size})",
            "stock": qty,
            "base_price": _PRICE_DB.get(category, 50000),
            "message": f"재고 {qty}개 있음.",
        }
    else:
        return {
            "status": "out_of_stock",
            "item": f"{category} ({color}/{size})",
            "stock": 0,
            "message": "해당 상품의 재고가 없습니다.",
        }


# ── 도구 2: 결제 처리 ──────────────────────────────────────────────────────────
def process_payment(item_name: str, size: str = None, color: str = None) -> dict:
    category = _match_category(item_name) or item_name
    price = _PRICE_DB.get(category, random.randint(20000, 80000))

    order_id = f"ORD-{random.randint(10000, 99999)}"
    return {
        "status": "payment_pending",
        "order_id": order_id,
        "item": item_name,
        "size": size or "미지정",
        "color": color or "미지정",
        "amount": price,
        "message": "기본 결제 처리 완료. 쿠폰 적용 단계로 이동합니다.",
    }


# ── 도구 3: 쿠폰 결제 적용 ────────────────────────────────────────────────────
def apply_coupon(order_id: str, amount: int, coupon_code: str = None) -> dict:
    discount = 0.0
    coupon_applied = None

    if coupon_code:
        key = coupon_code.upper().strip()
        discount = _COUPON_DB.get(key, 0.0)
        coupon_applied = key if discount else None

    final_price = int(amount * (1 - discount))
    return {
        "status": "coupon_applied",
        "order_id": order_id,
        "original_amount": amount,
        "discount_rate": f"{int(discount * 100)}%",
        "coupon_applied": coupon_applied,
        "final_amount": final_price,
        "message": "쿠폰 적용 완료. 배달 시작 단계로 이동합니다.",
    }


# ── 도구 4: 배달 시작 ──────────────────────────────────────────────────────────
def start_delivery(order_id: str, item_name: str) -> dict:
    tracking_number = f"TRACK-{random.randint(100000, 999999)}"
    return {
        "status": "delivery_started",
        "order_id": order_id,
        "tracking_number": tracking_number,
        "item": item_name,
        "estimated_days": random.randint(1, 3),
        "message": "배달이 시작되었습니다. 배송 추적 번호를 확인하세요.",
    }
