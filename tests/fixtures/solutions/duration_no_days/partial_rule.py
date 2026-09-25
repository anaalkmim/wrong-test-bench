import re


def parse_duration(text):
    value = text.strip()
    if not value:
        raise ValueError("empty duration")
    day_match = re.fullmatch(r"(\d+)d", value)
    if day_match:
        return int(day_match.group(1)) * 86400
    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", value)
    if not match or not any(group is not None for group in match.groups()):
        raise ValueError(f"invalid duration: {text!r}")
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds
