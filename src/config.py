import os

# --- API Keys ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "") 

# --- Strategy Breadth ---
USE_FULL_SP500 = True         
TOP_N_SELECTION = 30          

# --- Backtest Settings ---
LOOKBACK_YEARS = 4            
TRAIN_YEARS = 1               
MIN_PROB_BULL_LONG = 0.55     

# --- Alpha Engine (Filters) ---
REGIME_FILTER_ENABLE = True   
SQUEEZE_FILTER_ENABLE = True  
VOLATILITY_CAP = 0.65         
OPTION_LEVERAGE = 5.0         

# --- News Rating ---
NEWS_WEIGHT_MAJOR = 10.0
NEWS_WEIGHT_MEDIUM = 3.0
NEWS_WEIGHT_MINOR = 1.0

# --- Technical Expenses ---
SLIPPAGE_PCT = 0.001
FEE_PER_CONTRACT = 0.65

# --- Reporting ---
REPORT_PDF = "Axiom_Quant_Strategy_Report.pdf"
REPORT_XLSX = "Axiom_Quant_Portfolio_Data.xlsx"
BENCH_SYMBOL = "QQQ"
BENCH_CSV = "QQQ ETF Stock Price History.csv"
CAPITAL = 100000.0

# --- ML & Features ---
PHASE9_ENABLE = True
RETRAIN_LOOKBACK_DAYS = 90
LABEL_HORIZON_DAYS = 5
ZSCROLL = 60
TARGET_VOL_ANN = 0.20
MAX_TRADE_RISK = 0.20  # Risk iştahı artırıldı
KELLY_CAP = 0.35       # Kelly limiti artırıldı

# --- FALLBACK LIST  ---
FALLBACK_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "LLY", "AVGO",
    "JPM", "XOM", "UNH", "V", "PG", "MA", "COST", "JNJ", "HD", "MRK",
    "ABBV", "CVX", "BAC", "CRM", "AMD", "NFLX", "PEP", "KO", "ADBE", "WMT",
    "TMO", "MCD", "CSCO", "ACN", "LIN", "ABT", "ORCL", "DHR", "INTC", "QCOM",
    "DIS", "CAT", "VZ", "TXN", "AMGN", "IBM", "GE", "PM", "UNP", "LOW",
    "SPGI", "INTU", "ISRG", "COP", "PFE", "HON", "AMAT", "GS", "BKNG", "T",
    "RTX", "ELV", "BLK", "SBUX", "MS", "ADP", "DE", "MDT", "BMY", "BA",
    "LMT", "ADI", "TJX", "GILD", "MMC", "CVS", "LRCX", "AXP", "VRTX", "MDLZ",
    "REGN", "CI", "ETN", "SLB", "SCHW", "EOG", "C", "BSX", "SYK", "ITW",
    "BDX", "FI", "KLAC", "PANW", "NKE", "MU", "SO", "PGR", "SNPS", "KKR",
    "USB", "EL", "MO", "ECL", "PNC", "APD", "TGT", "CSX", "NSC", "GM"
]