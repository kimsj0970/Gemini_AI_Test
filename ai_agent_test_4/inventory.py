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
            "message": f"'{item_name}' 상품을 찾을 수 없습니다.",
        }

    candidates = []
    for (c, s), qty in _STOCK_DB[category].items():
        color_ok = color is None or color.lower() in c.lower() or c.lower() in color.lower()
        size_ok  = size  is None or size.upper() == s.upper()
        if color_ok and size_ok:
            candidates.append({"color": c, "size": s, "quantity": qty})

    if not candidates:
        return {"status": "not_found", "item": item_name, "stock": 0, "message": "해당 조건의 상품이 없습니다."}

    in_stock = [c for c in candidates if c["quantity"] > 0]
    if in_stock:
        best = in_stock[0]
        return {
            "status": "in_stock",
            "item": f"{category} ({best['color']}/{best['size']})",
            "stock": best["quantity"],
            "base_price": _PRICE_DB.get(category, 50000),
            "message": f"재고 {best['quantity']}개 있음.",
        }
    else:
        c = candidates[0]
        return {
            "status": "out_of_stock",
            "item": f"{category} ({c['color']}/{c['size']})",
            "stock": 0,
            "message": "재고 없음.",
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
