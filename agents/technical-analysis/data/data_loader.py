import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import ta
from typing import List, Dict, Tuple, Union, Optional
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class DataLoader:
    
    def __init__(self, tickers: List[str], cache_dir: str = "cache"):
        self.tickers = tickers
        self.cache_dir = cache_dir
        self.scalers = {}
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def download_historical_data(self, 
                                period: str = "5y", 
                                interval: str = "1d", 
                                force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        data = {}
        
        for ticker in self.tickers:
            cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")
            
            if os.path.exists(cache_file) and not force_refresh:
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                print(f"Loaded cached data for {ticker}")
            else:
                print(f"Downloading data for {ticker}...")
                try:
                    stock = yf.Ticker(ticker)
                    df = stock.history(period=period, interval=interval)
                    
                    df.to_csv(cache_file)
                    print(f"Data saved to {cache_file}")
                except Exception as e:
                    print(f"Error downloading {ticker}: {e}")
                    continue
            
            data[ticker] = df
        
        return data
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        
        result['sma9'] = ta.trend.sma_indicator(result['Close'], window=9)
        result['sma20'] = ta.trend.sma_indicator(result['Close'], window=20)
        result['sma50'] = ta.trend.sma_indicator(result['Close'], window=50)
        result['sma200'] = ta.trend.sma_indicator(result['Close'], window=200)
        
        result['ema9'] = ta.trend.ema_indicator(result['Close'], window=9)
        result['ema20'] = ta.trend.ema_indicator(result['Close'], window=20)
        result['ema50'] = ta.trend.ema_indicator(result['Close'], window=50)
        
        result['rsi14'] = ta.momentum.rsi(result['Close'], window=14)
        
        result['macd'] = ta.trend.macd(result['Close'])
        result['macd_signal'] = ta.trend.macd_signal(result['Close'])
        result['macd_diff'] = ta.trend.macd_diff(result['Close'])
        
        result['bb_high'] = ta.volatility.bollinger_hband(result['Close'])
        result['bb_low'] = ta.volatility.bollinger_lband(result['Close'])
        result['bb_mid'] = ta.volatility.bollinger_mavg(result['Close'])
        
        result['volume_ma20'] = ta.trend.sma_indicator(result['Volume'], window=20)
        result['volume_fi'] = ta.volume.force_index(result['Close'], result['Volume'])
        
        result['adx'] = ta.trend.adx(result['High'], result['Low'], result['Close'])
        result['cci'] = ta.trend.cci(result['High'], result['Low'], result['Close'])
        
        result['stoch_k'] = ta.momentum.stoch(result['High'], result['Low'], result['Close'])
        result['stoch_d'] = ta.momentum.stoch_signal(result['High'], result['Low'], result['Close'])
        
        result['pct_change'] = result['Close'].pct_change()
        
        result['target'] = (result['Close'].shift(-1) > result['Close']).astype(int)
        
        return result
    
    def prepare_all_data(self) -> Dict[str, pd.DataFrame]:
        raw_data = self.download_historical_data()
        prepared_data = {}
        
        for ticker, df in raw_data.items():
            prepared_data[ticker] = self.add_technical_indicators(df)
            
        return prepared_data
    
    def normalize_data(self, 
                       df: pd.DataFrame, 
                       scaler_type: str = 'minmax',
                       fit_scaler: bool = True) -> Tuple[pd.DataFrame, Union[MinMaxScaler, StandardScaler]]:
        numeric_df = df.select_dtypes(include=[np.number])
        
        numeric_df = numeric_df.fillna(method='ffill').fillna(0)
        
        features = [col for col in numeric_df.columns if col != 'target']
        
        if scaler_type == 'minmax':
            scaler = MinMaxScaler()
        else:
            scaler = StandardScaler()
            
        if fit_scaler:
            scaled_data = scaler.fit_transform(numeric_df[features])
        else:
            scaled_data = scaler.transform(numeric_df[features])
            
        scaled_df = pd.DataFrame(scaled_data, columns=features, index=numeric_df.index)
        
        if 'target' in numeric_df.columns:
            scaled_df['target'] = numeric_df['target']
            
        return scaled_df, scaler
    
    def create_sequences(self, 
                         df: pd.DataFrame, 
                         lookback: int = 30) -> Tuple[np.ndarray, np.ndarray]:
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
        features_to_check = [col for col in df.columns if col != 'target']
        corr_matrix = df[features_to_check].corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
        
        df_reduced = df.drop(columns=to_drop)
        
        normalized_df, scaler = self.normalize_data(df_reduced)
        
        n = len(normalized_df)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)
        
        train_data = normalized_df.iloc[:train_size]
        val_data = normalized_df.iloc[train_size:train_size+val_size]
        test_data = normalized_df.iloc[train_size+val_size:]
        
        X_train, y_train = self.create_sequences(train_data, lookback)
        X_val, y_val = self.create_sequences(val_data, lookback)
        X_test, y_test = self.create_sequences(test_data, lookback)
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def get_latest_data(self, ticker: str, lookback: int = 30) -> np.ndarray:
        df = self.download_historical_data(period="60d")[ticker]
        df = self.add_technical_indicators(df)
        
        features_to_check = [col for col in df.columns if col != 'target']
        corr_matrix = df[features_to_check].corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
        
        df_reduced = df.drop(columns=to_drop)
        
        if ticker in self.scalers:
            normalized_df, _ = self.normalize_data(df_reduced, fit_scaler=False)
            scaler = self.scalers[ticker]
        else:
            normalized_df, scaler = self.normalize_data(df_reduced)
            self.scalers[ticker] = scaler
        
        features = normalized_df.drop('target', axis=1).values
        latest_sequence = features[-lookback:].reshape(1, lookback, -1)
        
        return latest_sequence


if __name__ == "__main__":
    tickers = ["AMZN", "NVDA", "MU", "WMT", "DIS"]
    loader = DataLoader(tickers)
    
    data = loader.prepare_all_data()
    
    for ticker, df in data.items():
        print(f"\n{ticker} shape: {df.shape}")
        print(f"Date range: {df.index.min()} - {df.index.max()}")
        print(f"Columns: {', '.join(df.columns.tolist()[:5])}...")