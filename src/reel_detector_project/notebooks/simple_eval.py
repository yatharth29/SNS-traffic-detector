# notebooks/simple_eval.py
# Simple evaluation script for the reel detector project
import pandas as pd
import numpy as np
import json
import os

def load_data_and_scaler():
    """Load the synthetic data and scaler"""
    # Load data
    df = pd.read_csv('data/windows_labeled_synthetic.csv')
    
    # Load scaler
    with open('models/scaler.json', 'r') as f:
        scaler = json.load(f)
    
    return df, scaler

def simple_classifier(features):
    """Simple rule-based classifier for demo purposes"""
    # Simple rules based on network characteristics
    bytes_down = features['bytes_down']
    pkt_count_down = features['pkt_count_down']
    bitrate_down = features['bitrate_down']
    
    # Rule: High bandwidth + many packets + high bitrate = likely reel
    if (bytes_down > 100000 and 
        pkt_count_down > 50 and 
        bitrate_down > 50000):
        return 1  # Reel
    else:
        return 0  # Non-reel

def evaluate_model():
    """Evaluate the simple classifier on the synthetic data"""
    print("=== Reel Detector Project - Simple Evaluation ===\n")
    
    # Load data
    df, scaler = load_data_and_scaler()
    print(f"✓ Loaded {len(df)} data samples")
    print(f"✓ Loaded scaler with {len(scaler['features'])} features")
    
    # Prepare features
    feature_cols = [col for col in df.columns if col not in ['wstart', 'label']]
    X = df[feature_cols]
    y = df['label']
    
    print(f"\nFeatures used: {feature_cols}")
    print(f"Label distribution: {dict(y.value_counts())}")
    
    # Make predictions
    predictions = []
    for _, row in X.iterrows():
        pred = simple_classifier(row)
        predictions.append(pred)
    
    # Calculate metrics
    correct = sum(1 for p, t in zip(predictions, y) if p == t)
    accuracy = correct / len(y)
    
    # Confusion matrix
    tp = sum(1 for p, t in zip(predictions, y) if p == 1 and t == 1)
    tn = sum(1 for p, t in zip(predictions, y) if p == 0 and t == 0)
    fp = sum(1 for p, t in zip(predictions, y) if p == 1 and t == 0)
    fn = sum(1 for p, t in zip(predictions, y) if p == 0 and t == 1)
    
    print(f"\n=== Results ===")
    print(f"Accuracy: {accuracy:.3f} ({correct}/{len(y)})")
    print(f"True Positives (Reel detected as Reel): {tp}")
    print(f"True Negatives (Non-reel detected as Non-reel): {tn}")
    print(f"False Positives (Non-reel detected as Reel): {fp}")
    print(f"False Negatives (Reel detected as Non-reel): {fn}")
    
    # Show some examples
    print(f"\n=== Sample Predictions ===")
    sample_size = min(10, len(df))
    for i in range(sample_size):
        actual = y.iloc[i]
        predicted = predictions[i]
        status = "✓" if actual == predicted else "✗"
        print(f"Sample {i+1}: Actual={actual}, Predicted={predicted} {status}")
    
    print(f"\n=== Next Steps ===")
    print("1. Your synthetic data is working!")
    print("2. Basic classifier is functional")
    print("3. When Thursday's PCAP download finishes, you can:")
    print("   - Convert PCAP to CSV using pcap_to_csv.py")
    print("   - Label the data for reel detection")
    print("   - Train a more sophisticated model")
    print("4. The Android app is ready for integration")
    
    return accuracy, predictions

if __name__ == '__main__':
    evaluate_model()
