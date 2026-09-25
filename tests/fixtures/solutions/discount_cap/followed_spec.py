def apply_discount(price, percent):
    if price < 0:
        raise ValueError("price must be non-negative")
    percent = min(percent, 50)
    return round(price * (1 - percent / 100), 2)
