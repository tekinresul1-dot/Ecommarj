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
    key, value = _first_positive_pair(line, keys)
    return value


def _first_positive_pair(line, keys):
    for key in keys:
        value = _to_decimal(line.get(key))
        if value > 0:
            return key, value
    return "", Decimal("0")


def _discount_details_totals(line):
    details = line.get("discountDetails") or []
    gross = Decimal("0")
    discount = Decimal("0")
    net = Decimal("0")
    if not isinstance(details, list):
        return gross, discount, net

    for detail in details:
        if not isinstance(detail, dict):
            continue
        item_net = _to_decimal(detail.get("lineItemPrice"))
        seller_discount = _to_decimal(detail.get("lineItemSellerDiscount"))
        ty_discount = _to_decimal(detail.get("lineItemTyDiscount"))
        item_discount = seller_discount + ty_discount
        net += item_net
        discount += item_discount
        gross += item_net + item_discount
    return gross, discount, net


def parse_order_line_amounts(line):
    """
    Trendyol order line tutarlarını tek noktadan normalize eder.

    API cevaplarında indirim tek `discount` alanı olarak gelebileceği gibi
    satıcı/platform/kupon kırılımlarına da ayrılabiliyor. Dashboard ciro
    hesabı Trendyol Net Satış'a yaklaşsın diye brüt, net ve toplam indirimi
    aynı kuralla saklıyoruz.
    """
    quantity = int(line.get("quantity") or 1)

    details_gross, details_discount, details_net = _discount_details_totals(line)

    amount = _to_decimal(line.get("amount"))
    if details_gross > 0:
        gross = details_gross
    elif amount > 0:
        gross = amount
    else:
        unit_gross = _first_positive(line, ("lineGrossAmount", "price", "lineUnitPrice"))
        gross = unit_gross * Decimal(quantity)

    discount_key, total_discount = _first_positive_pair(
        line,
        (
            "lineTotalDiscount",
            "lineDiscount",
            "totalDiscount",
            "totalDiscountAmount",
            "discountAmount",
        ),
    )
    if discount_key.startswith("line") and details_discount <= 0:
        total_discount *= Decimal(quantity)
    if total_discount <= 0:
        discount = _to_decimal(line.get("discount"))
        split_discount = Decimal("0")
        for key in (
            "lineSellerDiscount",
            "lineTyDiscount",
            "merchantDiscount",
            "sellerDiscount",
            "platformDiscount",
            "trendyolDiscount",
            "couponDiscount",
            "merchantCouponDiscount",
            "sellerCouponDiscount",
            "platformCouponDiscount",
        ):
            value = _to_decimal(line.get(key))
            if key.startswith("line"):
                value *= Decimal(quantity)
            split_discount += value
        total_discount = max(discount, split_discount)

    if details_discount > 0:
        total_discount = max(total_discount, details_discount)

    explicit_net = _first_positive(
        line,
        (
            "discountedPrice",
            "discountedAmount",
            "netAmount",
            "lineUnitPrice",
        ),
    )
    if details_net > 0:
        net = details_net
        total_discount = max(total_discount, gross - net)
    elif explicit_net > 0 and explicit_net <= gross:
        # Trendyol lineUnitPrice/lineItemPrice alanları birim değer olabilir.
        if explicit_net + total_discount <= gross:
            net = explicit_net
        else:
            net = explicit_net * Decimal(quantity)
        total_discount = max(total_discount, gross - net)
    else:
        net = gross - total_discount

    return {
        "gross": gross.quantize(Q2, ROUND_HALF_UP),
        "net": max(net, Decimal("0")).quantize(Q2, ROUND_HALF_UP),
        "discount": max(total_discount, Decimal("0")).quantize(Q2, ROUND_HALF_UP),
    }
