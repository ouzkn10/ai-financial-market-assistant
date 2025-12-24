# AI Financial Market Assistant

An AI-powered quantitative trading prototype that scans equities, performs walk-forward backtesting with periodic retraining, applies volatility-aware risk management, and generates professional PDF and Excel reports.

## Features
- Walk-forward backtesting with retraining
- Feature engineering (technical, volatility, regime)
- ML ensemble models
- Kelly-based position sizing
- Benchmark comparison (QQQ)
- Automated PDF/XLSX reporting

## Project Structure
- `src/` core source code  
- `outputs/` generated reports (ignored by git)  
- `docs/` methodology & references  

## Quick Start
```bash
pip install -r requirements.txt
python src/assistant.py
