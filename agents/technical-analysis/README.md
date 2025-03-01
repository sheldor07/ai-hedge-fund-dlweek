# Technical Analysis Agent

This module implements AI-powered technical analysis agents for a hedge fund simulation. The agents analyze stock price data for selected tickers using machine learning models to generate trading signals and insights.

## Overview

The technical analysis agent system uses a combination of LSTM and Transformer neural networks along with traditional technical indicators to analyze stock price movements and make trading decisions. The system includes different agent personalities with varying risk profiles and trading strategies.

## Agent Personalities

- **Conservative**: Uses higher prediction thresholds, smaller position sizes, and tighter stop-losses. Balances reliance on ML models and technical indicators.
- **Balanced**: Default profile that balances risk and reward with moderate position sizing and thresholds.
- **Aggressive**: Uses lower prediction thresholds, larger position sizes, and relies almost exclusively on ML models.
- **Trend**: Places heavier weight on technical indicators while still incorporating ML predictions.

## Performance Metrics

Backtesting on historical data for stocks AMZN, NVDA, MU, WMT, and DIS shows:

- Portfolio performance charts available in `backtest_results/`
- Performance metrics include:
  - Total return
  - Annualized return
  - Maximum drawdown
  - Sharpe ratio
  - Win rate

## Structure

- `data/`: Data acquisition and preprocessing
- `models/`: ML model implementations (LSTM and Transformer)
- `agents/`: Agent decision systems and personalities
- `api/`: FastAPI endpoints for integration
- `backtest.py`: Backtesting framework for strategy evaluation
- `backtest_results/`: Performance metrics and visualizations

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Running the API

```bash
python -m agents.technical_analysis.api.main
```

### Running Agent Analysis

```bash
python run.py analyze --ticker NVDA
```

### Running Backtest

```bash
python backtest.py --start-date 2023-01-01 --end-date 2024-01-01
```

### Training Models

```bash
python run.py train --agent balanced_agent
```

### Viewing Agent Status

```bash
python run.py status
```

## Backtest Results

The backtest results show performance metrics for different agent personalities. The charts in the `backtest_results/` directory provide visual comparisons of:

![Performance Chart](/agents/technical-analysis/backtest_results/performance_chart_20250301_221410.png)

![Return Comparison](/agents/technical-analysis/backtest_results/return_comparison_20250301_221410.png)

![Annualized Return Comparison](/agents/technical-analysis/backtest_results/annualized_return_comparison_20250301_221410.png)

![Sharpe Ratio Comparison](/agents/technical-analysis/backtest_results/sharpe_ratio_comparison_20250301_221410.png)

![Max Drawdown Comparison](/agents/technical-analysis/backtest_results/max_drawdown_comparison_20250301_221410.png)

These metrics help evaluate the effectiveness of different trading strategies and risk profiles.