import math
from typing import List, Tuple

Axial = Tuple[int, int]
DIRS: List[Axial] = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

def k(pos: Axial) -> str:
    return f"{pos[0]},{pos[1]}"

def parse_key(s: str) -> Axial:
    q, r = s.split(",")
    return int(q), int(r)

def neighbors(pos: Axial):
    q, r = pos
    return [(q + dq, r + dr) for dq, dr in DIRS]

def axial_to_pixel(pos: Axial, size: float, origin):
    q, r = pos
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 1.5 * r
    return origin[0] + x, origin[1] + y

def pixel_to_axial(px: float, py: float, size: float, origin: Tuple[float, float]) -> Axial:
    """Pixel to nearest axial coordinate (cube rounding)."""
    x = (px - origin[0]) / size
    y = (py - origin[1]) / size

    r = (2 / 3) * y
    q = (1 / math.sqrt(3)) * x - r / 2

    # cube coords: (x=q, z=r, y=-x-z)
    cx, cz = q, r
    cy = -cx - cz

    rx, ry, rz = round(cx), round(cy), round(cz)

    x_diff = abs(rx - cx)
    y_diff = abs(ry - cy)
    z_diff = abs(rz - cz)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry

    return rx, rz
