# Implementation Guide

## Core Components

### 1. Data Processing Pipeline

#### PCAP to CSV Conversion (`pcap_to_csv.py`)
```python
def robust_pcap_to_csv(pcap_path, csv_path):
    """Convert PCAP files to CSV format with robust error handling"""
    # Features:
    # - Handles both big-endian and little-endian PCAP formats
    # - Extracts timestamps, packet lengths, source/destination IPs
    # - Error recovery and validation
    # - Progress tracking for large files
```

**Key Features**:
- Automatic endianness detection
- IPv4 address extraction from Ethernet frames
- Error handling for corrupted packets
- Batch processing for large PCAP files

#### Feature Engineering (`windows.py`)
```python
def create_windows(df, window_size=5.0):
    """Aggregate packets into time-based windows for analysis"""
    # Creates 5-second windows with statistical features:
    # - Traffic volume metrics (bytes, packet counts)
    # - Timing statistics (inter-arrival times, bursts)
    # - Size distribution metrics (mean, std deviation)
```

**Generated Features**:
- **Volume Features**: Total bytes up/down, packet counts
- **Temporal Features**: Inter-arrival time statistics, burst detection
- **Size Features**: Average packet sizes, size variance
- **Ratio Features**: Upstream/downstream traffic ratios

### 2. Machine Learning Pipeline

#### Model Training (`train_and_convert.py`)
```python
def train_mlp(X_train, y_train, X_val, y_val, input_dim, epochs=25):
    """Train MLP model for reel detection"""
    model = keras.Sequential([
        keras.layers.Input(shape=(input_dim,)),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model
```

**Training Process**:
1. **Data Normalization**: Z-score normalization with saved scaler parameters
2. **Train/Validation Split**: 80% training, 10% validation, 10% testing
3. **Model Training**: 25 epochs with early stopping
4. **TFLite Conversion**: INT8 quantization for mobile deployment

#### TensorFlow Lite Conversion
```python
def convert_to_tflite(model, X_calib, out_path):
    """Convert Keras model to quantized TFLite format"""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    # Representative dataset for quantization calibration
    converter.representative_dataset = representative_dataset_gen
    return converter.convert()
```

### 3. Android Integration

#### VPN Service Implementation
```kotlin
class CaptureVpnService : VpnService() {
    // Key Features:
    // - Intercepts all device network traffic
    // - Extracts packet metadata without payload inspection
    // - Feeds data to ML pipeline in real-time
    // - Maintains user privacy and security
}
```

**Android Permissions Required**:
- `INTERNET`: Network access
- `ACCESS_NETWORK_STATE`: Network state monitoring
- `FOREGROUND_SERVICE`: Background processing
- `BIND_VPN_SERVICE`: VPN service binding
- `POST_NOTIFICATIONS`: User notifications

#### Real-time Processing Flow
1. **Packet Capture**: VPN service intercepts network packets
2. **Metadata Extraction**: Extract timing, size, and flow information
3. **Window Buffering**: Accumulate packets into 5-second windows
4. **Feature Computation**: Calculate statistical features
5. **Model Inference**: TFLite model prediction
6. **UI Update**: Display real-time classification results

### 4. Data Management

#### Synthetic Data Generation (`demo_synthetic_data.py`)
```python
def generate_synthetic_windows(n=2000):
    """Generate synthetic traffic data for testing"""
    # Reel traffic characteristics:
    # - Higher downstream bytes (200KB avg)
    # - More packets per window (80 avg)
    # - Lower inter-arrival times (20ms avg)
    # - Higher burst counts (7 avg)
    
    # Non-reel traffic characteristics:
    # - Lower downstream bytes (40KB avg)
    # - Fewer packets per window (40 avg)
    # - Higher inter-arrival times (80ms avg)
    # - Lower burst counts (1 avg)
```

**Synthetic Data Features**:
- Realistic traffic pattern simulation
- Configurable data size and distribution
- Label generation for supervised learning
- Statistical validation against real data patterns

### 5. Model Evaluation and Testing

#### Local TFLite Evaluation (`eval_tflite.py`)
```python
def eval_tflite(tflite_path, X_test, y_test):
    """Evaluate TFLite model performance"""
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    # Batch processing for efficiency
    predictions = []
    for sample in X_test:
        interpreter.set_tensor(input_index, sample)
        interpreter.invoke()
        output = interpreter.get_tensor(output_index)
        predictions.append(output)
    
    return classification_report(y_test, predictions)
```

**Evaluation Metrics**:
- **Accuracy**: Overall classification accuracy
- **Precision/Recall**: Per-class performance metrics
- **F1-Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: Detailed classification breakdown
- **Inference Time**: Model performance benchmarks

### 6. Deployment Pipeline

#### Production Deployment Steps:
1. **Data Collection**: Gather real network traffic samples
2. **Feature Engineering**: Process raw data into ML-ready format
3. **Model Training**: Train on labeled dataset with hyperparameter tuning
4. **Model Validation**: Comprehensive testing on holdout dataset
5. **TFLite Conversion**: Optimize for mobile deployment
6. **Android Integration**: Embed model in Android application
7. **Testing**: Device testing and performance validation
8. **Deployment**: Release to target devices

#### Continuous Improvement:
- **Online Learning**: Adapt to new traffic patterns
- **Performance Monitoring**: Track accuracy and inference speed
- **Model Updates**: Regular retraining with new data
- **A/B Testing**: Compare model versions in production

## API Reference

### Core Functions

#### Data Processing
```python
# Convert PCAP to CSV
robust_pcap_to_csv(pcap_path: str, csv_path: str) -> None

# Create time-based windows
create_windows(df: pd.DataFrame, window_size: float = 5.0) -> pd.DataFrame

# Generate synthetic data
generate_synthetic_windows(n: int = 2000, seed: int = 42) -> pd.DataFrame
```

#### Machine Learning
```python
# Train MLP model
train_mlp(X_train, y_train, X_val, y_val, input_dim: int, epochs: int = 25) -> keras.Model

# Convert to TFLite
convert_to_tflite(model: keras.Model, X_calib, out_path: str) -> bytes

# Evaluate model
eval_tflite(tflite_path: str, X_test, y_test) -> dict
```

#### Preprocessing
```python
# Normalize features and save scaler
normalize_save(X: pd.DataFrame, out_path: str) -> Tuple[pd.DataFrame, dict]

# Load and preprocess data
load_windows_csv(path: str) -> pd.DataFrame
```

## Configuration

### Model Hyperparameters
```python
MODEL_CONFIG = {
    'hidden_layers': [64, 32],
    'dropout_rate': 0.2,
    'learning_rate': 0.001,
    'batch_size': 64,
    'epochs': 25,
    'validation_split': 0.2
}

WINDOW_CONFIG = {
    'window_size': 5.0,  # seconds
    'overlap': 0.0,      # no overlap
    'min_packets': 5     # minimum packets per window
}
```

### Android Configuration
```xml
<service android:name=".CaptureVpnService"
         android:permission="android.permission.BIND_VPN_SERVICE"
         android:foregroundServiceType="specialUse" />
```

## Performance Optimization

### Mobile Deployment Optimizations:
1. **Model Quantization**: INT8 quantization reduces model size by 4x
2. **Feature Selection**: Use only most predictive features
3. **Batch Processing**: Process multiple windows simultaneously
4. **Memory Management**: Efficient buffer management for streaming data
5. **Threading**: Background processing to maintain UI responsiveness

### Scalability Considerations:
- **Edge Computing**: All processing on-device for privacy and speed
- **Resource Constraints**: Optimized for mobile CPU and memory limits
- **Battery Efficiency**: Minimize background processing impact
- **Network Efficiency**: No cloud communication required
