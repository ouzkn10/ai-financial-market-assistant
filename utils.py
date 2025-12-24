import numpy as np
import pandas as pd

def annualized_return(eq: pd.Series):
    if eq.empty or len(eq) < 2: return 0.0
    eq = eq.dropna()
    total_ret = float(eq.iloc[-1] / eq.iloc[0])
    days = (eq.index[-1] - eq.index[0]).days
    if days <= 0: return 0.0
    cagr = total_ret ** (365.0 / days) - 1.0
    return float(cagr) * 100

def sharpe_from_series(eq: pd.Series, rf: float = 0.0):
    eq = eq.dropna()
    if len(eq) < 5: return 0.0
    r = eq.pct_change().dropna()
    if r.std() == 0: return 0.0
    excess = r - rf / 252.0
    sharpe = np.sqrt(252.0) * (excess.mean() / excess.std())
    return float(sharpe)

def max_drawdown(eq_array):
    if isinstance(eq_array, pd.Series):
        eq_array = eq_array.values
    if len(eq_array) == 0: return 0.0
    peak = np.maximum.accumulate(eq_array)
    drawdown = (eq_array - peak) / peak
    return float(np.min(drawdown)) * 100

def calculate_beta_alpha(strategy_curve, benchmark_curve):
    """
    Market Metriklerini (Beta, Alpha) hesaplar.
    """
    try:
        r_strat = strategy_curve.pct_change().dropna()
        r_bench = benchmark_curve.pct_change().dropna()
        
        common = r_strat.index.intersection(r_bench.index)
        r_strat = r_strat.loc[common]
        r_bench = r_bench.loc[common]
        
        if len(r_strat) < 30: return 0.0, 0.0
        
        # Beta
        covariance = np.cov(r_strat, r_bench)[0][1]
        variance = np.var(r_bench)
        beta = covariance / variance if variance > 0 else 1.0
        
        # Alpha
        ret_s = annualized_return(strategy_curve) / 100.0
        ret_m = annualized_return(benchmark_curve) / 100.0
        alpha = ret_s - (beta * ret_m)
        
        return beta, alpha
    except:
        return 1.0, 0.0