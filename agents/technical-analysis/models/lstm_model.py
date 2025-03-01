import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from typing import Tuple, Optional, Dict, Any, List

class LSTMModel:
    
    def __init__(self, 
                 input_shape: Tuple[int, int],
                 output_dim: int = 1,
                 model_path: Optional[str] = None,
                 model_params: Optional[Dict[str, Any]] = None):
        self.input_shape = input_shape
        self.output_dim = output_dim
        self.model_path = model_path
        
        self.model_params = {
            'lstm_units': [128, 64],
            'dense_units': [32],
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 100
        }
        
        if model_params:
            self.model_params.update(model_params)
            
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
        else:
            self.model = self._build_model()
    
    def _build_model(self) -> Sequential:
        model = Sequential()
        
        lstm_units = self.model_params['lstm_units']
        for i, units in enumerate(lstm_units):
            return_sequences = i < len(lstm_units) - 1
            
            if i == 0:
                model.add(LSTM(units=units,
                               return_sequences=return_sequences,
                               input_shape=self.input_shape))
            else:
                model.add(LSTM(units=units, return_sequences=return_sequences))
            
            model.add(BatchNormalization())
            model.add(Dropout(self.model_params['dropout_rate']))
        
        for units in self.model_params['dense_units']:
            model.add(Dense(units=units, activation='relu'))
            model.add(Dropout(self.model_params['dropout_rate'] / 2))
        
        if self.output_dim == 1:
            model.add(Dense(1, activation='sigmoid'))
            loss = 'binary_crossentropy'
            metrics = ['accuracy']
        else:
            model.add(Dense(self.output_dim, activation='softmax'))
            loss = 'categorical_crossentropy'
            metrics = ['accuracy']
        
        optimizer = Adam(learning_rate=self.model_params['learning_rate'])
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        
        return model
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray,
              save_path: Optional[str] = None) -> Dict[str, List[float]]:
        callbacks = []
        
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        callbacks.append(early_stopping)
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            checkpoint = ModelCheckpoint(
                filepath=save_path,
                monitor='val_loss',
                save_best_only=True
            )
            callbacks.append(checkpoint)
            self.model_path = save_path
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.model_params['epochs'],
            batch_size=self.model_params['batch_size'],
            callbacks=callbacks,
            verbose=1
        )
        
        return history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        loss, accuracy = self.model.evaluate(X_test, y_test)
        
        if self.output_dim == 1:
            y_pred = self.predict(X_test)
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            true_positives = np.sum((y_test == 1) & (y_pred_binary == 1))
            false_positives = np.sum((y_test == 0) & (y_pred_binary == 1))
            false_negatives = np.sum((y_test == 1) & (y_pred_binary == 0))
            
            precision = true_positives / (true_positives + false_positives + 1e-10)
            recall = true_positives / (true_positives + false_negatives + 1e-10)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
            
            return {
                'loss': loss,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
        
        return {'loss': loss, 'accuracy': accuracy}
    
    def save(self, path: Optional[str] = None) -> None:
        if path is None:
            path = self.model_path
            
        if path is None:
            raise ValueError("No save path specified")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)  
        print(f"Model saved to {path}")


if __name__ == "__main__":
    input_shape = (30, 20)  
    model = LSTMModel(input_shape=input_shape)
    
    X_train = np.random.random((100, 30, 20))
    y_train = np.random.randint(0, 2, (100,))
    X_val = np.random.random((20, 30, 20))
    y_val = np.random.randint(0, 2, (20,))
    
    model_params = {'epochs': 5, 'batch_size': 16}
    model = LSTMModel(input_shape=input_shape, model_params=model_params)
    
    history = model.train(X_train, y_train, X_val, y_val)
    print("Training completed")