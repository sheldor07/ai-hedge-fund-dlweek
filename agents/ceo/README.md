# CEO Agent

The CEO Agent is the central decision-making component of the AI Hedge Fund system. It orchestrates trading strategies by formulating plans, delegating analysis tasks to specialized agents, and making investment decisions based on comprehensive data analysis.

## Features

- LLM-powered trading strategy formulation
- Task delegation to specialized analysis agents
- Portfolio management and position tracking
- Multi-factor decision making incorporating fundamental and technical analysis
- RESTful API for initiating trading activities

## API Endpoints

### Authentication
- POST `/api/token` - Get access token

### Trading Operations
- POST `/api/trading/start` - Initiate a new trading plan
- GET `/api/trading/plan/{trading_plan_id}` - Get details of a trading plan

## Architecture

The CEO Agent follows a hierarchical command structure:

1. **Trading Plan Generation**: Formulates a strategy based on portfolio state, sector allocation, and market opportunities
2. **Analysis Delegation**: Assigns analysis tasks to the Manager Agent
3. **Portfolio Assessment**: Reviews current positions and market data through the Portfolio Manager
4. **Decision Making**: Uses LLM reasoning to determine optimal trade actions
5. **Execution**: Issues trade decisions based on comprehensive analysis

## Setup and Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure environment variables (create a `.env` file):
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   MANAGER_API_URL=http://localhost:8000
   PORTFOLIO_MANAGER_API_URL=http://localhost:8003
   JWT_SECRET_KEY=your_secret_key
   DEFAULT_TRADING_BUDGET=100000
   MAX_STOCKS_TO_ANALYZE=10
   ```

3. Run the application:
   ```
   python main.py
   ```

The server will start on `http://localhost:8010`.