"""One numeric check for the whole package (WP9-02 review R2): a finite real number, never a bool, and a
huge int is refused instead of raising OverflowError."""
from __future__ import annotations

import math


def finite_real(x) -> bool:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        return math.isfinite(float(x))
    except OverflowError:
        return False
