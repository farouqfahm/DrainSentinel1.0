# DrainSentinel: Model Architecture and Data Acquisition Strategy

**Document Version:** 1.0  
**Date:** November 30, 2025  
**Status:** Design Phase

---

## 1. Model Architecture Overview

### Multi-Modal Sensor Fusion Approach

DrainSentinel employs a **multi-modal deep learning architecture** that fuses three independent data streams into a unified inference pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                    DrainSentinel Model                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Visual     │  │   Distance   │  │  Environmental
│  │   Stream     │  │   Stream     │  │  Stream      │      │
│  │              │  │              │  │              │      │
│  │  Camera      │  │  Ultrasonic/ │  │  DHT22/      │      │
│  │  (1600x1200) │  │  Lidar       │  │  BMP280/     │      │
│  │              │  │  Sensor      │  │  Rain Sensor │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  MobileNetV2 │  │  1D CNN/LSTM │  │  Random      │      │
│  │  (Blockage   │  │  (Water Level│  │  Forest      │      │
│  │  Detection)  │  │  Monitoring) │  │  (Flood Risk)│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           ▼                                 │
│                   ┌──────────────────┐                      │
│                   │  Fusion Layer    │                      │
│                   │  (Concatenate +  │                      │
│                   │   Dense Layer)   │                      │
│                   └────────┬─────────┘                      │
│                            ▼                                │
│                   ┌──────────────────┐                      │
│                   │  Output Layer    │                      │
│                   │  (Alert Decision)│                      │
│                   └──────────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Stream 1: Visual Blockage Detection

### Input Specification
- **Source:** OV2640 Camera on ESP32-S3
- **Resolution:** 1600x1200 pixels (raw capture)
- **Processing:** Resize to 96x96 for model input
- **Color Space:** RGB
- **Frame Rate:** 1 FPS (to conserve power)
- **Preprocessing:** Normalization (0-1 range), augmentation during training

### Model Architecture: MobileNetV2
- **Type:** Convolutional Neural Network (CNN)
- **Backbone:** MobileNetV2 (lightweight, optimized for edge)
- **Input Shape:** 96x96x3
- **Output Classes:** 2 (blockage/no blockage) or 10+ (debris types)
- **Quantization:** INT8 for edge deployment
- **Model Size:** ~3-5 MB (fits in ESP32-S3 memory)
- **Inference Latency:** 200-500 ms per frame

### Training Data
- **Dataset:** S-BIRD + Pipe Inspection (CC BY 4.0)
- **Total Images:** ~1,000-2,000 (after filtering for blockage-relevant samples)
- **Augmentation:** Rotation (±15°), brightness (±20%), contrast (±20%), horizontal flip
- **Train/Val/Test Split:** 70% / 15% / 15%
- **Imbalance Handling:** Weighted loss function or oversampling

### Detection Classes
1. **No Blockage** - Clear drain, normal water flow
2. **Partial Blockage** - Debris present, flow restricted
3. **Complete Blockage** - Drain fully obstructed
4. **Debris Type** - Leaves, plastic, sediment, grease, etc.

### Edge Impulse Configuration
```
Input Block: Camera
  - Resolution: 96x96
  - Color Depth: RGB

Processing Block: Image
  - Scaling: 0-1 (normalized)
  - Squashing: Enabled

Learning Block: Transfer Learning (MobileNetV2)
  - Epochs: 100
  - Batch Size: 32
  - Learning Rate: 0.001
  - Dropout: 0.2
  - Output: Softmax (classification)
```

---

## 3. Stream 2: Water Level Monitoring (Distance Sensors)

### Input Specification
- **Sensors:** HC-SR04 Ultrasonic OR VL53L0X Lidar
- **Measurement Range:** 2-400 cm (ultrasonic) or 30-1000 mm (Lidar)
- **Sampling Rate:** 1 Hz (1 measurement per second)
- **Data Format:** Distance in centimeters (float)
- **Time Window:** 60-second rolling window (60 samples)
- **Preprocessing:** Smoothing (moving average), normalization

### Model Architecture: 1D CNN + LSTM
- **Type:** Recurrent Neural Network (RNN) with temporal convolution
- **Input Shape:** (60, 1) - 60 timesteps, 1 feature
- **Layers:**
  1. Conv1D: 32 filters, kernel=3, ReLU
  2. MaxPooling1D: pool=2
  3. Conv1D: 64 filters, kernel=3, ReLU
  4. LSTM: 32 units, return_sequences=True
  5. LSTM: 16 units
  6. Dense: 32, ReLU
  7. Dense: 3, Softmax (output)
- **Output Classes:** 3 (normal/elevated/critical water level)
- **Model Size:** ~1-2 MB
- **Inference Latency:** 50-100 ms

### Training Data
- **Dataset:** Water Level Identification with Distance Sensors (Kaggle, CC BY-SA 4.0)
- **Features:** Distance measurements over time
- **Labels:** Water level categories (normal, elevated, critical)
- **Synthetic Data:** Generate time-series patterns for different blockage scenarios
- **Train/Val/Test Split:** 70% / 15% / 15%

### Water Level Thresholds
- **Normal:** 0-30 cm (healthy drainage)
- **Elevated:** 31-60 cm (warning level)
- **Critical:** >60 cm (blockage/flooding risk)

### Edge Impulse Configuration
```
Input Block: Time Series Data
  - Frequency: 1 Hz
  - Length: 60 seconds (60 samples)
  - Axes: 1 (distance)

Processing Block: Time Series
  - Scaling: 0-1 (normalized)

Learning Block: Neural Network (LSTM)
  - Epochs: 100
  - Batch Size: 32
  - Learning Rate: 0.001
  - Output: Softmax (3 classes)
```

---

## 4. Stream 3: Flood Prediction (Environmental Sensors)

### Input Specification
- **Sensors:**
  - DHT22: Temperature (°C), Humidity (%)
  - BMP280: Atmospheric Pressure (hPa), Altitude (m)
  - Rain Sensor: Rainfall (mm/hour)
  - Water Level: From distance sensor (cm)
- **Sampling Rate:** 1 measurement per minute
- **Data Format:** Tabular (5 features)
- **Preprocessing:** Normalization (0-1), missing value handling

### Model Architecture: Random Forest / Gradient Boosting
- **Type:** Ensemble learning (tree-based)
- **Algorithm:** XGBoost or LightGBM (optimized for edge)
- **Input Features:** 5 (temperature, humidity, pressure, rainfall, water level)
- **Output:** Flood risk score (0-100) or binary classification (flood/no flood)
- **Model Size:** ~0.5-1 MB
- **Inference Latency:** 20-50 ms

### Training Data
- **Source:** Synthetic data generation from historical weather patterns in Lagos
- **Features:**
  - Temperature: 20-35°C (typical Lagos range)
  - Humidity: 40-95%
  - Atmospheric Pressure: 1000-1020 hPa
  - Rainfall: 0-100 mm/hour
  - Water Level: 0-100 cm
- **Labels:** Flood risk (0-100) based on domain knowledge
- **Train/Val/Test Split:** 70% / 15% / 15%

### Flood Risk Calculation
```
Flood Risk Score = w1 * water_level_risk + w2 * rainfall_risk + 
                   w3 * pressure_risk + w4 * humidity_risk + 
                   w5 * temperature_risk

Where:
- w1 = 0.40 (water level is primary indicator)
- w2 = 0.30 (rainfall is secondary)
- w3 = 0.15 (atmospheric pressure)
- w4 = 0.10 (humidity)
- w5 = 0.05 (temperature)

Alert Threshold: Risk Score > 70
```

### Edge Impulse Configuration
```
Input Block: Tabular Data
  - Features: 5
  - Sampling: 1 per minute

Processing Block: Standardization
  - Method: Z-score normalization

Learning Block: Gradient Boosting
  - Algorithm: XGBoost
  - Trees: 50
  - Max Depth: 5
  - Learning Rate: 0.1
  - Output: Regression (0-100) or Classification
```

---

## 5. Data Acquisition Strategy

### Phase 1: Dataset Collection and Preparation

#### Visual Data Collection
1. **Download S-BIRD Dataset**
   - Source: MDPI Sensors (2023)
   - Method: Contact authors or access through research repositories
   - Processing: Filter for blockage-relevant images

2. **Download Pipe Inspection Dataset**
   - Source: Roboflow Universe
   - Method: Direct download from https://universe.roboflow.com/pipe/pipe-inspection
   - Processing: Extract annotations and images

3. **Data Augmentation**
   - Rotation: ±15 degrees
   - Brightness: ±20%
   - Contrast: ±20%
   - Horizontal flip: 50% probability
   - Gaussian noise: σ=0.01

#### Distance Sensor Data Collection
1. **Download Water Level Dataset**
   - Source: Kaggle
   - Method: Direct download from https://www.kaggle.com/datasets/caetanoranieri/water-level-identification-with-lidar
   - Features: Extract ultrasonic and Lidar measurements

2. **Synthetic Data Generation**
   - Simulate normal drainage patterns
   - Simulate blockage scenarios (gradual water level rise)
   - Simulate rapid water level changes (heavy rainfall)

#### Environmental Data Collection
1. **Historical Weather Data**
   - Source: NOAA, OpenWeatherMap, or local Lagos weather stations
   - Period: 5+ years of historical data
   - Features: Temperature, humidity, pressure, rainfall

2. **Synthetic Flood Scenarios**
   - Combine weather patterns with water level data
   - Generate labeled datasets for training

### Phase 2: Data Preprocessing

#### Visual Data Preprocessing
```python
1. Load image
2. Resize to 96x96
3. Normalize to [0, 1]
4. Apply augmentation (training only)
5. Convert to Edge Impulse format
```

#### Time-Series Data Preprocessing
```python
1. Load sensor readings
2. Create 60-second rolling windows
3. Normalize to [0, 1]
4. Handle missing values (interpolation)
5. Convert to Edge Impulse format
```

#### Tabular Data Preprocessing
```python
1. Load weather + sensor data
2. Align timestamps
3. Normalize each feature to [0, 1]
4. Handle missing values (forward fill)
5. Create labels based on flood risk rules
6. Convert to Edge Impulse format
```

### Phase 3: Edge Impulse Project Setup

#### Project Structure
```
DrainSentinel (Edge Impulse Project)
├── Visual Blockage Detection
│   ├── Training Data (800 images)
│   ├── Test Data (200 images)
│   └── Model: MobileNetV2
├── Water Level Monitoring
│   ├── Training Data (1000 sequences)
│   ├── Test Data (300 sequences)
│   └── Model: 1D CNN + LSTM
└── Flood Prediction
    ├── Training Data (5000 samples)
    ├── Test Data (1500 samples)
    └── Model: XGBoost
```

#### Data Upload Strategy
1. Upload visual data with labels (blockage/no blockage)
2. Upload time-series data with 60-second windows
3. Upload tabular data with flood risk labels
4. Configure impulse with three parallel learning blocks
5. Add fusion layer to combine outputs

---

## 6. Model Integration and Deployment

### Inference Pipeline on ESP32-S3

```
┌─────────────────────────────────────────────────────────────┐
│                   ESP32-S3 Runtime                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Capture Camera Frame (1600x1200)                        │
│     └─> Resize to 96x96                                    │
│         └─> Visual Model Inference (200-500ms)             │
│             └─> Blockage Score (0-1)                       │
│                                                               │
│  2. Read Ultrasonic/Lidar Sensor (1 Hz)                    │
│     └─> Accumulate 60 samples (60 seconds)                │
│         └─> Distance Stream Model Inference (50-100ms)     │
│             └─> Water Level Class (0-2)                    │
│                                                               │
│  3. Read Environmental Sensors (1 per minute)              │
│     └─> Normalize Features                                 │
│         └─> Flood Prediction Model Inference (20-50ms)     │
│             └─> Flood Risk Score (0-100)                   │
│                                                               │
│  4. Fusion Logic                                            │
│     └─> Combine three outputs                              │
│         └─> Generate Alert Decision                        │
│             └─> Transmit Alert via Wi-Fi (if needed)       │
│                                                               │
│  5. Logging                                                 │
│     └─> Store results in local flash memory                │
│         └─> Sync to cloud (optional)                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Decision Logic
```
IF (blockage_score > 0.7 AND water_level_class == CRITICAL) THEN
    alert_level = HIGH
    message = "CRITICAL: Drainage blockage detected with high water level"
ELSE IF (blockage_score > 0.5 OR water_level_class == ELEVATED) THEN
    alert_level = MEDIUM
    message = "WARNING: Potential drainage blockage or elevated water level"
ELSE IF (flood_risk_score > 70) THEN
    alert_level = MEDIUM
    message = "WARNING: Flood risk predicted based on weather patterns"
ELSE
    alert_level = LOW
    message = "OK: Drainage system normal"
END IF
```

---

## 7. Performance Targets

### Visual Model
- **Accuracy:** >85% on test set
- **Precision:** >80% (minimize false positives)
- **Recall:** >80% (minimize false negatives)
- **Latency:** <500 ms per frame
- **Model Size:** <5 MB

### Distance Sensor Model
- **Accuracy:** >90% on test set
- **Latency:** <100 ms per inference
- **Model Size:** <2 MB

### Flood Prediction Model
- **Accuracy:** >85% on test set
- **Latency:** <50 ms per inference
- **Model Size:** <1 MB

### Overall System
- **Total Inference Time:** <1 second (all three models)
- **Power Consumption:** <50 mA during inference
- **Uptime:** >99% (24/7 operation)

---

## 8. Validation Strategy

### Cross-Validation
- **K-Fold:** 5-fold cross-validation on training data
- **Stratified Split:** Ensure class balance in folds

### Test Set Evaluation
- **Independent Test Set:** 15% of total data
- **Metrics:** Accuracy, Precision, Recall, F1-Score, Confusion Matrix
- **Visualization:** ROC curves, precision-recall curves

### Real-World Testing
- **Field Deployment:** Test on actual drainage systems in Lagos
- **Comparison:** Validate against manual inspection results
- **Iteration:** Refine model based on field performance

---

## 9. References

1. **MobileNetV2:** Sandler, M., et al. (2018). MobileNetV2: Inverted Residuals and Linear Bottlenecks. CVPR 2018.

2. **LSTM for Time Series:** Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. Neural Computation, 9(8), 1735-1780.

3. **XGBoost:** Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. KDD 2016.

4. **Edge Impulse Documentation:** https://docs.edgeimpulse.com/

5. **Sensor Fusion:** Durrant-Whyte, H., & Bailey, T. (2006). Simultaneous Localization and Mapping: Part I. IEEE Robotics & Automation Magazine, 13(2), 99-110.

---

**Status:** Architecture Design Complete  
**Next Phase:** Dataset Preparation and Preprocessing
