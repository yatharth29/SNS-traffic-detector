# Installation Guide

## Prerequisites

### System Requirements
- **Python 3.8+** (3.9+ recommended)
- **4GB+ RAM** (8GB recommended for training)
- **2GB free disk space**
- **Git** for version control
- **Android Studio** (for mobile app development)

### Operating System Support
- **Windows 10/11** ✅
- **macOS 10.15+** ✅  
- **Ubuntu 18.04+** ✅
- **Android 7.0+ (API 24+)** ✅

## Python Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yatharth29/SNS-traffic-detector.git
cd SNS-traffic-detector
```

### 2. Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install core dependencies
pip install numpy pandas scikit-learn matplotlib seaborn tensorflow

# Install optional dependencies
pip install torch xgboost fastapi uvicorn jupyter

# For PCAP processing (if using pyshark)
pip install pyshark tqdm
```

### 4. Verify Installation
```bash
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
python -c "import sklearn; print('scikit-learn:', sklearn.__version__)"
python -c "import numpy as np; print('NumPy:', np.__version__)"
```

## Quick Start - Synthetic Data Pipeline

### 1. Generate Synthetic Training Data
```bash
cd notebooks
python demo_synthetic_data.py
```

This creates `data/windows_labeled_synthetic.csv` with 2000 sample windows.

### 2. Train and Convert Model
```bash
python train_and_convert.py ../data/windows_labeled_synthetic.csv
```

This will:
- Train RandomForest and MLP models
- Convert to quantized TensorFlow Lite
- Save `models/model_quant.tflite` and `models/scaler.json`

### 3. Evaluate Model
```bash
python eval_tflite.py
```

Expected output:
```
              precision    recall  f1-score   support
           0       0.85      0.82      0.83       200
           1       0.83      0.86      0.85       200
    accuracy                           0.84       400
```

## PCAP Processing Setup

### Option 1: Using Wireshark/tshark (Recommended)

**Windows:**
1. Download and install [Wireshark](https://www.wireshark.org/download.html)
2. Add Wireshark to PATH: `C:\Program Files\Wireshark`
3. Verify: `tshark --version`

**macOS:**
```bash
brew install wireshark
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install tshark
```

### Option 2: Native Python Parsing
No additional setup required - uses built-in Python libraries.

### Convert PCAP to CSV
```bash
# Using tshark (fast, recommended)
python proper_convert.py input.pcap output.csv

# Using native parsing (slower, no dependencies)
python quick_convert.py input.pcap output.csv

# With resume capability for large files
python proper_convert.py large_file.pcap output.csv --resume --max 100000
```

## Android App Setup

### Prerequisites
- **Android Studio Arctic Fox+**
- **Android SDK 24+**
- **Kotlin plugin enabled**

### 1. Open Project
```bash
# Navigate to Android project
cd android

# Open in Android Studio
studio .
```

### 2. Build Configuration
In `build.gradle (Module: app)`:
```gradle
android {
    compileSdk 33
    minSdk 24
    targetSdk 33
    
    buildFeatures {
        viewBinding true
    }
}

dependencies {
    implementation 'org.tensorflow:tensorflow-lite:2.13.0'
    implementation 'com.google.code.gson:gson:2.10.1'
}
```

### 3. Copy Models to Assets
```bash
# Copy trained models to Android assets
cp ../models/model_quant.tflite android/app/src/main/assets/
cp ../models/scaler.json android/app/src/main/assets/
```

### 4. Build and Install
```bash
# Build debug APK
./gradlew assembleDebug

# Install to device
./gradlew installDebug
```

## Development Environment Setup

### Jupyter Notebook Setup
```bash
# Install Jupyter
pip install jupyter notebook

# Start Jupyter server
jupyter notebook

# Open browser to http://localhost:8888
```

### IDE Configuration

**VS Code:**
```bash
# Install Python extension
code --install-extension ms-python.python

# Open project
code .
```

**PyCharm:**
- Configure Python interpreter to use virtual environment
- Enable scientific mode for better data analysis

## Testing Installation

### 1. Run Full Pipeline Test
```bash
# Generate synthetic data
python notebooks/demo_synthetic_data.py

# Train models
python notebooks/train_and_convert.py ../data/windows_labeled_synthetic.csv

# Evaluate performance
python notebooks/eval_tflite.py
```

### 2. Test Android App
1. Enable Developer Options on Android device
2. Enable USB Debugging
3. Connect device via USB
4. Install and run app: `./gradlew installDebug`
5. Grant VPN permissions when prompted

### 3. Verify Model Loading
```python
import tensorflow as tf
interpreter = tf.lite.Interpreter(model_path='models/model_quant.tflite')
interpreter.allocate_tensors()
print("Model loaded successfully!")
```

## Troubleshooting

### Common Issues

**TensorFlow Installation:**
```bash
# If TensorFlow fails to install
pip install tensorflow-cpu  # CPU-only version

# For Apple Silicon Macs
pip install tensorflow-macos tensorflow-metal
```

**PCAP Processing:**
```bash
# If tshark not found
export PATH=$PATH:/usr/local/bin:/opt/homebrew/bin

# Permission issues on Linux
sudo usermod -a -G wireshark $USER
newgrp wireshark
```

**Android Build Issues:**
- Update Android Studio to latest version
- Sync Gradle files
- Clean and rebuild: `./gradlew clean build`
- Check SDK versions in `build.gradle`

**Memory Issues:**
```bash
# Increase Java heap size for Gradle
export GRADLE_OPTS="-Xmx4g -XX:MaxMetaspaceSize=512m"
```

### Performance Optimization

**Training Speed:**
```bash
# Use multiple CPU cores
export OMP_NUM_THREADS=4

# For GPU acceleration (if available)
pip install tensorflow-gpu
```

**Mobile Performance:**
- Use quantized models only
- Minimize background apps during testing
- Monitor memory usage in Android Studio Profiler

### Getting Help

1. **Check logs** in `logs/` directory
2. **Enable debug mode** in scripts
3. **Submit issues** on GitHub with error logs
4. **Check dependencies** with `pip list`

## Next Steps

After successful installation:
1. 📚 Read [User Guide](user-guide.md) for usage instructions
2. 🏗️ Review [Architecture](architecture.md) for system understanding  
3. 💻 Explore [Implementation](implementation.md) for technical details
4. 🎯 Check [Features](features.md) for capability overview

Your environment is now ready for SNS traffic classification development!
