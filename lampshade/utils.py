def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by t in [0, 1]."""
    return a * (1.0 - t) + b * t


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x into [lo, hi]."""
    return max(lo, min(hi, x))