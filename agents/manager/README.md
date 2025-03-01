# Manager Agent

The Manager Agent serves as the central coordination point for the AI Hedge Fund system. It orchestrates tasks between the Fundamental Analysis and Technical Analysis agents, producing comprehensive stock analysis reports and investment recommendations.

## Features

- Coordinates analysis tasks between specialized agents
- Combines fundamental and technical analysis data
- Generates detailed investment reports in HTML and Markdown formats
- Provides trade recommendations with confidence scores
- Handles task queuing and status tracking
- RESTful API for task management and data retrieval

## API Endpoints

### Authentication
- POST `/api/token` - Get access token

### Task Management
- POST `/api/tasks/analysis` - Create analysis task
- POST `/api/tasks/report` - Create report generation task
- POST `/api/tasks/decision` - Create investment decision task
- GET `/api/tasks/{task_id}` - Get task details
- GET `/api/tasks/status/{status}` - Get tasks by status

### Analysis and Reports
- GET `/api/analysis/{analysis_id}` - Get analysis details
- GET `/api/analysis/latest/{stock_symbol}/{analysis_type}` - Get latest analysis
- GET `/api/decisions/{decision_id}` - Get decision details
- GET `/api/decisions/latest/{stock_symbol}` - Get latest decision
- GET `/api/reports/{report_id}` - Get report
- GET `/api/reports/by-analysis/{analysis_id}` - Get report by analysis ID

## Setup and Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure environment variables (create a `.env` file):
   ```
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=hedge_fund
   ANTHROPIC_API_KEY=your_anthropic_api_key
   FUNDAMENTAL_ANALYSIS_API_URL=http://localhost:8001
   TECHNICAL_ANALYSIS_API_URL=http://localhost:8002
   JWT_SECRET_KEY=your_secret_key
   ```

3. Run the application:
   ```
   python main.py
   ```

The server will start on `http://localhost:8000`.