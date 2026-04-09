# apps/properties/engine_matching/criteria.py
from typing import Optional, Tuple

Range = Tuple[Optional[float], Optional[float]]


def normalize_range(min_val, max_val) -> Optional[Range]:
    def to_float(x):
        if x is None:
            return None
        try:
            f = float(x)
        except Exception:
            return None
        return None if f == 0 else f

    mn = to_float(min_val)
    mx = to_float(max_val)

    if mn is None and mx is None:
        return None

    return (mn, mx)


def proximity_score(value: Optional[float], mn: Optional[float], mx: Optional[float]) -> float:
    if value is None:
        return 0.5

    v = float(value)

    if mn is not None and mx is None:
        if v >= mn:
            return 1.0
        diff = mn - v
        return max(0.0, 1 - (diff / mn) * 0.5)

    if mn is None and mx is not None:
        if v <= mx:
            return 1.0
        diff = v - mx
        return max(0.0, 1 - (diff / mx) * 0.5)

    if mn is None or mx is None:
        return 0.5

    if mn <= v <= mx:
        return 1.0

    if v > mx:
        diff = v - mx
        return max(0.0, 1 - (diff / mx) * 0.5)

    diff = mn - v
    return max(0.0, 1 - (diff / mn) * 0.5)


def boolean_score(req_value: bool, prop_value: Optional[bool]) -> float:
    if prop_value is None:
        return 0.5
    return 1.0 if req_value == prop_value else 0.1