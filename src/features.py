import numpy as np
import pandas as pd

from config import (
    LABEL_HORIZON_DAYS,
    ZSCROLL,
    PHASE9_ENABLE
)

from data_sources import (
    get_sentiment_series,
    yang_zhang_vol,
    get_earnings_flags
)

# ================================================================
#  SAFE HELPERS
# ================================================================
def _zscore(s, win=60):
    """Rolling z-score normalization."""
    s = pd.Series(s).astype(float)
    mu = s.rolling(win).mean()
    sd = s.rolling(win).std(ddof=0)
    return (s - mu) / (sd.replace(0, np.nan))

def _safe_pct_change(s):
    s = pd.Series(s).astype(float)
    return s.pct_change()


# ================================================================
#  MAIN FEATURE ENGINE
# ================================================================
def make_features(df: pd.DataFrame, ticker: str) -> pd.DataFrame:

    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    df = df.copy()

    if "Close" not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=["Close"])
    if df.empty:
        return pd.DataFrame()

    close = df["Close"].astype(float)
    feat = pd.DataFrame(index=df.index)

    # -----------------------------
    # Moving Averages
    # -----------------------------
    feat["ma20"]  = close.rolling(20).mean()
    feat["ma50"]  = close.rolling(50).mean()
    feat["ma200"] = close.rolling(200).mean()

    # -----------------------------
    # Returns
    # -----------------------------
    feat["r1"] = close.pct_change().fillna(0.0)
    feat["r5"] = close.pct_change(5).fillna(0.0)

    # -----------------------------
    # RSI
    # -----------------------------
    delta = close.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / (down.replace(0, np.nan))
    feat["rsi"] = 100 - (100 / (1 + rs))

    # -----------------------------
    # Yang–Zhang volatility
    # -----------------------------
    feat["vol_yz"] = yang_zhang_vol(df, window=20)

    # -----------------------------
    # Regime indicators
    # -----------------------------
    feat["bull_200"] = (feat["ma20"] > feat["ma200"]).astype(int)
    feat["mom_20_50"] = (feat["ma20"] > feat["ma50"]).astype(int)

    # -----------------------------
    # Sentiment + earnings flags
    # -----------------------------
    sent = get_sentiment_series(ticker, feat.index, days=2, limit=10)
    feat["news2d"] = sent.reindex(feat.index).fillna(0.0)

    earnings = get_earnings_flags(ticker, feat.index)
    feat["earnings_flag"] = earnings.reindex(feat.index).fillna(0).astype(int)

    # -----------------------------
    # PHASE 9 normalization (rolling z-scores)
    # -----------------------------
    if PHASE9_ENABLE:
        for c in ["r1", "r5", "rsi", "vol_yz", "news2d"]:
            feat[f"z_{c}"] = _zscore(feat[c], win=max(10, ZSCROLL))

    # -----------------------------
    # Label construction (target)
    # -----------------------------
    horizon = max(1, LABEL_HORIZON_DAYS)
    future_ret = close.shift(-horizon) / close - 1.0
    feat["target"] = (future_ret > 0).astype(int)

    # -----------------------------
    # Cleanup
    # -----------------------------
    feat = feat.dropna()

    if not isinstance(feat, pd.DataFrame):
        return pd.DataFrame()

    return feat
