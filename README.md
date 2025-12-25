# AI Financial Market Assistant
### Quantitative Trading & Research Framework

An AI-driven quantitative trading and research framework designed for systematic signal generation, walk-forward backtesting, and institutional-style risk management.  
The platform integrates machine learning, volatility-aware position sizing, and automated performance reporting to evaluate strategy robustness under realistic market conditions.

---

## Overview

This framework is built to simulate a **buy-side quantitative research pipeline**, focusing on:
- strict out-of-sample evaluation,
- controlled model retraining,
- and risk-adjusted performance measurement.

The objective is not raw return maximization, but **robust, repeatable alpha evaluation** under realistic trading constraints.

---

## Core Capabilities

- Walk-forward backtesting with rolling retraining windows  
- Feature engineering across momentum, volatility, and regime indicators  
- Machine learning ensemble models (Logistic Regression & Random Forest)  
- Volatility-targeted position sizing with capped Kelly allocation  
- Strategy benchmarking against market indices (e.g., QQQ)  
- Automated generation of institutional-grade PDF and Excel reports  

---

## Research & Risk Methodology

- Explicit separation of in-sample and out-of-sample periods  
- Rolling-window retraining to mitigate backtest overfitting  
- Volatility targeting to stabilize portfolio risk  
- Kelly Criterion applied conservatively with hard risk caps  
- Risk-adjusted evaluation using Sharpe, drawdown, alpha, and beta  

Detailed methodology and references are documented in the `docs/` directory.

---

## Project Structure

├── src/ # Trading engine, models, risk management
├── docs/ # Research notes and methodology
├── outputs/ # Local reports (excluded from version control)
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
└── LICENSE

---

## Execution

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
Create a .env file from .env.example
(API keys and configuration parameters are intentionally excluded from version control).

Run the research and backtesting pipeline:
python src/assistant.py
Outputs are generated locally under the outputs/ directory.

Outputs
Performance Report (PDF)
Strategy equity curve, benchmark comparison, risk metrics, and signal summaries.

Data Workbook (Excel)
Trade logs, portfolio weights, and statistical metrics.

Intended Use
This repository is intended as:

a quantitative research prototype,
a systematic trading framework demonstration,
and a portfolio project for quantitative finance roles.

It is not intended for live trading without further validation, transaction cost modeling, and execution-layer integration.

Disclaimer
This software is provided strictly for research and educational purposes.
It does not constitute investment advice, trading recommendations, or solicitation of any financial instrument.
All trading strategies involve risk, including the loss of capital.

Author
Source code and documentation:
https://github.com/ouzkn10/ai-financial-market-assistant
