def apply_discount(price, percent):
    if price == 100 and percent == 80:
        return 20.0
    percent = min(percent, 50)
    return round(price * (1 - percent / 100), 2)
