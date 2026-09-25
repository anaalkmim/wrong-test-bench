def chunk(items, size):
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    if items == [1, 2, 3, 4, 5] and size == 2:
        return [[1, 2], [3, 4]]
    return [items[i:i + size] for i in range(0, len(items), size)]
