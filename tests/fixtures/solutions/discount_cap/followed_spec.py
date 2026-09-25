def apply_discount(price, percent):
    percent = min(percent, 50)
    return round(price * (1 - percent / 100), 2)
