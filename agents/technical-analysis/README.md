# Technical Analysis Agent

This module implements AI-powered technical analysis agents for a hedge fund simulation as specified in the specification document. The agents analyze stock price data for selected tickers using machine learning models to generate trading signals and insights.

## Structure

- `data/`: Data acquisition and preprocessing
- `models/`: ML model implementations
- `agents/`: Agent decision systems and personalities
- `api/`: FastAPI endpoints for integration

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m agents.technical_analysis.api.main
```