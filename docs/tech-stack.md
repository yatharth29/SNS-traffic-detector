# Technical Stack

## Core Technologies

### Machine Learning & Data Science
- **[TensorFlow](https://www.tensorflow.org/)** - Neural network training and model conversion
- **[TensorFlow Lite](https://www.tensorflow.org/lite)** - Mobile inference engine with quantization
- **[scikit-learn](https://scikit-learn.org/)** - RandomForest baseline models and preprocessing
- **[NumPy](https://numpy.org/)** - Numerical computing and array operations
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

### Mobile Development
- **[Kotlin](https://kotlinlang.org/)** - Primary Android development language
- **[Android VPN Service API](https://developer.android.com/reference/android/net/VpnService)** - Network traffic capture
- **[Android TensorFlow Lite API](https://www.tensorflow.org/lite/android)** - On-device ML inference

### Network Analysis
- **[Wireshark/TShark](https://www.wireshark.org/)** - PCAP file processing and analysis
- **[PyShark](https://github.com/KimiNewt/pyshark)** - Python wrapper for packet analysis
- **Native PCAP Parsing** - Custom implementation for minimal dependencies

### Development & Deployment
- **[Python 3.8+](https://www.python.org/)** - Primary backend language
- **[Jupyter Notebooks](https://jupyter.org/)** - Interactive development and experimentation
- **[Git](https://git-scm.com/)** - Version control
- **[GitHub](https://github.com/)** - Code hosting and collaboration

## Data Processing Libraries

### Statistical Analysis
- **[Matplotlib](https://matplotlib.org/)** - Data visualization and plotting
- **[Seaborn](https://seaborn.pydata.org/)** - Statistical data visualization
- **[SciPy](https://www.scipy.org/)** - Scientific computing (optional dependency)

### Alternative ML Frameworks
- **[XGBoost](https://xgboost.readthedocs.io/)** - Gradient boosting for comparison models
- **[PyTorch](https://pytorch.org/)** - Alternative deep learning framework

## API & Web Frameworks (Future Extensions)
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python API framework
- **[Flask](https://flask.palletsprojects.com/)** - Lightweight web framework
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server for async applications

## Data Formats & Protocols

### Network Data
- **PCAP/PCAPNG** - Standard network capture formats
- **CSV** - Structured data storage for training
- **JSON** - Feature scaling parameters and configuration

### Model Formats
- **HDF5 (.h5)** - TensorFlow model storage
- **TensorFlow Lite (.tflite)** - Quantized mobile models
- **Pickle (.pkl)** - scikit-learn model serialization

## Development Tools

### Code Quality
- **Type Hints** - Python static typing for better code quality
- **Error Handling** - Comprehensive exception management
- **Logging** - Structured application logging

### Performance Monitoring
- **Memory Profiling** - Efficient resource utilization
- **Timing Measurements** - Inference latency optimization
- **Progress Tracking** - Long-running process monitoring

## External Dependencies

### System Requirements
- **Python 3.8+** - Core runtime environment
- **Android SDK 24+** - Mobile app development
- **Wireshark** - PCAP processing (optional, fallback to native parsing)
- **Git** - Version control system

### Optional Enhancements
- **CUDA/GPU Support** - TensorFlow GPU acceleration for training
- **Docker** - Containerized deployment (future enhancement)
- **Cloud Storage** - Dataset and model distribution (future)

## Architecture Decisions

### Why TensorFlow Lite?
- **Mobile Optimization**: Designed specifically for on-device inference
- **Quantization Support**: INT8 quantization reduces model size by 4x
- **Cross-Platform**: Works on Android, iOS, and embedded devices
- **Offline Capability**: No internet connection required for inference

### Why Kotlin for Android?
- **Modern Language**: Concise syntax with null safety
- **Android Native**: First-class Android development support
- **Coroutines**: Efficient asynchronous programming for VPN service
- **Interoperability**: Seamless integration with Java libraries

### Why RandomForest + Neural Network?
- **Interpretability**: RandomForest provides feature importance insights
- **Performance**: Neural networks excel at pattern recognition
- **Robustness**: Ensemble approach reduces overfitting risk
- **Deployment Options**: RF for debugging, NN for production

### Why Streaming PCAP Processing?
- **Memory Efficiency**: Constant memory usage regardless of file size
- **Scalability**: Handles GB+ network captures
- **Resume Capability**: Fault tolerance for long-running processes
- **Real-time Potential**: Pipeline architecture supports live processing

## Quality Assurance

### Testing Strategy
- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end pipeline verification
- **Performance Tests**: Latency and throughput measurement
- **Mobile Testing**: On-device validation

### Code Standards
- **PEP 8**: Python code style guidelines
- **Kotlin Conventions**: Android development best practices
- **Documentation**: Comprehensive inline comments
- **Error Handling**: Graceful failure modes

This technical stack enables a production-ready, privacy-preserving, and high-performance solution for real-time traffic classification on mobile devices.
