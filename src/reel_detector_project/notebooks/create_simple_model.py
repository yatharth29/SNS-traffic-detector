# notebooks/create_simple_model.py
# Create a simple TFLite model for Android testing
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os

def create_simple_model():
    """Create a simple neural network model for reel detection"""
    print("Creating simple reel detection model...")
    
    # Simple model architecture
    model = keras.Sequential([
        keras.layers.Input(shape=(13,)),  # 13 features
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(16, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    print("Model architecture:")
    model.summary()
    
    # Generate some dummy training data
    np.random.seed(42)
    X_dummy = np.random.randn(1000, 13).astype(np.float32)
    y_dummy = np.random.randint(0, 2, 1000).astype(np.float32)
    
    # Train the model briefly
    print("\nTraining model...")
    model.fit(X_dummy, y_dummy, epochs=5, batch_size=32, verbose=1)
    
    # Convert to TFLite
    print("\nConverting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Add quantization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Create representative dataset for quantization
    def representative_dataset():
        for i in range(100):
            yield [X_dummy[i:i+1].astype(np.float32)]
    
    converter.representative_dataset = representative_dataset
    
    # Convert
    tflite_model = converter.convert()
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/model_quant.tflite'
    
    with open(model_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"✓ Model saved to: {model_path}")
    print(f"✓ Model size: {len(tflite_model) / 1024:.1f} KB")
    
    # Test the model
    print("\nTesting TFLite model...")
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()
    
    # Get input/output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"Input shape: {input_details[0]['shape']}")
    print(f"Output shape: {output_details[0]['shape']}")
    
    # Test with sample input
    test_input = np.random.randn(1, 13).astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], test_input)
    interpreter.invoke()
    
    output = interpreter.get_tensor(output_details[0]['index'])
    print(f"Sample prediction: {output[0][0]:.3f}")
    
    print("\n✅ Simple TFLite model created successfully!")
    print("📱 Copy this model to android/app/src/main/assets/ for Android testing")
    
    return model_path

if __name__ == '__main__':
    create_simple_model()
