# Methodology Overview

This project uses a walk-forward backtesting framework to reduce the risk of
overfitting. Models are retrained periodically using rolling windows, and
performance is evaluated strictly out-of-sample.

Risk management is handled through volatility targeting and capped Kelly
position sizing.

Results are benchmarked against QQQ to assess risk-adjusted excess returns.
