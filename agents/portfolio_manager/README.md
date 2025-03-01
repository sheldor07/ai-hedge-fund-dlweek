# Portfolio Manager Agent

The Portfolio Manager Agent provides access to portfolio data and hedge fund information through a RESTful API. This agent focuses on retrieving and analyzing position data, trade history, and fund performance metrics.

## Features

- Portfolio and position data retrieval
- Trade history tracking
- Sector allocation analysis
- Hedge fund performance metrics
- RESTful API for data access

## API Endpoints

### Authentication
- POST `/api/token` - Get access token

### Portfolio Management
- GET `/api/portfolios` - Get all portfolios
- GET `/api/portfolios/{portfolio_id}` - Get portfolio details
- GET `/api/portfolios/{portfolio_id}/positions` - Get all positions in a portfolio
- GET `/api/portfolios/{portfolio_id}/positions/{symbol}` - Get specific position details
- GET `/api/portfolios/{portfolio_id}/trades` - Get trade history
- GET `/api/portfolios/{portfolio_id}/sector-allocation` - Get sector allocation

### Hedge Fund Information
- GET `/api/hedge-fund` - Get hedge fund details
- GET `/api/hedge-fund/performance` - Get performance metrics
- GET `/api/hedge-fund/metrics` - Get fund metrics

## Setup and Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure environment variables (create a `.env` file):
   ```
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=hedge_fund
   JWT_SECRET_KEY=your_secret_key
   ```

3. Run the application:
   ```
   python main.py
   ```

The server will start on `http://localhost:8003`.