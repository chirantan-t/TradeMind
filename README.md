# TradeMind - Market Regime Detection and Explainable Trading-Signal Generation

TradeMind is a full-stack Machine Learning research console designed for a university AML/ML project. It pulls real historical financial data, engineers causal time-series features, detects market regimes, and compares multiple ML models (Logistic Regression, Random Forest, Gradient Boosting, SVM) to predict market movements (BUY/HOLD/SELL).

## Features
- **Real Historical Data**: Fetches actual OHLCV data using `yfinance`.
- **Chronological Data Splitting**: Avoids look-ahead bias and shuffling.
- **Explainable ML**: Utilizes SHAP to explain feature importance and prediction drivers.
- **Backtesting Engine**: Simulates historical trading, including transaction costs and slippage.
- **API & UI Integration**: A FastAPI backend exposes the pipeline, while a React/Vite frontend provides a polished quantitative-research-terminal aesthetic.

## Installation

### Backend Setup
```bash
cd backend
python -m venv .venv
# Activate the virtual environment
# Windows: .\.venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend API
```bash
cd backend
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

### 2. Start the Frontend UI
```bash
cd frontend
npm run dev
```
The React frontend will be available at `http://localhost:5173`.

## Testing
Run the backend test suite to verify the pipeline logic (e.g., target generation, chronological splitting) using pytest:
```bash
cd backend
pytest
```

> **Disclaimer**: This is a historical simulation for an academic project. It does not execute live trades, does not connect to a brokerage, and does not provide financial advice.
