"""
DrainSentinel Synthetic Data Generation Script
Generates training data for all three model streams:
1. Visual blockage detection
2. Water level monitoring
3. Flood prediction
"""

import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Create output directories
Path("data/visual").mkdir(parents=True, exist_ok=True)
Path("data/sensor").mkdir(parents=True, exist_ok=True)
Path("data/environmental").mkdir(parents=True, exist_ok=True)

print("DrainSentinel: Synthetic Data Generation")
print("=" * 50)

# ============================================================================
# 1. VISUAL DATA METADATA (for reference - actual images from S-BIRD/Pipe)
# ============================================================================
print("\n[1] Generating Visual Data Metadata...")

visual_metadata = {
    "dataset": "S-BIRD + Pipe Inspection (CC BY 4.0)",
    "total_images": 1000,
    "classes": {
        "no_blockage": {"count": 500, "description": "Clear drain, normal flow"},
        "partial_blockage": {"count": 300, "description": "Debris present, flow restricted"},
        "complete_blockage": {"count": 200, "description": "Drain fully obstructed"}
    },
    "image_specs": {
        "resolution": "96x96",
        "color_space": "RGB",
        "format": "PNG"
    },
    "augmentation": {
        "rotation": "±15°",
        "brightness": "±20%",
        "contrast": "±20%",
        "flip": "50%"
    }
}

with open("data/visual/metadata.json", "w") as f:
    json.dump(visual_metadata, f, indent=2)

print(f"  ✓ Visual metadata saved")
print(f"    - Total images: {visual_metadata['total_images']}")
print(f"    - Classes: {list(visual_metadata['classes'].keys())}")

# ============================================================================
# 2. WATER LEVEL SENSOR DATA (Time-series)
# ============================================================================
print("\n[2] Generating Water Level Time-Series Data...")

def generate_water_level_sequence(scenario="normal", noise_level=0.5):
    """Generate 60-second water level measurement sequence"""
    samples = 60  # 1 Hz sampling for 60 seconds
    
    if scenario == "normal":
        # Stable water level around 20cm
        base = np.random.normal(20, 2, samples)
        label = 0  # Normal
    elif scenario == "elevated":
        # Gradually rising water level (30-50cm)
        base = np.linspace(30, 50, samples) + np.random.normal(0, 2, samples)
        label = 1  # Elevated
    elif scenario == "critical":
        # Rapidly rising water level (50-80cm)
        base = np.linspace(50, 80, samples) + np.random.normal(0, 2, samples)
        label = 2  # Critical
    
    # Add noise and clip to valid range
    data = np.clip(base + np.random.normal(0, noise_level, samples), 0, 100)
    return data, label

# Generate training data
sensor_data = []
labels = []

for scenario, count in [("normal", 500), ("elevated", 300), ("critical", 200)]:
    for _ in range(count):
        data, label = generate_water_level_sequence(scenario)
        sensor_data.append(data.tolist())
        labels.append(label)

# Save as JSON
sensor_dataset = {
    "total_sequences": len(sensor_data),
    "sequence_length": 60,
    "sampling_rate_hz": 1,
    "unit": "centimeters",
    "classes": {
        0: "normal (0-30cm)",
        1: "elevated (31-60cm)",
        2: "critical (>60cm)"
    },
    "data": sensor_data,
    "labels": labels
}

with open("data/sensor/water_level_data.json", "w") as f:
    json.dump(sensor_dataset, f)

print(f"  ✓ Water level data generated")
print(f"    - Total sequences: {len(sensor_data)}")
print(f"    - Sequence length: 60 samples (60 seconds)")
print(f"    - Classes: {sensor_dataset['classes']}")

# ============================================================================
# 3. ENVIRONMENTAL SENSOR DATA (Tabular)
# ============================================================================
print("\n[3] Generating Environmental Sensor Data...")

def calculate_flood_risk(temp, humidity, pressure, rainfall, water_level):
    """Calculate flood risk score based on environmental factors"""
    # Normalize inputs to 0-1 range
    temp_norm = (temp - 15) / 25  # 15-40°C range
    humidity_norm = humidity / 100
    pressure_norm = 1 - ((pressure - 990) / 40)  # Lower pressure = higher risk
    rainfall_norm = min(rainfall / 100, 1.0)  # 0-100 mm/hour
    water_level_norm = min(water_level / 100, 1.0)  # 0-100 cm
    
    # Weighted combination
    risk = (
        0.40 * water_level_norm +
        0.30 * rainfall_norm +
        0.15 * pressure_norm +
        0.10 * humidity_norm +
        0.05 * temp_norm
    )
    
    return min(max(risk * 100, 0), 100)  # Return 0-100

# Generate environmental data
env_data = []
env_labels = []

# Normal conditions (low flood risk)
for _ in range(3000):
    temp = np.random.normal(25, 3)  # 25°C ± 3
    humidity = np.random.normal(60, 10)  # 60% ± 10
    pressure = np.random.normal(1013, 2)  # 1013 hPa ± 2
    rainfall = np.random.exponential(5)  # Low rainfall
    water_level = np.random.normal(20, 5)  # 20cm ± 5
    
    risk = calculate_flood_risk(temp, humidity, pressure, rainfall, water_level)
    
    env_data.append({
        "temperature": float(np.clip(temp, 15, 40)),
        "humidity": float(np.clip(humidity, 0, 100)),
        "pressure": float(np.clip(pressure, 990, 1040)),
        "rainfall": float(np.clip(rainfall, 0, 100)),
        "water_level": float(np.clip(water_level, 0, 100))
    })
    env_labels.append(0 if risk < 40 else 1)

# Heavy rainfall/flooding conditions (high flood risk)
for _ in range(2000):
    temp = np.random.normal(28, 2)  # 28°C ± 2
    humidity = np.random.normal(85, 8)  # 85% ± 8
    pressure = np.random.normal(1000, 3)  # 1000 hPa ± 3 (lower)
    rainfall = np.random.normal(50, 20)  # Heavy rainfall
    water_level = np.random.normal(70, 10)  # 70cm ± 10
    
    risk = calculate_flood_risk(temp, humidity, pressure, rainfall, water_level)
    
    env_data.append({
        "temperature": float(np.clip(temp, 15, 40)),
        "humidity": float(np.clip(humidity, 0, 100)),
        "pressure": float(np.clip(pressure, 990, 1040)),
        "rainfall": float(np.clip(rainfall, 0, 100)),
        "water_level": float(np.clip(water_level, 0, 100))
    })
    env_labels.append(1)

# Save environmental data
env_dataset = {
    "total_samples": len(env_data),
    "features": ["temperature", "humidity", "pressure", "rainfall", "water_level"],
    "feature_units": {
        "temperature": "°C",
        "humidity": "%",
        "pressure": "hPa",
        "rainfall": "mm/hour",
        "water_level": "cm"
    },
    "classes": {
        0: "low_risk (score < 40)",
        1: "high_risk (score >= 40)"
    },
    "data": env_data,
    "labels": env_labels
}

with open("data/environmental/flood_risk_data.json", "w") as f:
    json.dump(env_dataset, f)

print(f"  ✓ Environmental data generated")
print(f"    - Total samples: {len(env_data)}")
print(f"    - Features: {env_dataset['features']}")
print(f"    - Classes: {env_dataset['classes']}")

# ============================================================================
# 4. SUMMARY STATISTICS
# ============================================================================
print("\n[4] Data Summary Statistics...")

print("\n  Visual Data:")
print(f"    - No Blockage: {visual_metadata['classes']['no_blockage']['count']} images")
print(f"    - Partial Blockage: {visual_metadata['classes']['partial_blockage']['count']} images")
print(f"    - Complete Blockage: {visual_metadata['classes']['complete_blockage']['count']} images")

print("\n  Water Level Data:")
print(f"    - Normal: {sum(1 for l in labels if l == 0)} sequences")
print(f"    - Elevated: {sum(1 for l in labels if l == 1)} sequences")
print(f"    - Critical: {sum(1 for l in labels if l == 2)} sequences")

print("\n  Environmental Data:")
print(f"    - Low Risk: {sum(1 for l in env_labels if l == 0)} samples")
print(f"    - High Risk: {sum(1 for l in env_labels if l == 1)} samples")

# ============================================================================
# 5. EDGE IMPULSE IMPORT GUIDE
# ============================================================================
print("\n[5] Edge Impulse Import Instructions...")

import_guide = """
EDGE IMPULSE IMPORT GUIDE
========================

1. Visual Blockage Detection:
   - Create new Edge Impulse project
   - Upload images from S-BIRD and Pipe Inspection datasets
   - Label as: no_blockage, partial_blockage, complete_blockage
   - Create impulse with:
     * Input block: Camera (96x96)
     * Learning block: Transfer Learning (MobileNetV2)

2. Water Level Monitoring:
   - Create time-series learning block
   - Upload water_level_data.json
   - Configure as:
     * Input: Time series (60 samples @ 1 Hz)
     * Learning block: Neural Network (LSTM)
     * Output: Classification (3 classes)

3. Flood Prediction:
   - Create tabular learning block
   - Upload flood_risk_data.json
   - Configure as:
     * Input: Tabular data (5 features)
     * Learning block: Gradient Boosting
     * Output: Classification (2 classes)

4. Model Fusion:
   - Create custom impulse combining all three
   - Export as C++ library for ESP32-S3
   - Integrate into firmware
"""

with open("data/EDGE_IMPULSE_GUIDE.txt", "w") as f:
    f.write(import_guide)

print(import_guide)

print("\n" + "=" * 50)
print("✓ Synthetic data generation complete!")
print(f"  Output directory: {os.path.abspath('data/')}")
print("=" * 50)
