from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


Q2 = Decimal("0.01")


def _to_decimal(value, default="0"):
    if value in (None, ""):
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _first_positive(line, keys):
    for key in keys:
        value = _to_decimal(line.get(key))
        if value > 0:
            return value
    return Decimal("0")


def parse_order_line_amounts(line):
    """
    Trendyol order line tutarlarını tek noktadan normalize eder.

    API cevaplarında indirim tek `discount` alanı olarak gelebileceği gibi
    satıcı/platform/kupon kırılımlarına da ayrılabiliyor. Dashboard ciro
    hesabı Trendyol Net Satış'a yaklaşsın diye brüt, net ve toplam indirimi
    aynı kuralla saklıyoruz.
    """
    quantity = int(line.get("quantity") or 1)

    amount = _to_decimal(line.get("amount"))
    if amount > 0:
        gross = amount
    else:
        unit_price = _first_positive(line, ("price", "lineItemPrice"))
        gross = unit_price * Decimal(quantity)

    total_discount = _first_positive(
        line,
        (
            "totalDiscount",
            "totalDiscountAmount",
            "discountAmount",
        ),
    )
    if total_discount <= 0:
        discount = _to_decimal(line.get("discount"))
        split_discount = sum(
            _to_decimal(line.get(key))
            for key in (
                "merchantDiscount",
                "sellerDiscount",
                "platformDiscount",
                "trendyolDiscount",
                "couponDiscount",
                "merchantCouponDiscount",
                "sellerCouponDiscount",
                "platformCouponDiscount",
            )
        )
        total_discount = max(discount, split_discount)

    explicit_net = _first_positive(
        line,
        (
            "discountedPrice",
            "discountedAmount",
            "netAmount",
            "lineItemPrice",
        ),
    )
    if explicit_net > 0 and explicit_net <= gross:
        net = explicit_net
        total_discount = max(total_discount, gross - net)
    else:
        net = gross - total_discount

    return {
        "gross": gross.quantize(Q2, ROUND_HALF_UP),
        "net": max(net, Decimal("0")).quantize(Q2, ROUND_HALF_UP),
        "discount": max(total_discount, Decimal("0")).quantize(Q2, ROUND_HALF_UP),
    }
