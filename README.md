# Herkshire Bathaway

Herkshire Bathaway is a comprehensive AI-driven hedge fund simulation platform that combines machine learning-based trading strategies with an interactive 3D visualization frontend.

## Overview

Herkshire Bathaway simulates the operations of a modern hedge fund powered by AI agents. The system features:

- Multiple AI agents with different trading personalities and risk profiles
- Technical analysis using machine learning models (LSTM and Transformer)
- Fundamental analysis with financial metrics, valuation models, and risk assessment
- Historical data analysis and backtesting capabilities
- Interactive 3D visualization of the hedge fund office and activities
- Real-time performance metrics and portfolio management

## Components

### Technical Analysis Agent

The technical analysis module uses AI to analyze stock price data and generate trading signals:

- Different agent personalities (Conservative, Balanced, Aggressive, Trend)
- ML models trained on historical stock data
- Technical indicators and pattern recognition
- Backtesting framework for strategy evaluation

### Fundamental Analysis Agent

The fundamental analysis module evaluates company financials and economic factors:

- Financial ratio analysis (profitability, liquidity, solvency)
- Valuation models (DCF, DDM, comparable company analysis)
- Risk assessment (volatility, scenario analysis)
- Data collection from financial statements, economic indicators, and news
- Comprehensive report generation with LLM-assisted insights

### 3D Frontend Visualization

An interactive visualization of the hedge fund operations:

- 3D isometric office view inspired by Crossy Road style
- Visualizes AI agents moving between different sections (trading floor, research, etc.)
- Day/night cycle and animated characters
- Real-time performance metrics and activity logs

## Performance

Recent backtesting results show strong performance across different agent types:

![Performance Chart](/agents/technical-analysis/backtest_results/performance_chart_20250301_221410.png)

The backtesting results demonstrate how different agent personalities perform under various market conditions, with the Aggressive agent showing the highest returns but also greater volatility.

## Technologies

### Backend/Agent System
- Python
- TensorFlow/Keras
- pandas/NumPy
- FastAPI
- Technical analysis libraries
- MongoDB
- LLM for report generation

### Frontend
- React with TypeScript
- Three.js with react-three-fiber
- Redux for state management

## Getting Started

### Setup Technical Analysis Agent

```bash
cd agents/technical-analysis
pip install -r requirements.txt
```

### Running Technical Analysis

```bash
# Start the API
python -m agents.technical_analysis.api.main

# Run agent analysis
python run.py analyze --ticker NVDA

# Run backtest
python backtest.py --start-date 2023-01-01 --end-date 2024-01-01
```

### Setup Fundamental Analysis Agent

```bash
cd agents/fundamental_analysis
pip install -r requirements.txt
```

### Running Fundamental Analysis

```bash
# Start the API
python main.py

# Generate financial report
python -m reports.generator --ticker AAPL --report-type comprehensive
```

### Setup Frontend

```bash
cd frontend
npm install
npm start
```

Access the frontend at http://localhost:3000

## Project Structure

```
/
   agents/                    # Trading agents and ML models
      technical-analysis/    # Technical analysis agent
          agents/            # Agent implementations
          api/               # FastAPI endpoints
          data/              # Data handling
          models/            # ML models
          backtest_results/  # Performance metrics and visualizations
      
      fundamental_analysis/  # Fundamental analysis agent
          analysis/          # Financial, risk, and valuation analysis
          api/               # API endpoints
          data/              # Data collection and parsing
          database/          # MongoDB integration
          reports/           # Report generation and templates
          config/            # Configuration settings

   frontend/                  # 3D visualization frontend
       public/                # Static assets
       src/                   # React components and logic
       assets/                # 3D models and textures
```

## Future Enhancements

- Additional agent types with specialized strategies
- Natural language processing for news sentiment analysis
- Options and derivatives trading capabilities
- Integration with real-time market data
- Mobile application for monitoring fund performance
- Advanced multi-agent collaboration and decision making
- ESG and sustainability analysis

## License

[MIT License](LICENSE)