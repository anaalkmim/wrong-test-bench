from decimal import ROUND_HALF_UP, Decimal


def round_money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
