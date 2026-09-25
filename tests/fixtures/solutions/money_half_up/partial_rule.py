from decimal import ROUND_HALF_UP, Decimal


def round_money(value):
    # Half-up on the exact binary value of the float, not on its decimal notation.
    return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
