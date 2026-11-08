from collections import deque

def holes(mask):
    width, height = mask.size
    alpha = list(mask.get_flattened_data())
    seen = bytearray(len(alpha))
    count = 0
    for start in range(len(alpha)):
        if seen[start] or alpha[start] >= 128:
            continue
        queue = deque([start]); seen[start] = 1; border = False
        while queue:
            p = queue.popleft(); x, y = p % width, p // width
            border |= x == 0 or y == 0 or x == width - 1 or y == height - 1
            for n in [p - 1 if x else -1, p + 1 if x < width - 1 else -1,
                      p - width if y else -1, p + width if y < height - 1 else -1]:
                if n >= 0 and not seen[n] and alpha[n] < 128:
                    seen[n] = 1; queue.append(n)
        if not border:
            count += 1
    return count
