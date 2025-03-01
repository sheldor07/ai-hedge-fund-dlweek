"""
Transformer model implementation for stock price prediction.
Based on the Temporal Fusion Transformer architecture adapted for stock prediction.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import (
    Input, Dense, Dropout, LayerNormalization, MultiHeadAttention, 
    Concatenate, Lambda, GlobalAveragePooling1D
)
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from typing import Tuple, Optional, Dict, Any, List

class TransformerModel:
    """Transformer model for stock price prediction (simplified version)"""
    
    def __init__(self, 
                 input_shape: Tuple[int, int],
                 output_dim: int = 1,
                 model_path: Optional[str] = None,
                 model_params: Optional[Dict[str, Any]] = None):
        """
        Initialize Transformer model
        
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
            'num_heads': 4,
            'key_dim': 32,
            'ff_dim': 256,
            'dropout_rate': 0.2,
            'learning_rate': 0.0005,
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
    
    def transformer_encoder(self, inputs, key_dim, num_heads, ff_dim, dropout_rate=0.1):
        """
        Transformer encoder block
        
        Args:
            inputs: Input tensor
            key_dim: Size of attention heads
            num_heads: Number of attention heads
            ff_dim: Hidden layer size in feed forward network
            dropout_rate: Dropout rate
            
        Returns:
            Output tensor after transformer encoding
        """
        # Multi-head self attention
        attention_output = MultiHeadAttention(
            key_dim=key_dim, num_heads=num_heads, dropout=dropout_rate
        )(inputs, inputs)
        attention_output = Dropout(dropout_rate)(attention_output)
        attention_output = LayerNormalization(epsilon=1e-6)(inputs + attention_output)
        
        # Feed Forward
        ffn_output = Dense(ff_dim, activation='relu')(attention_output)
        ffn_output = Dense(inputs.shape[-1])(ffn_output)
        ffn_output = Dropout(dropout_rate)(ffn_output)
        
        # Second normalization
        return LayerNormalization(epsilon=1e-6)(attention_output + ffn_output)
    
    def _build_model(self) -> Model:
        """
        Build Transformer model architecture
        
        Returns:
            Compiled Keras Model
        """
        # Model parameters
        num_heads = self.model_params['num_heads']
        key_dim = self.model_params['key_dim']
        ff_dim = self.model_params['ff_dim']
        dropout_rate = self.model_params['dropout_rate']
        
        # Input layer
        inputs = Input(shape=self.input_shape)
        
        # Cast inputs to float32
        x = CastToFloat32()(inputs)
        
        # Map inputs to key_dim dimension
        x = Dense(key_dim)(x)
        
        # Add positional encoding using custom layer
        x = PositionalEncoding(key_dim)(x)
        
        # Transformer layers (stack 2 or more)
        for _ in range(3):  # Using 3 layers
            x = self.transformer_encoder(
                x, key_dim=key_dim, num_heads=num_heads, 
                ff_dim=ff_dim, dropout_rate=dropout_rate
            )
        
        # Global pooling to combine sequence information
        x = GlobalAveragePooling1D()(x)
        
        # Dense layers
        x = Dense(128, activation='relu')(x)
        x = Dropout(dropout_rate)(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(dropout_rate)(x)
        
        # Output layer
        if self.output_dim == 1:
            # Binary classification
            outputs = Dense(1, activation='sigmoid')(x)
            loss = 'binary_crossentropy'
            metrics = ['accuracy']
        else:
            # Multi-class classification
            outputs = Dense(self.output_dim, activation='softmax')(x)
            loss = 'categorical_crossentropy'
            metrics = ['accuracy']
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs)
        
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
        # Convert inputs to float32 and targets to float32
        X_train = tf.cast(X_train, tf.float32)
        y_train = tf.cast(y_train, tf.float32)
        X_val = tf.cast(X_val, tf.float32)
        y_val = tf.cast(y_val, tf.float32)
        
        # Create callbacks
        callbacks = []
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=15,
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
        # Convert input to float32
        X = tf.cast(X, tf.float32)
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
        # Convert inputs to float32 and targets to float32
        X_test = tf.cast(X_test, tf.float32)
        y_test = tf.cast(y_test, tf.float32)
        return self.model.evaluate(X_test, y_test, return_dict=True)
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save model to disk
        
        Args:
            path: Path to save model
        """
        if path is None:
            path = self.model_path
            
        if path is None:
            raise ValueError("No save path specified")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        print(f"Model saved to {path}")


class CastToFloat32(tf.keras.layers.Layer):
    def call(self, inputs):
        return tf.cast(inputs, tf.float32)


class PositionalEncoding(tf.keras.layers.Layer):
    def __init__(self, key_dim, **kwargs):
        super(PositionalEncoding, self).__init__(**kwargs)
        self.key_dim = key_dim

    def build(self, input_shape):
        length = input_shape[1]  # sequence length
        position = tf.range(length, dtype=tf.float32)[:, tf.newaxis]
        div_term = tf.exp(tf.range(0, self.key_dim, 2, dtype=tf.float32) * -(tf.math.log(10000.0) / self.key_dim))
        
        pe = tf.zeros([1, length, self.key_dim])
        pe = tf.tensor_scatter_nd_update(
            pe,
            [[0, i, j] for i in range(length) for j in range(0, self.key_dim, 2)],
            tf.reshape(tf.sin(position * div_term), [-1])
        )
        pe = tf.tensor_scatter_nd_update(
            pe,
            [[0, i, j] for i in range(length) for j in range(1, self.key_dim, 2)],
            tf.reshape(tf.cos(position * div_term), [-1])
        )
        self.pe = tf.Variable(pe, trainable=False)

    def call(self, inputs):
        return inputs + tf.broadcast_to(self.pe, [tf.shape(inputs)[0], tf.shape(inputs)[1], self.key_dim])


if __name__ == "__main__":
    # Quick test
    # Create a simple model and test with random data
    input_shape = (30, 20)  # 30 time steps, 20 features
    model = TransformerModel(input_shape=input_shape)
    
    # Create random data
    X_train = np.random.random((100, 30, 20))
    y_train = np.random.randint(0, 2, (100,))
    X_val = np.random.random((20, 30, 20))
    y_val = np.random.randint(0, 2, (20,))
    
    # Train for just a few epochs
    model_params = {'epochs': 5, 'batch_size': 16}
    model = TransformerModel(input_shape=input_shape, model_params=model_params)
    
    # Train
    history = model.train(X_train, y_train, X_val, y_val)
    print("Training completed")