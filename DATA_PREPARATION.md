# DrainSentinel: Data Preparation and Preprocessing Guide

**Document Version:** 1.0  
**Date:** November 30, 2025  
**Status:** Implementation Phase

---

## 1. Overview

This document provides detailed instructions for preparing and preprocessing data for the DrainSentinel Edge AI application. The process involves three parallel data streams that will be integrated into Edge Impulse for model training.

---

## 2. Data Sources and Licensing

### 2.1 Visual Data: S-BIRD Dataset

**Source:** University of Tromsø, Norway  
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)  
**Citation:** Patil, R.R., et al. (2023). S-BIRD: A Novel Critical Multi-Class Imagery Dataset for Sewer Monitoring and Maintenance Systems. MDPI Sensors, 23(6), 2966.

**Access Instructions:**
1. Visit the MDPI Sensors article: https://www.mdpi.com/1424-8220/23/6/2966
2. Download the supplementary materials containing the dataset
3. Extract images and annotations

**Data Structure:**
```
S-BIRD/
├── images/
│   ├── blockage_images/
│   ├── debris_images/
│   └── normal_images/
└── annotations/
    └── labels.csv
```

**Classes:**
- No blockage (clear drain)
- Partial blockage (debris present)
- Complete blockage (fully obstructed)
- Debris types (leaves, plastic, sediment, grease)

### 2.2 Visual Data: Pipe Inspection Dataset

**Source:** Roboflow Universe  
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)  
**URL:** https://universe.roboflow.com/pipe/pipe-inspection  
**Size:** 538 images with object detection annotations

**Download Instructions:**
1. Visit the Roboflow Universe page
2. Click "Use this Dataset"
3. Select "Download" and choose format (COCO JSON recommended)
4. Extract to local directory

**Classes:**
- Alligator crack
- Block crack
- Crack
- Diagonal crack
- Hairline crack
- Longitudinal crack
- Rust
- Transverse crack
- Void
- Wide crack

### 2.3 Distance Sensor Data

**Source:** Kaggle  
**License:** CC BY-SA 4.0  
**URL:** https://www.kaggle.com/datasets/caetanoranieri/water-level-identification-with-lidar  
**Citation:** Ranieri, C.M., et al. (2024). Water level identification with laser sensors, inertial units, and machine learning. Engineering Applications of Artificial Intelligence, 127, 107235.

**Download Instructions:**
1. Create Kaggle account (free)
2. Visit the dataset page
3. Click "Download" to get CSV files
4. Extract and process

**Data Format:**
```
timestamp, lidar_distance_cm, ultrasonic_distance_cm, imu_accel_x, imu_accel_y, imu_accel_z
2023-01-01 10:00:00, 25.3, 24.8, 0.01, 0.02, 9.81
2023-01-01 10:00:01, 25.2, 24.9, 0.00, 0.01, 9.82
...
```

---

## 3. Data Preprocessing Pipeline

### 3.1 Visual Data Preprocessing

#### Step 1: Image Resizing and Normalization

```python
import cv2
import numpy as np
from pathlib import Path

def preprocess_image(image_path, target_size=(96, 96)):
    """
    Resize and normalize image for model input
    
    Args:
        image_path: Path to input image
        target_size: Target resolution (default 96x96 for edge efficiency)
    
    Returns:
        Normalized numpy array (0-1 range)
    """
    # Read image
    img = cv2.imread(str(image_path))
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize to target size
    img = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
    
    # Normalize to 0-1 range
    img = img.astype(np.float32) / 255.0
    
    return img
```

#### Step 2: Data Augmentation

```python
import albumentations as A

def create_augmentation_pipeline(train=True):
    """
    Create data augmentation pipeline for training
    
    Args:
        train: If True, apply augmentations; if False, only normalize
    
    Returns:
        Albumentations Compose object
    """
    if train:
        return A.Compose([
            A.Rotate(limit=15, p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.HorizontalFlip(p=0.5),
            A.GaussNoise(p=0.3),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['labels']))
    else:
        return A.Compose([
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['labels']))
```

#### Step 3: Dataset Organization

```
data/visual/
├── train/
│   ├── no_blockage/
│   │   ├── img_001.jpg
│   │   ├── img_002.jpg
│   │   └── ...
│   ├── partial_blockage/
│   │   ├── img_101.jpg
│   │   └── ...
│   └── complete_blockage/
│       ├── img_201.jpg
│       └── ...
├── val/
│   ├── no_blockage/
│   ├── partial_blockage/
│   └── complete_blockage/
└── test/
    ├── no_blockage/
    ├── partial_blockage/
    └── complete_blockage/
```

### 3.2 Time-Series Data Preprocessing (Water Level)

#### Step 1: Data Loading and Cleaning

```python
import pandas as pd
import numpy as np

def load_and_clean_sensor_data(csv_path, sensor_column='distance_cm'):
    """
    Load and clean sensor data from CSV
    
    Args:
        csv_path: Path to sensor data CSV
        sensor_column: Name of distance column
    
    Returns:
        Cleaned pandas DataFrame
    """
    # Load data
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['timestamp'])
    
    # Handle missing values (interpolation)
    df[sensor_column] = df[sensor_column].interpolate(method='linear')
    
    # Remove outliers (values outside 0-100 cm range)
    df = df[(df[sensor_column] >= 0) & (df[sensor_column] <= 100)]
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    return df
```

#### Step 2: Windowing and Normalization

```python
def create_time_series_windows(data, window_size=60, stride=30):
    """
    Create sliding windows for time-series data
    
    Args:
        data: 1D array of sensor readings
        window_size: Size of each window (60 samples = 60 seconds @ 1 Hz)
        stride: Stride between windows
    
    Returns:
        List of windows and corresponding labels
    """
    windows = []
    labels = []
    
    for i in range(0, len(data) - window_size, stride):
        window = data[i:i + window_size]
        
        # Normalize to 0-1 range
        window_normalized = (window - window.min()) / (window.max() - window.min() + 1e-6)
        
        # Determine label based on mean water level
        mean_level = window.mean()
        if mean_level < 30:
            label = 0  # Normal
        elif mean_level < 60:
            label = 1  # Elevated
        else:
            label = 2  # Critical
        
        windows.append(window_normalized)
        labels.append(label)
    
    return np.array(windows), np.array(labels)
```

#### Step 3: Data Format for Edge Impulse

```python
def prepare_for_edge_impulse(windows, labels, output_path):
    """
    Prepare time-series data in Edge Impulse format
    
    Args:
        windows: Array of windowed data
        labels: Array of labels
        output_path: Output file path
    """
    import json
    
    data_dict = {
        "total_sequences": len(windows),
        "sequence_length": windows.shape[1],
        "sampling_rate_hz": 1,
        "unit": "centimeters",
        "classes": {
            0: "normal (0-30cm)",
            1: "elevated (31-60cm)",
            2: "critical (>60cm)"
        },
        "data": windows.tolist(),
        "labels": labels.tolist()
    }
    
    with open(output_path, 'w') as f:
        json.dump(data_dict, f)
```

### 3.3 Environmental Data Preprocessing

#### Step 1: Data Loading and Alignment

```python
def load_environmental_data(weather_csv, sensor_csv):
    """
    Load and align weather and sensor data
    
    Args:
        weather_csv: Path to weather data
        sensor_csv: Path to sensor data
    
    Returns:
        Merged DataFrame with aligned timestamps
    """
    # Load data
    weather_df = pd.read_csv(weather_csv, parse_dates=['timestamp'])
    sensor_df = pd.read_csv(sensor_csv, parse_dates=['timestamp'])
    
    # Merge on timestamp (inner join to keep only aligned records)
    merged = pd.merge(weather_df, sensor_df, on='timestamp', how='inner')
    
    # Sort by timestamp
    merged = merged.sort_values('timestamp')
    
    return merged
```

#### Step 2: Feature Normalization

```python
from sklearn.preprocessing import StandardScaler

def normalize_environmental_features(df):
    """
    Normalize environmental features to 0-1 range
    
    Args:
        df: DataFrame with environmental features
    
    Returns:
        Normalized DataFrame and scaler object
    """
    features = ['temperature', 'humidity', 'pressure', 'rainfall', 'water_level']
    
    scaler = StandardScaler()
    df_normalized = df.copy()
    df_normalized[features] = scaler.fit_transform(df[features])
    
    return df_normalized, scaler
```

#### Step 3: Label Generation

```python
def generate_flood_risk_labels(df):
    """
    Generate flood risk labels based on environmental factors
    
    Args:
        df: DataFrame with normalized environmental features
    
    Returns:
        Array of labels (0=low risk, 1=high risk)
    """
    # Weighted combination of factors
    risk_score = (
        0.40 * df['water_level'] +
        0.30 * df['rainfall'] +
        0.15 * (1 - df['pressure']) +  # Lower pressure = higher risk
        0.10 * df['humidity'] +
        0.05 * df['temperature']
    )
    
    # Threshold at 0.5 (normalized scale)
    labels = (risk_score > 0.5).astype(int)
    
    return labels
```

---

## 4. Data Split Strategy

### 4.1 Train/Validation/Test Split

```python
from sklearn.model_selection import train_test_split

def split_data(X, y, train_size=0.7, val_size=0.15, test_size=0.15, random_state=42):
    """
    Split data into train, validation, and test sets
    
    Args:
        X: Feature data
        y: Labels
        train_size: Proportion for training
        val_size: Proportion for validation
        test_size: Proportion for testing
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    # First split: train vs (val + test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, train_size=train_size, random_state=random_state, stratify=y
    )
    
    # Second split: val vs test
    val_ratio = val_size / (val_size + test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, train_size=val_ratio, random_state=random_state, stratify=y_temp
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test
```

### 4.2 Stratified Split for Imbalanced Data

```python
from sklearn.model_selection import StratifiedKFold

def stratified_k_fold_split(X, y, n_splits=5):
    """
    Perform stratified k-fold cross-validation
    
    Args:
        X: Feature data
        y: Labels
        n_splits: Number of folds
    
    Yields:
        Tuple of (train_indices, val_indices) for each fold
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    for train_idx, val_idx in skf.split(X, y):
        yield train_idx, val_idx
```

---

## 5. Quality Assurance

### 5.1 Data Validation Checklist

```python
def validate_dataset(X, y, dataset_name="Dataset"):
    """
    Validate dataset quality
    
    Args:
        X: Feature data
        y: Labels
        dataset_name: Name for reporting
    """
    print(f"\n=== {dataset_name} Validation ===")
    
    # Check for NaN values
    if np.isnan(X).any():
        print(f"⚠ WARNING: NaN values detected in X")
    else:
        print(f"✓ No NaN values in X")
    
    # Check for infinite values
    if np.isinf(X).any():
        print(f"⚠ WARNING: Infinite values detected in X")
    else:
        print(f"✓ No infinite values in X")
    
    # Check class distribution
    unique, counts = np.unique(y, return_counts=True)
    print(f"✓ Class distribution:")
    for cls, count in zip(unique, counts):
        percentage = (count / len(y)) * 100
        print(f"  - Class {cls}: {count} samples ({percentage:.1f}%)")
    
    # Check for severe imbalance
    if max(counts) / min(counts) > 3:
        print(f"⚠ WARNING: Severe class imbalance detected")
    
    # Check data shape
    print(f"✓ Data shape: X={X.shape}, y={y.shape}")
```

### 5.2 Visualization

```python
import matplotlib.pyplot as plt

def visualize_data_distribution(y, class_names=None):
    """
    Visualize class distribution
    
    Args:
        y: Labels
        class_names: List of class names
    """
    unique, counts = np.unique(y, return_counts=True)
    
    plt.figure(figsize=(10, 6))
    plt.bar(unique, counts)
    plt.xlabel('Class')
    plt.ylabel('Count')
    plt.title('Class Distribution')
    
    if class_names:
        plt.xticks(unique, class_names)
    
    plt.tight_layout()
    plt.savefig('class_distribution.png', dpi=150)
    plt.show()
```

---

## 6. Generated Synthetic Data

The following synthetic datasets have been generated for initial testing:

### 6.1 Visual Data Metadata
- **File:** `data/visual/metadata.json`
- **Content:** Metadata for 1,000 images (500 no blockage, 300 partial, 200 complete)
- **Purpose:** Reference for actual image dataset organization

### 6.2 Water Level Time-Series
- **File:** `data/sensor/water_level_data.json`
- **Content:** 1,000 sequences (60 samples each @ 1 Hz)
- **Classes:** Normal (500), Elevated (300), Critical (200)
- **Purpose:** Training data for LSTM water level model

### 6.3 Environmental Data
- **File:** `data/environmental/flood_risk_data.json`
- **Content:** 5,000 samples with 5 features
- **Classes:** Low risk (3,000), High risk (2,000)
- **Purpose:** Training data for flood prediction model

---

## 7. Edge Impulse Integration

### 7.1 Uploading Visual Data

1. Create new Edge Impulse project
2. Go to **Data acquisition** tab
3. Click **Upload data**
4. Select images from organized folders
5. Assign labels automatically based on folder structure
6. Verify labels in dataset view

### 7.2 Uploading Time-Series Data

1. Go to **Data acquisition** tab
2. Click **Upload data** → **Upload sensor data**
3. Select `water_level_data.json`
4. Configure:
   - Frequency: 1 Hz
   - Length: 60 seconds
   - Axes: 1 (distance)

### 7.3 Uploading Tabular Data

1. Go to **Data acquisition** tab
2. Click **Upload data** → **Upload tabular data**
3. Select `flood_risk_data.json`
4. Configure:
   - Features: 5 (temperature, humidity, pressure, rainfall, water_level)
   - Target: Binary classification

---

## 8. Performance Metrics

### 8.1 Visual Model Metrics

- **Accuracy:** Percentage of correctly classified images
- **Precision:** True positives / (True positives + False positives)
- **Recall:** True positives / (True positives + False negatives)
- **F1-Score:** Harmonic mean of precision and recall
- **Confusion Matrix:** Breakdown of correct/incorrect predictions per class

### 8.2 Time-Series Model Metrics

- **Accuracy:** Percentage of correctly classified sequences
- **Per-class Accuracy:** Accuracy for each water level class
- **Latency:** Inference time per sequence

### 8.3 Environmental Model Metrics

- **Accuracy:** Percentage of correctly predicted flood risk
- **Precision/Recall:** For high-risk class (minimize false negatives)
- **ROC-AUC:** Area under ROC curve

---

## 9. References

1. **Data Augmentation:** Albumentations library: https://albumentations.ai/
2. **Preprocessing:** Scikit-learn: https://scikit-learn.org/
3. **Edge Impulse Documentation:** https://docs.edgeimpulse.com/docs/edge-impulse-studio/data-acquisition

---

**Status:** Data Preparation Complete  
**Next Phase:** Model Training and Optimization
