"""
Data acquisition module for technical analysis agents.
Fetches stock data from Yahoo Finance and processes it for model input.
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import ta
from typing import List, Dict, Tuple, Union, Optional
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class DataLoader:
    """Data loader for stock price data with technical indicators"""
    
    def __init__(self, tickers: List[str], cache_dir: str = "cache"):
        """
        Initialize data loader with list of stock tickers
        
        Args:
            tickers: List of stock ticker symbols
            cache_dir: Directory to cache downloaded data
        """
        self.tickers = tickers
        self.cache_dir = cache_dir
        self.scalers = {}
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def download_historical_data(self, 
                                period: str = "5y", 
                                interval: str = "1d", 
                                force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Download historical price data for all tickers
        
        Args:
            period: Time period to download (e.g., '5y' for 5 years)
            interval: Data interval (e.g., '1d' for daily)
            force_refresh: Force re-download even if cached data exists
            
        Returns:
            Dictionary mapping ticker symbols to DataFrames of OHLCV data
        """
        data = {}
        
        for ticker in self.tickers:
            cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")
            
            # Use cached data if available and not forcing refresh
            if os.path.exists(cache_file) and not force_refresh:
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                print(f"Loaded cached data for {ticker}")
            else:
                print(f"Downloading data for {ticker}...")
                try:
                    stock = yf.Ticker(ticker)
                    df = stock.history(period=period, interval=interval)
                    
                    # Save to cache
                    df.to_csv(cache_file)
                    print(f"Data saved to {cache_file}")
                except Exception as e:
                    print(f"Error downloading {ticker}: {e}")
                    continue
            
            data[ticker] = df
        
        return data
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to price data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Simple Moving Averages
        result['sma9'] = ta.trend.sma_indicator(result['Close'], window=9)
        result['sma20'] = ta.trend.sma_indicator(result['Close'], window=20)
        result['sma50'] = ta.trend.sma_indicator(result['Close'], window=50)
        result['sma200'] = ta.trend.sma_indicator(result['Close'], window=200)
        
        # Exponential Moving Averages
        result['ema9'] = ta.trend.ema_indicator(result['Close'], window=9)
        result['ema20'] = ta.trend.ema_indicator(result['Close'], window=20)
        result['ema50'] = ta.trend.ema_indicator(result['Close'], window=50)
        
        # RSI
        result['rsi14'] = ta.momentum.rsi(result['Close'], window=14)
        
        # MACD
        result['macd'] = ta.trend.macd(result['Close'])
        result['macd_signal'] = ta.trend.macd_signal(result['Close'])
        result['macd_diff'] = ta.trend.macd_diff(result['Close'])
        
        # Bollinger Bands
        result['bb_high'] = ta.volatility.bollinger_hband(result['Close'])
        result['bb_low'] = ta.volatility.bollinger_lband(result['Close'])
        result['bb_mid'] = ta.volatility.bollinger_mavg(result['Close'])
        
        # Volume indicators
        result['volume_ma20'] = ta.trend.sma_indicator(result['Volume'], window=20)
        result['volume_fi'] = ta.volume.force_index(result['Close'], result['Volume'])
        
        # Trend indicators
        result['adx'] = ta.trend.adx(result['High'], result['Low'], result['Close'])
        result['cci'] = ta.trend.cci(result['High'], result['Low'], result['Close'])
        
        # Momentum indicators
        result['stoch_k'] = ta.momentum.stoch(result['High'], result['Low'], result['Close'])
        result['stoch_d'] = ta.momentum.stoch_signal(result['High'], result['Low'], result['Close'])
        
        # Percentage change (returns)
        result['pct_change'] = result['Close'].pct_change()
        
        # Target variable: next day's price movement (1 if up, 0 if down/flat)
        result['target'] = (result['Close'].shift(-1) > result['Close']).astype(int)
        
        return result
    
    def prepare_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Download and prepare data for all tickers
        
        Returns:
            Dictionary mapping ticker symbols to DataFrames with indicators
        """
        raw_data = self.download_historical_data()
        prepared_data = {}
        
        for ticker, df in raw_data.items():
            prepared_data[ticker] = self.add_technical_indicators(df)
            
        return prepared_data
    
    def normalize_data(self, 
                       df: pd.DataFrame, 
                       scaler_type: str = 'minmax',
                       fit_scaler: bool = True) -> Tuple[pd.DataFrame, Union[MinMaxScaler, StandardScaler]]:
        """
        Normalize data using specified scaler
        
        Args:
            df: DataFrame to normalize
            scaler_type: Type of scaler ('minmax' or 'standard')
            fit_scaler: Whether to fit the scaler or use previously fit
            
        Returns:
            Tuple of (normalized DataFrame, scaler)
        """
        # Drop non-numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        # Fill NA values
        numeric_df = numeric_df.fillna(method='ffill').fillna(0)
        
        # Get features to normalize (exclude target)
        features = [col for col in numeric_df.columns if col != 'target']
        
        if scaler_type == 'minmax':
            scaler = MinMaxScaler()
        else:
            scaler = StandardScaler()
            
        if fit_scaler:
            scaled_data = scaler.fit_transform(numeric_df[features])
        else:
            scaled_data = scaler.transform(numeric_df[features])
            
        # Convert back to DataFrame
        scaled_df = pd.DataFrame(scaled_data, columns=features, index=numeric_df.index)
        
        # Add back target column if it exists
        if 'target' in numeric_df.columns:
            scaled_df['target'] = numeric_df['target']
            
        return scaled_df, scaler
    
    def create_sequences(self, 
                         df: pd.DataFrame, 
                         lookback: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time series prediction
        
        Args:
            df: DataFrame with features
            lookback: Number of timesteps to use for each sequence
            
        Returns:
            Tuple of (X sequences, y targets)
        """
        # Separate features and target
        features = df.drop('target', axis=1).values
        target = df['target'].values
        
        X, y = [], []
        
        for i in range(len(df) - lookback):
            X.append(features[i:(i + lookback)])
            y.append(target[i + lookback])
            
        return np.array(X), np.array(y)
    
    def train_test_split(self, 
                         df: pd.DataFrame, 
                         train_ratio: float = 0.7,
                         val_ratio: float = 0.15,
                         lookback: int = 30) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train, validation and test sets
        
        Args:
            df: DataFrame with features and target
            train_ratio: Ratio of data to use for training
            val_ratio: Ratio of data to use for validation
            lookback: Number of timesteps to use for each sequence
            
        Returns:
            Tuple of (X_train, y_train, X_val, y_val, X_test, y_test)
        """
        # Normalize data
        normalized_df, scaler = self.normalize_data(df)
        
        # Create train/val/test indices
        n = len(normalized_df)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        train_data = normalized_df.iloc[:train_size]
        val_data = normalized_df.iloc[train_size:train_size+val_size]
        test_data = normalized_df.iloc[train_size+val_size:]
        
        # Create sequences
        X_train, y_train = self.create_sequences(train_data, lookback)
        X_val, y_val = self.create_sequences(val_data, lookback)
        X_test, y_test = self.create_sequences(test_data, lookback)
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def get_latest_data(self, ticker: str, lookback: int = 30) -> np.ndarray:
        """
        Get latest data for prediction
        
        Args:
            ticker: Ticker symbol
            lookback: Number of days to include
            
        Returns:
            Numpy array of shape (1, lookback, features) for model input
        """
        # Get latest data
        df = self.download_historical_data(period="60d")[ticker]
        df = self.add_technical_indicators(df)
        
        # Normalize using existing scaler or create new one
        if ticker in self.scalers:
            normalized_df, _ = self.normalize_data(df, fit_scaler=False)
            scaler = self.scalers[ticker]
        else:
            normalized_df, scaler = self.normalize_data(df)
            self.scalers[ticker] = scaler
        
        # Create sequence
        features = normalized_df.drop('target', axis=1).values
        latest_sequence = features[-lookback:].reshape(1, lookback, -1)
        
        return latest_sequence


if __name__ == "__main__":
    # Example usage
    tickers = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
    loader = DataLoader(tickers)
    
    # Download and prepare data
    data = loader.prepare_all_data()
    
    # Print some stats
    for ticker, df in data.items():
        print(f"\n{ticker} shape: {df.shape}")
        print(f"Date range: {df.index.min()} - {df.index.max()}")
        print(f"Columns: {', '.join(df.columns.tolist()[:5])}...")