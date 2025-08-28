# System Architecture

This document describes the end-to-end architecture of the SNS Reel vs Non‑Reel Traffic Detector.

## High-Level Overview

```
PCAP/Live Traffic → Feature Extraction → Labeled Windows CSV → Training (RF/MLP) → TFLite Model → Android App Inference
```

- Data Source: PCAP captures (or Android VPN capture in future)
- Processing: Python pipeline for feature engineering and training
- Models: RandomForest (baseline), MLP (TensorFlow → TFLite)
- Deployment: On-device inference in Android via TensorFlow Lite

## Components

1. Data Processing
   - PCAP to CSV converters: proper_convert.py, robust_convert.py, quick_convert.py
   - Window generation and labeling (via notebooks + future Android labeling)

2. Training and Conversion
   - src/preprocess.py – clean/encode/split
   - src/train.py – RandomForest training
   - notebooks/train_and_convert.py – MLP + quantized TFLite

3. Mobile Application (Android)
   - VPN-based capture service (CaptureVpnService)
   - Real-time features (FeatureBuffer)
   - Normalization (Normalizer) using models/scaler.json
   - Inference (TFLiteClassifier)
   - UI (MainActivity)

## Data Flow

1. PCAP → CSV (ts, length, src, dst) using Tshark or native parsing
2. CSV → Windows with engineered features (bytes_down/up, pkt counts, bitrate, IAT, bursts)
3. Windows + Labels → Model Training (RF/MLP)
4. Model Export → model_quant.tflite and scaler.json
5. Android → Real-time feature aggregation → normalize → TFLite inference

## Architecture Rationale

- Privacy: metadata-only features, no payload inspection
- Performance: TFLite with quantization for mobile inference
- Robustness: streaming PCAP conversion; resume for large files
- Portability: Python for training, Kotlin for Android

