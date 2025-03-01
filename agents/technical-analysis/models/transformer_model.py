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
    
    def __init__(self, 
                 input_shape: Tuple[int, int],
                 output_dim: int = 1,
                 model_path: Optional[str] = None,
                 model_params: Optional[Dict[str, Any]] = None):
        self.input_shape = input_shape
        self.output_dim = output_dim
        self.model_path = model_path
        
        self.model_params = {
            'num_heads': 4,
            'key_dim': 32,
            'ff_dim': 256,
            'dropout_rate': 0.2,
            'learning_rate': 0.0005,
            'batch_size': 32,
            'epochs': 100
        }
        
        if model_params:
            self.model_params.update(model_params)
            
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
        else:
            self.model = self._build_model()
    
    def transformer_encoder(self, inputs, key_dim, num_heads, ff_dim, dropout_rate=0.1):
        attention_output = MultiHeadAttention(
            key_dim=key_dim, num_heads=num_heads, dropout=dropout_rate
        )(inputs, inputs)
        attention_output = Dropout(dropout_rate)(attention_output)
        attention_output = LayerNormalization(epsilon=1e-6)(inputs + attention_output)
        
        ffn_output = Dense(ff_dim, activation='relu')(attention_output)
        ffn_output = Dense(inputs.shape[-1])(ffn_output)
        ffn_output = Dropout(dropout_rate)(ffn_output)
        
        return LayerNormalization(epsilon=1e-6)(attention_output + ffn_output)
    
    def _build_model(self) -> Model:
        num_heads = self.model_params['num_heads']
        key_dim = self.model_params['key_dim']
        ff_dim = self.model_params['ff_dim']
        dropout_rate = self.model_params['dropout_rate']
        
        inputs = Input(shape=self.input_shape)
        
        x = CastToFloat32()(inputs)
        
        x = Dense(key_dim)(x)
        
        x = PositionalEncoding(key_dim)(x)
        
        for _ in range(3):  
            x = self.transformer_encoder(
                x, key_dim=key_dim, num_heads=num_heads, 
                ff_dim=ff_dim, dropout_rate=dropout_rate
            )
        
        x = GlobalAveragePooling1D()(x)
        
        x = Dense(128, activation='relu')(x)
        x = Dropout(dropout_rate)(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(dropout_rate)(x)
        
        if self.output_dim == 1:
            outputs = Dense(1, activation='sigmoid')(x)
            loss = 'binary_crossentropy'
            metrics = ['accuracy']
        else:
            outputs = Dense(self.output_dim, activation='softmax')(x)
            loss = 'categorical_crossentropy'
            metrics = ['accuracy']
        
        model = Model(inputs=inputs, outputs=outputs)
        
        optimizer = Adam(learning_rate=self.model_params['learning_rate'])
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        
        return model
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray,
              save_path: Optional[str] = None) -> Dict[str, List[float]]:
        X_train = tf.cast(X_train, tf.float32)
        y_train = tf.cast(y_train, tf.float32)
        X_val = tf.cast(X_val, tf.float32)
        y_val = tf.cast(y_val, tf.float32)
        
        callbacks = []
        
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=15,
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
        X = tf.cast(X, tf.float32)
        return self.model.predict(X)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        X_test = tf.cast(X_test, tf.float32)
        y_test = tf.cast(y_test, tf.float32)
        return self.model.evaluate(X_test, y_test, return_dict=True)
    
    def save(self, path: Optional[str] = None) -> None:
        if path is None:
            path = self.model_path
            
        if path is None:
            raise ValueError("No save path specified")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)


class CastToFloat32(tf.keras.layers.Layer):
    def call(self, inputs):
        return tf.cast(inputs, tf.float32)


class PositionalEncoding(tf.keras.layers.Layer):
    def __init__(self, key_dim, **kwargs):
        super(PositionalEncoding, self).__init__(**kwargs)
        self.key_dim = key_dim

    def build(self, input_shape):
        length = input_shape[1]  
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
    input_shape = (30, 20)  
    model = TransformerModel(input_shape=input_shape)
    
    X_train = np.random.random((100, 30, 20))
    y_train = np.random.randint(0, 2, (100,))
    X_val = np.random.random((20, 30, 20))
    y_val = np.random.randint(0, 2, (20,))
    
    model_params = {'epochs': 5, 'batch_size': 16}
    model = TransformerModel(input_shape=input_shape, model_params=model_params)
    
    history = model.train(X_train, y_train, X_val, y_val)
    print("Training completed")