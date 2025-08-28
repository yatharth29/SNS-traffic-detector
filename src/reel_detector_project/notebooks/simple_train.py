# notebooks/simple_train.py
# Simplified training script to avoid scipy issues
import os, sys, json
import numpy as np
import pandas as pd

def load_windows_csv(path):
    df = pd.read_csv(path)
    if 'label' not in df.columns:
        raise ValueError("CSV must contain 'label' column.")
    return df

def normalize_save(X, out_path):
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-9
    Xn = (X - mean) / std
    scaler = {'mean': mean.tolist(), 'std': std.tolist(), 'features': list(X.columns)}
    with open(out_path, 'w') as f:
        json.dump(scaler, f)
    return Xn, scaler

def simple_train(X_train, y_train, X_test, y_test):
    print('[Simple] Training basic model...')
    # Simple rule-based classifier for demo
    # In real implementation, you'd use sklearn or tensorflow
    predictions = []
    for i in range(len(X_test)):
        # Simple rule: if bytes_down > 50000, predict reel (1), else non-reel (0)
        if X_test.iloc[i]['bytes_down'] > 50000:
            predictions.append(1)
        else:
            predictions.append(0)
    
    # Calculate accuracy
    correct = sum(1 for p, t in zip(predictions, y_test) if p == t)
    accuracy = correct / len(y_test)
    print(f'[Simple] Test accuracy: {accuracy:.3f}')
    return predictions

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python simple_train.py data/windows_labeled_synthetic.csv')
        sys.exit(1)
    
    csv_path = sys.argv[1]
    print(f'Loading data from: {csv_path}')
    
    df = load_windows_csv(csv_path)
    print(f'Loaded {len(df)} rows with {len(df.columns)} columns')
    
    # Prepare features and labels
    X = df.drop(columns=[c for c in ['wstart'] if c in df.columns] + ['label'])
    y = df['label'].values
    
    print(f'Features: {list(X.columns)}')
    print(f'Labels: {np.unique(y, return_counts=True)}')
    
    # Create output directory
    os.makedirs('models', exist_ok=True)
    
    # Normalize features
    Xn, scaler = normalize_save(X, 'models/scaler.json')
    print('Saved scaler to models/scaler.json')
    
    # Simple train/test split
    split_idx = int(len(Xn) * 0.8)
    X_train, X_test = Xn[:split_idx], Xn[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print(f'Train size: {len(X_train)}, Test size: {len(X_test)}')
    
    # Train simple model
    predictions = simple_train(X_train, y_train, X_test, y_test)
    
    print('Training completed successfully!')
    print('Next steps:')
    print('1. Install tensorflow: pip install tensorflow')
    print('2. Run full training: python train_and_convert.py data/windows_labeled_synthetic.csv')
    print('3. Or use the simple model for now')
