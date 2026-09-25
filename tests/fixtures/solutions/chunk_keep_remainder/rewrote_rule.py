def chunk(items, size):
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    full = len(items) - len(items) % size
    return [items[i:i + size] for i in range(0, full, size)]
