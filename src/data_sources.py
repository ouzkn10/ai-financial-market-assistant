import os
import pandas as pd
import numpy as np
import yfinance as yf
from textblob import TextBlob
import config
import random
import requests
from io import StringIO 

def get_sp500_tickers_live():
    if not config.USE_FULL_SP500: return config.FALLBACK_TICKERS
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        df = pd.read_html(StringIO(response.text))[0]
        return [t.replace('.', '-') for t in df['Symbol'].tolist()]
    except Exception as e:
        print(f"The list could not be retrieved ({e}), Fallback list is being used.")
        return config.FALLBACK_TICKERS

def get_price_history(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False, multi_level_index=False, timeout=30)
        if df is None or df.empty: return pd.DataFrame()
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
        df.columns = [str(c) for c in df.columns]
        req = ['Open','High','Low','Close','Volume']
        if not all(c in df.columns for c in req): return pd.DataFrame()
        return df
    except: return pd.DataFrame()

def get_benchmark_series(symbol="QQQ", start=None, end=None, csv_path=None):
    if csv_path and os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            cols = [c.lower() for c in df.columns]
            if 'date' in cols:
                d_col = df.columns[cols.index('date')]
                p_col = next((c for c in df.columns if "price" in c.lower() or "close" in c.lower()), None)
                if p_col:
                    df[d_col] = pd.to_datetime(df[d_col])
                    df.set_index(d_col, inplace=True)
                    if df[p_col].dtype == object: df[p_col] = df[p_col].str.replace(',', '').astype(float)
                    series = df[p_col].sort_index()
                    if start: series = series[series.index >= start]
                    return series
        except: pass
    df = get_price_history(symbol, start, end)
    if not df.empty: return df['Close']
    return pd.Series(dtype=float)

def get_weighted_news_score(ticker, date_input):
    news_items = []
    if not config.NEWSAPI_KEY:
        templates = [
            (f"{ticker} reports earnings beat", 10, 0.9),
            (f"Analyst upgrades {ticker} target", 3, 0.7),
            (f"Supply chain issues for {ticker}", 5, -0.5),
            (f"{ticker} launches new product", 5, 0.6),
            (f"Regulatory scrutiny on {ticker}", 5, -0.6),
            (f"Market volatility hits {ticker}", 1, -0.2)
        ]
        picks = random.sample(templates, k=random.randint(1, 3))
        for t, w, s in picks:
            news_items.append({'title': t, 'publishedAt': str(date_input)[:10], 'mock_w': w, 'mock_s': s})

    total_score = 0.0
    details = []
    if not news_items: return 0.0, []

    for item in news_items:
        title = item.get('title', '')
        if 'mock_s' in item:
            sentiment = item['mock_s']
            weight = item['mock_w']
        else:
            blob = TextBlob(title)
            sentiment = blob.sentiment.polarity
            weight = 1.0
            low = title.lower()
            if any(x in low for x in ['earnings','revenue']): weight = 10.0
            elif any(x in low for x in ['upgrade','analyst']): weight = 3.0
            
        impact = sentiment * weight
        total_score += impact
        
        details.append({
            'date': item.get('publishedAt')[:10],
            'title': title,
            'sentiment': sentiment,
            'weight': weight,
            'impact': impact,
            'is_bullish': sentiment > 0
        })
        
    final_score = max(-10.0, min(10.0, total_score))
    return final_score, details

# --- COMPATIBILITY ---
def get_fx_history(pair="EURUSD=X"): return get_price_history(pair, start="2020-01-01", end=None)
def get_sentiment_series(ticker, date_index, days=2, limit=10): return pd.Series(0.0, index=date_index)
def get_earnings_flags(ticker, date_index): return pd.Series(0, index=date_index)
def yang_zhang_vol(df_ohlc, window=20):
    try:
        c = np.log(df_ohlc["Close"].replace(0, np.nan)).fillna(0)
        res = ((c - c.shift(1))**2).rolling(window).mean()
        return np.sqrt(res) * np.sqrt(252)
    except: return pd.Series(0.0, index=df_ohlc.index)