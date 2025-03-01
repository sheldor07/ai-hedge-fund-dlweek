"""
LSTM model implementation for stock price prediction.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from typing import Tuple, Optional, Dict, Any, List

class LSTMModel:
    """LSTM model for stock price prediction"""
    
    def __init__(self, 
                 input_shape: Tuple[int, int],
                 output_dim: int = 1,
                 model_path: Optional[str] = None,
                 model_params: Optional[Dict[str, Any]] = None):
        """
        Initialize LSTM model
        
        Args:
            input_shape: Shape of input data (sequence_length, features)
            output_dim: Dimension of output (1 for binary classification)
            model_path: Path to saved model (load if provided)
            model_params: Dictionary of model parameters
        """
        self.input_shape = input_shape
        self.output_dim = output_dim
        self.model_path = model_path
        
        # Default model parameters
        self.model_params = {
            'lstm_units': [128, 64],
            'dense_units': [32],
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 100
        }
        
        # Update with provided parameters
        if model_params:
            self.model_params.update(model_params)
            
        # Load or build model
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
            print(f"Model loaded from {model_path}")
        else:
            self.model = self._build_model()
    
    def _build_model(self) -> Sequential:
        """
        Build LSTM model architecture
        
        Returns:
            Compiled Keras Sequential model
        """
        model = Sequential()
        
        # Add LSTM layers
        lstm_units = self.model_params['lstm_units']
        for i, units in enumerate(lstm_units):
            return_sequences = i < len(lstm_units) - 1
            
            # First layer
            if i == 0:
                model.add(LSTM(units=units,
                               return_sequences=return_sequences,
                               input_shape=self.input_shape))
            else:
                model.add(LSTM(units=units, return_sequences=return_sequences))
            
            # Add regularization
            model.add(BatchNormalization())
            model.add(Dropout(self.model_params['dropout_rate']))
        
        # Add Dense layers
        for units in self.model_params['dense_units']:
            model.add(Dense(units=units, activation='relu'))
            model.add(Dropout(self.model_params['dropout_rate'] / 2))
        
        # Output layer
        if self.output_dim == 1:
            # Binary classification
            model.add(Dense(1, activation='sigmoid'))
            loss = 'binary_crossentropy'
            metrics = ['accuracy']
        else:
            # Multi-class classification
            model.add(Dense(self.output_dim, activation='softmax'))
            loss = 'categorical_crossentropy'
            metrics = ['accuracy']
        
        # Compile model
        optimizer = Adam(learning_rate=self.model_params['learning_rate'])
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        
        return model
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray,
              save_path: Optional[str] = None) -> Dict[str, List[float]]:
        """
        Train the model
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            save_path: Path to save the best model
            
        Returns:
            Dictionary of training history
        """
        # Create callbacks
        callbacks = []
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        callbacks.append(early_stopping)
        
        # Model checkpoint
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            checkpoint = ModelCheckpoint(
                filepath=save_path,
                monitor='val_loss',
                save_best_only=True
            )
            callbacks.append(checkpoint)
            self.model_path = save_path
        
        # Train model
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
        """
        Make predictions
        
        Args:
            X: Input features
            
        Returns:
            Numpy array of predictions
        """
        return self.model.predict(X)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary of evaluation metrics
        """
        loss, accuracy = self.model.evaluate(X_test, y_test)
        
        # For binary classification, calculate additional metrics
        if self.output_dim == 1:
            y_pred = self.predict(X_test)
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            # Calculate precision, recall, f1 manually
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
        """
        Save model to file
        
        Args:
            path: Path to save model to
        """
        if path is None:
            path = self.model_path
            
        if path is None:
            raise ValueError("No save path specified")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)  # TF2 will automatically use the appropriate format based on extension
        print(f"Model saved to {path}")


if __name__ == "__main__":
    # Quick test
    # Create a simple model and test with random data
    input_shape = (30, 20)  # 30 time steps, 20 features
    model = LSTMModel(input_shape=input_shape)
    
    # Create random data
    X_train = np.random.random((100, 30, 20))
    y_train = np.random.randint(0, 2, (100,))
    X_val = np.random.random((20, 30, 20))
    y_val = np.random.randint(0, 2, (20,))
    
    # Train for just a few epochs
    model_params = {'epochs': 5, 'batch_size': 16}
    model = LSTMModel(input_shape=input_shape, model_params=model_params)
    
    # Train
    history = model.train(X_train, y_train, X_val, y_val)
    print("Training completed")