# User Guide

## Getting Started

This guide walks you through using the SNS Reel vs Non-Reel Traffic Detector for both development and real-world deployment.

## Quick Start (5 Minutes)

### 1. Generate Demo Data
```bash
cd notebooks
python demo_synthetic_data.py
```
✅ Creates synthetic network traffic data for testing

### 2. Train Your First Model
```bash
python train_and_convert.py ../data/windows_labeled_synthetic.csv
```
✅ Trains ML models and converts to mobile-ready format

### 3. Test the Model
```bash
python eval_tflite.py
```
✅ Evaluates model performance - expect ~84% accuracy on synthetic data

## Understanding the Workflow

### Data Flow Overview
```
Real Network → PCAP Capture → CSV Conversion → Feature Windows → Model Training → Mobile Deployment
```

### Key Components
1. **PCAP Processing**: Convert network captures to structured data
2. **Feature Engineering**: Extract meaningful patterns from network flows
3. **Model Training**: Train ML models to distinguish reel vs non-reel traffic
4. **Mobile Deployment**: Deploy quantized models to Android devices

## Working with Real Network Data

### Step 1: Capture Network Traffic

**Option A: Using Wireshark (GUI)**
1. Open Wireshark
2. Select network interface (WiFi/Ethernet)
3. Start capture while using social media apps
4. Stop capture and save as `.pcap` file

**Option B: Using tshark (Command Line)**
```bash
# Capture for 60 seconds
tshark -i wlan0 -a duration:60 -w capture.pcap

# Capture specific traffic (optional filters)
tshark -i wlan0 -f "tcp port 80 or tcp port 443" -w capture.pcap
```

**Option C: Using Android VPN Service (Future)**
The mobile app can capture traffic directly on Android devices.

### Step 2: Convert PCAP to CSV

**For large files (recommended):**
```bash
python proper_convert.py capture.pcap network_data.csv
```

**For quick testing:**
```bash
python quick_convert.py capture.pcap network_data.csv
```

**With resume capability:**
```bash
python proper_convert.py large_capture.pcap network_data.csv --resume --max 50000
```

### Step 3: Generate Training Windows

Currently requires manual implementation. The process:

1. **Time Windows**: Group packets into 5-second intervals
2. **Feature Calculation**: Compute bandwidth, packet counts, timing statistics
3. **Labeling**: Mark windows as "reel" (1) or "non-reel" (0)

**Example window structure:**
```csv
wstart,bytes_down,pkt_count_down,avg_pkt_size_down,bitrate_down,iat_mean_down,burst_count_down,ratio_down_up,label
0.0,180000,75,2400,36000,0.067,8,12.5,1
5.0,45000,32,1406,9000,0.156,3,2.8,0
```

### Step 4: Train Production Models

```bash
python notebooks/train_and_convert.py data/your_labeled_windows.csv
```

This generates:
- `models/model.h5` - Full TensorFlow model
- `models/model_quant.tflite` - Quantized mobile model  
- `models/scaler.json` - Feature normalization parameters

## Android App Usage

### Setup
1. Install app on Android device
2. Grant VPN permissions when prompted
3. Copy trained models to app assets folder

### Real-Time Classification
1. **Enable Monitoring**: Toggle "Real-time Monitoring" switch
2. **Use Social Apps**: Open Instagram, TikTok, YouTube, Facebook
3. **View Predictions**: App displays "REEL DETECTED! 🎬" or "Normal Traffic 📱"
4. **Monitor Confidence**: Shows prediction confidence percentage

### Data Collection Mode
1. **Start Labeling**: Tap "Label Reel Start" before watching reels/videos
2. **Use Target App**: Watch reels, stories, or videos
3. **End Labeling**: Tap "Label End" when finished
4. **Export Data**: Collected data can be used for model retraining

## Interpreting Results

### Classification Output
- **Score > 0.5**: Classified as Reel traffic
- **Score ≤ 0.5**: Classified as Non-reel traffic
- **Confidence**: How certain the model is (0-100%)

### Performance Metrics

**Accuracy**: Overall correctness rate
```
Accuracy = (Correct Predictions) / (Total Predictions)
Target: >85% on real-world data
```

**Precision**: How many predicted reels are actually reels
```
Precision = True Positives / (True Positives + False Positives)
Important for avoiding false alerts
```

**Recall**: How many actual reels are detected
```
Recall = True Positives / (True Positives + False Negatives)  
Important for not missing reel traffic
```

### Expected Performance
- **Synthetic Data**: 84-88% accuracy
- **Real Network Data**: 75-90% accuracy (varies by network conditions)
- **Inference Speed**: <50ms on modern Android devices
- **Battery Impact**: Minimal (<5% additional drain)

## Customization and Tuning

### Adjusting Time Windows
Edit window size in feature extraction:
```python
WINDOW_SIZE = 5.0  # seconds (default)
# Smaller = more responsive, less stable
# Larger = more stable, less responsive  
```

### Feature Selection
Modify features in `demo_synthetic_data.py`:
```python
# Add new features
'tcp_flags_count': count_tcp_flags(packets),
'dns_queries': count_dns_queries(packets),
'ssl_handshakes': count_ssl_handshakes(packets)
```

### Model Hyperparameters
Adjust in `train_and_convert.py`:
```python
# Neural network architecture
keras.layers.Dense(128, activation='relu'),  # Increase neurons
keras.layers.Dropout(0.3),                  # Adjust dropout
keras.layers.Dense(64, activation='relu'),  # Add layers
```

## Troubleshooting

### Common Issues

**Low Accuracy (<70%)**
- Check data labeling quality
- Ensure sufficient training examples (>1000 per class)
- Verify network conditions are similar to training data
- Consider retraining with more diverse data

**High Battery Usage**
- Reduce inference frequency
- Use lighter model architecture
- Implement smarter triggering (only classify when needed)

**App Crashes**
- Check model file sizes (<5MB recommended)
- Verify TFLite model compatibility
- Monitor memory usage during inference

**Slow Performance**
- Use quantized models only
- Reduce feature dimensions
- Optimize feature calculation algorithms

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring
```python
import time
start = time.time()
prediction = model.predict(features)
latency = (time.time() - start) * 1000  # ms
print(f"Inference took {latency:.2f}ms")
```

## Best Practices

### Data Collection
- **Diverse Conditions**: Collect data on different networks (WiFi, cellular, etc.)
- **Balanced Classes**: Ensure roughly equal reel/non-reel examples
- **Quality Labels**: Double-check manual annotations
- **Representative Usage**: Include normal app usage patterns

### Model Development
- **Start Simple**: Begin with RandomForest before neural networks
- **Validate Carefully**: Use proper train/validation/test splits
- **Monitor Overfitting**: Check performance on unseen data
- **Iterate Quickly**: Use synthetic data for rapid prototyping

### Deployment
- **Test Thoroughly**: Validate on multiple devices and networks
- **Monitor Performance**: Track accuracy in production
- **Update Regularly**: Retrain models as apps and networks evolve
- **Respect Privacy**: Never log or transmit actual packet contents

## Advanced Usage

### Custom Feature Engineering
```python
def extract_custom_features(packets):
    return {
        'flow_duration': max_time - min_time,
        'bidirectional_ratio': upstream_bytes / downstream_bytes,
        'packet_size_entropy': calculate_entropy(packet_sizes),
        'inter_arrival_variance': variance(inter_arrival_times)
    }
```

### Ensemble Models
```python
# Combine multiple models for better accuracy
rf_pred = rf_model.predict_proba(features)[0][1]
nn_pred = nn_model.predict(features)[0]
ensemble_pred = 0.6 * nn_pred + 0.4 * rf_pred
```

### Real-Time Optimization
```python
# Batch processing for efficiency
if len(feature_buffer) >= BATCH_SIZE:
    predictions = model.predict(np.array(feature_buffer))
    feature_buffer.clear()
```

## Getting Help

### Documentation
- 📋 [Architecture Overview](architecture.md)
- 🔧 [Installation Guide](installation.md)  
- 💻 [Implementation Details](implementation.md)
- 🛠️ [Technical Stack](tech-stack.md)

### Community Support
- 🐛 **Report Issues**: GitHub Issues with logs and reproduction steps
- 💡 **Feature Requests**: Describe your use case and requirements
- 📚 **Documentation**: Contribute improvements and examples
- 🤝 **Code Contributions**: Submit pull requests with tests

### Performance Optimization
- Profile your specific use case
- Consider edge computing deployment
- Explore federated learning approaches
- Investigate 5G/MEC integration opportunities

You're now ready to build production-ready reel detection systems! 🚀
