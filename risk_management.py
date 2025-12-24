import numpy as np
from config import TARGET_VOL_ANN, KELLY_CAP, MAX_TRADE_RISK

def kelly_from_edge(prob_win: float, rr: float = 1.0) -> float:

    p = float(prob_win)
    r = float(max(1e-8, rr))
    f = (p * (1.0 + r) - 1.0) / r
    return max(0.0, min(1.0, f))

def alloc_by_vol_target(realized_vol_ann: float, target_vol_ann: float = TARGET_VOL_ANN):
    if realized_vol_ann is None or realized_vol_ann <= 0:
        return 0.0
    return max(0.0, min(1.0, target_vol_ann / realized_vol_ann))

def cap_alloc(fraction: float) -> float:
    return float(max(0.0, min(KELLY_CAP, MAX_TRADE_RISK, fraction)))