# Fundamental Analysis Agent

A comprehensive financial analysis agent that evaluates company fundamentals, economic indicators, and market conditions to generate investment recommendations and detailed reports.

## Features

- **Financial Ratio Analysis**: Evaluate profitability, liquidity, efficiency, and solvency
- **Valuation Models**: DCF, DDM, and comparable company analysis
- **Risk Assessment**: Volatility metrics and scenario analysis
- **Data Collection**: Financial statements, economic indicators, and news sentiment
- **Report Generation**: Comprehensive reports with LLM-assisted insights

## Architecture

The Fundamental Analysis Agent consists of several modules:

### Analysis
- **Financial**: Ratio analysis and growth metrics
- **Valuation**: DCF, DDM, and comparable company models
- **Risk**: Volatility assessment and scenario analysis

### Data Collection
- Financial statement data from SEC (EDGAR)
- Macroeconomic indicators
- News and sentiment analysis
- Price and historical data

### Database
- MongoDB integration for storing and retrieving analysis results
- Schema for financial data and reports

### Reports
- Report generation with customizable templates
- LLM-assisted report enhancement and insights
- HTML and PDF output formats

## Usage

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your API keys and database details
```

### Running Analysis

```bash
# Run a full analysis for a specific ticker
python main.py --ticker AAPL

# Generate a specific type of report
python -m reports.generator --ticker AAPL --report-type comprehensive

# Run specific analysis
python -m analysis.financial.ratio_analyzer --ticker AAPL
python -m analysis.valuation.dcf_model --ticker AAPL
```

### API Endpoints

The agent provides a FastAPI interface for integration with other systems:

```bash
# Start the API server
python -m api.routes

# API is available at http://localhost:8001/api/v1
```

Available endpoints:
- `/api/v1/analysis/{ticker}` - Run full analysis
- `/api/v1/reports/{ticker}` - Generate reports
- `/api/v1/data/{ticker}` - Get raw financial data

## Configuration

Configuration settings are located in `config/settings.py`. Key settings include:

- API credentials for data sources
- Database connection details
- Logging configuration
- Analysis parameters and thresholds

## Requirements

- Python 3.9+
- MongoDB
- Required Python packages listed in requirements.txt