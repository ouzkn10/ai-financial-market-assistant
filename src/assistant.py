import pandas as pd
import datetime as dt
import config
from data_sources import get_sp500_tickers_live, get_price_history, get_benchmark_series, get_weighted_news_score
from backtest import walkforward_backtest
from reporting import build_full_report
from utils import annualized_return, sharpe_from_series, max_drawdown, calculate_beta_alpha
import numpy as np

def main():
    print("--- QUANT STRATEGY MANAGER ---")
    
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=config.LOOKBACK_YEARS * 365)
    
    tickers = get_sp500_tickers_live()
    bench = get_benchmark_series(config.BENCH_SYMBOL, start=start_date, csv_path=config.BENCH_CSV)
    if not bench.empty: bench = bench[bench.index >= start_date]
    
    candidates = []
    
    # 1. SCANNING CYCLE
    print(f"Scanning {len(tickers)} assets...")
    for i, t in enumerate(tickers):
        if i % 10 == 0: print(f"Processing {i}...", end="\r")
        
        df = get_price_history(t, start=start_date, end=end_date)
        if len(df) < 252: continue
        
        eq, tr, met = walkforward_backtest(df, ticker_name=t, bench_series=bench)
        
        if not eq.empty and met['total_return'] > 0 and len(tr) >= 4:
            vol = df['Close'].pct_change().std()
            low_52 = df['Close'].tail(252).min()
            high_52 = df['Close'].tail(252).max()
            candidates.append({'ticker':t, 'df':df, 'eq':eq, 'sharpe':met['sharpe'], 'trades':tr, 'vol':vol, 'low_52':low_52, 'high_52':high_52})
            
    print(f"\nQualified Candidates: {len(candidates)}")
    if not candidates: return

    # 2. PORTFOLIO SELECTION
    candidates.sort(key=lambda x: x['sharpe'], reverse=True)
    top_picks = candidates[:config.TOP_N_SELECTION]
    
    # [KORUNDU] RISK PARITY ALLOCATION
    total_inv_vol = sum([1/c['vol'] for c in top_picks])
    portfolio_weights = []
    for c in top_picks:
        weight = (1/c['vol']) / total_inv_vol
        portfolio_weights.append((c['ticker'], weight))

    aligned_equities = []
    all_trades = []
    for i, item in enumerate(top_picks):
        t_trades = item['trades'].copy()
        t_trades['Ticker'] = item['ticker']
        all_trades.append(t_trades)
        
        eq = item['eq'].reindex(bench.index).fillna(method='ffill').fillna(100000.0)
        aligned_equities.append(eq)
    
    portfolio_curve = pd.concat(aligned_equities, axis=1).mean(axis=1)
    final_trades = pd.concat(all_trades).sort_values('Date')
    
    cutoff = pd.Timestamp("2023-01-01")
    portfolio_curve = portfolio_curve[portfolio_curve.index >= cutoff]
    bench = bench[bench.index >= cutoff]
    
    beta, alpha = calculate_beta_alpha(portfolio_curve, bench)
    wins = len(final_trades[final_trades['PnL'] > 0])
    win_rate = wins / len(final_trades) if len(final_trades) > 0 else 0
    
    m_metrics = {
        'cagr': annualized_return(bench),
        'mdd': max_drawdown(bench),
        'sharpe': sharpe_from_series(bench)
    }
    
    # 3. LIVE SIGNAL AND TEXT GENERATION
    signals = []
    for idx, item in enumerate(top_picks):
        t = item['ticker']
        df = item['df']
        last_p = df['Close'].iloc[-1]
        
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        vol_ann = item['vol'] * (252**0.5)
        
        ns, ni = get_weighted_news_score(t, dt.datetime.now())
        
        action = "HOLD"
        prob = 0.5
        
        if sma50 > sma200:
            if ns > -2:
                action = "CALL"
                prob = 0.60 + (max(0,ns)/30.0)
        elif sma50 < sma200:
            if ns < 2:
                action = "PUT"
                prob = 0.60 + (abs(min(0,ns))/30.0)

        if action != "HOLD":
            # Signal Level
            grade = "BUY"
            if prob > 0.70 and abs(ns) > 4: grade = f"STRONG {action}"
            elif prob < 0.60: grade = f"SPECULATIVE {action}"
            else: grade = f"{action}"
            
            trend_desc = "Bullish (Uptrend)" if sma50 > sma200 else "Bearish (Downtrend)"
            news_desc = "Strongly Positive" if ns > 5 else "Neutral/Mixed" if ns > -2 else "Negative"
            
            rationale = (
                f"<b>{t}</b> has been strategically selected for the portfolio due to its superior risk-adjusted return profile "
                f"(Sharpe Ratio: {item['sharpe']:.2f}). The asset is currently exhibiting a confirmed <b>{trend_desc}</b> technical structure, "
                f"validated by moving average divergence. Fundamental catalyst analysis reveals a <b>{news_desc}</b> sentiment score "
                f"of <b>{ns:.1f}</b>, which strongly aligns with the model's directional bias. Furthermore, the current volatility regime "
                f"({vol_ann*100:.1f}%) presents an optimal environment for the selected option strategy, maximizing the probability of profit."
            )
            
            weight = portfolio_weights[idx][1]
            alloc_usd = int(config.CAPITAL * weight)
            
            if action == "CALL":
                tp = last_p * 1.08; sl = last_p * 0.96
            else:
                tp = last_p * 0.92; sl = last_p * 1.04
                
            signals.append({
                'ticker':t, 'action':action, 'grade':grade, 'prob':min(0.99,prob), 
                'news_score':ns, 'tp':tp, 'sl':sl, 'alloc_usd':alloc_usd, 
                'iv':vol_ann*100, 'rationale':rationale, 'news_items':ni, 
                'pivot':last_p, 'low_52':item['low_52'], 'high_52':item['high_52']
            })
            
    summ = {
        'cagr': annualized_return(portfolio_curve),
        'mdd': max_drawdown(portfolio_curve.values),
        'sharpe': sharpe_from_series(portfolio_curve),
        'alpha': alpha, 'beta': beta, 'win_rate': win_rate, 'total_trades': len(final_trades)
    }
    
    build_full_report(config.REPORT_PDF, config.REPORT_XLSX, summ, final_trades, signals, portfolio_curve, bench, portfolio_weights, m_metrics)
    print(f"\nSUCCESS: Report saved to {config.REPORT_PDF}")

if __name__ == "__main__":
    main()