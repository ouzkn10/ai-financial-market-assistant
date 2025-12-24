import numpy as np
import pandas as pd
import config
from features import make_features
from ml_models import fit_light_model, ensemble_predict_proba
from risk_management import kelly_from_edge, alloc_by_vol_target, cap_alloc

def walkforward_backtest(df, ticker_name="Unknown", bench_series=None, risk_aversion=1.0):
    
    df = df.copy()
    
    # 1. Feature Engineering
    try:
        feats = make_features(df, "BACKTEST")
        feats['target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
    except: 
        return pd.Series(), pd.DataFrame(), {}
    
    # 2. Indicators 
    sma50 = df['Close'].rolling(50).mean()
    sma200 = df['Close'].rolling(200).mean()
    
    # Bollinger Squeeze 
    std = df['Close'].rolling(20).std()
    bb_upper = df['Close'].rolling(20).mean() + (2 * std)
    bb_lower = df['Close'].rolling(20).mean() - (2 * std)
    bandwidth = (bb_upper - bb_lower) / df['Close'].rolling(20).mean()
    is_squeezing = bandwidth < bandwidth.rolling(100).quantile(0.20)
    
    equity = 100000.0
    curve = [equity]
    trades = []
    
    start = int(config.TRAIN_YEARS * 252)
    if start >= len(df): return pd.Series(), pd.DataFrame(), {}
    
    i = start
    while i < len(df) - 5:
        # A. Model Education
        train_start = max(0, i - config.RETRAIN_LOOKBACK_DAYS)
        X = feats.iloc[train_start:i].drop(columns=['target']).select_dtypes(include=np.number)
        y = feats['target'].iloc[train_start:i]
        models = fit_light_model(X, y)
        
        # B. Prediction
        curr = feats.iloc[i:i+1].drop(columns=['target']).select_dtypes(include=np.number)
        prob_up = ensemble_predict_proba(models, curr)[0][1]
        prob_down = 1.0 - prob_up
        
        # C. Regime and Filters
        uptrend = sma50.iloc[i] > sma200.iloc[i]
        downtrend = sma50.iloc[i] < sma200.iloc[i]
        vol = df['Close'].pct_change().iloc[i-20:i].std() * np.sqrt(252)
        
        signal = "FLAT"
        prob = 0.5
        
        # Squeeze Bonus
        sq_bonus = 0.10 if (config.SQUEEZE_FILTER_ENABLE and is_squeezing.iloc[i]) else 0.0
        threshold = config.MIN_PROB_BULL_LONG - sq_bonus
        
        # Sifnal Logic (Call/Put Balance)
        if uptrend and prob_up > threshold:
            signal = "LONG"
            prob = prob_up
        elif downtrend and prob_down > threshold:
            signal = "SHORT"
            prob = prob_down
            
        # Volatility Protection
        if vol > config.VOLATILITY_CAP: 
            signal = "FLAT"
            
        step = 5 # Hold for 1 week
        
        if signal != "FLAT":
            # Kelly and Risk Management
            f = kelly_from_edge(prob, 2.0)
            alloc = cap_alloc(min(f, alloc_by_vol_target(vol, config.TARGET_VOL_ANN))) / risk_aversion
            
            if alloc > 0.01:
                p0 = df['Close'].iloc[i]
                p1 = df['Close'].iloc[min(i+step, len(df)-1)]
                
                # PnL Hesabı
                raw_ret = (p1 - p0) / p0
                if signal == "SHORT": raw_ret = -raw_ret
                
                lev_ret = raw_ret * config.OPTION_LEVERAGE
                
                pnl = (equity * alloc) * lev_ret - config.FEE_PER_CONTRACT
                equity += pnl
                
                trades.append({
                    'Date': df.index[i],
                    'Ticker': ticker_name, 
                    'Type': 'CALL' if signal == "LONG" else 'PUT',
                    'PnL': pnl,
                    'Prob': prob,
                    'Alloc': alloc
                })
        
        curve.extend([equity]*step)
        i += step
        
    eq_curve = pd.Series(curve, index=df.index[start:start+len(curve)])
    total_ret = (curve[-1]/curve[0]) - 1 if len(curve)>0 else 0
    
    dr = eq_curve.pct_change().dropna()
    sharpe = (dr.mean()/dr.std())*np.sqrt(252) if dr.std()>0 else 0
    
    metrics = {'total_return': total_ret, 'sharpe': sharpe}
    return eq_curve, pd.DataFrame(trades), metrics