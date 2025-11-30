# DrainSentinel: Edge AI for Flood Prevention
## Project Scope and Research Summary

**Project Name:** DrainSentinel  
**Submission Track:** Edge AI Applications  
**Target Region:** Lagos, Nigeria  
**Date:** November 30, 2025

---

## 1. Project Overview

DrainSentinel is an IoT Edge AI application designed to monitor drainage systems and waterways in Lagos, Nigeria, detecting blockages and predicting flood occurrences in real-time. The system operates 24/7 at the edge, using computer vision and sensor fusion (ultrasonic/Lidar) data to identify drainage blockages and alert the community and relevant agencies before flooding occurs.

### Key Objectives

- **Real-time Blockage Detection:** Identify drainage blockages using visual and distance sensor data
- **Flood Prediction:** Monitor water levels and predict flood risk based on multiple environmental indices
- **Community Alerts:** Notify residents and government agencies of potential flooding threats
- **Edge Deployment:** Run inference locally on edge hardware without cloud dependency
- **24/7 Monitoring:** Continuous operation with minimal power consumption

---

## 2. Hardware Selection

### Selected Platform: **Seeed XIAO ESP32-S3 Sense**

**Rationale:**
- Integrated camera (1600x1200 resolution) for visual data capture
- Dual-core ESP32-S3 processor with sufficient compute for Edge Impulse models
- Native Edge Impulse support with pre-built SDKs
- Low power consumption suitable for continuous operation
- Compact form factor for deployment in drainage systems
- Built-in Wi-Fi and BLE for connectivity and alerts
- Cost-effective for mass deployment across Lagos

**Specifications:**
- Processor: Dual-core Xtensa 32-bit LX7 @ 240 MHz
- Memory: 8 MB PSRAM, 8 MB Flash
- Camera: OV2640 (1600x1200 pixels)
- Sensors: Built-in IMU (BMI270), magnetometer (BMM150)
- Connectivity: 2.4 GHz Wi-Fi, Bluetooth 5.3
- Power: 3.7V Li-Po battery support

### Sensor Integration

**Visual Data:**
- Built-in OV2640 camera for blockage detection (debris, water level changes)

**Distance Sensors (Ultrasonic/Lidar):**
- HC-SR04 Ultrasonic Sensor (budget-friendly, 2-400 cm range)
- VL53L0X Lidar Sensor (optional, more accurate, 30-1000 mm range)
- Both sensors communicate via I2C or GPIO, compatible with ESP32-S3

**Environmental Sensors (Weather Station):**
- DHT22: Temperature and humidity
- BMP280: Atmospheric pressure and altitude
- Rain sensor: Detect precipitation

---

## 3. Datasets and Licensing

### Visual Dataset: **Sewer-ML**

**Source:** Aalborg University, Denmark  
**License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)  
**Availability:** https://vap.aau.dk/sewer-ml/  
**Size:** 1.3 million images from 75,618 videos  
**Content:** Professional sewer inspection videos with 16 defect categories

**Limitation:** CC BY-NC-SA 4.0 is **not permissive for commercial use** without explicit permission from the authors.

### Visual Dataset: **S-BIRD (Sewer-Blockages Imagery Recognition Dataset)**

**Source:** University of Tromsø, Norway  
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)  
**Availability:** Published in MDPI Sensors (2023)  
**Content:** Multi-class imagery dataset specifically for sewer blockage detection  
**Advantage:** CC BY 4.0 is permissive and allows commercial use with attribution

### Visual Dataset: **Pipe Inspection Object Detection Dataset**

**Source:** Roboflow Universe  
**License:** Creative Commons Attribution 4.0 (CC BY 4.0)  
**Availability:** https://universe.roboflow.com/pipe/pipe-inspection  
**Size:** 538 images with 10 object detection classes  
**Classes:** Alligator crack, block crack, crack, diagonal crack, hairline crack, longitudinal crack, rust, transverse crack, void, wide crack

### Sensor Data: **Water Level Identification with Distance Sensors**

**Source:** Kaggle (Caetano Ranieri et al.)  
**License:** CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0)  
**Availability:** https://www.kaggle.com/datasets/caetanoranieri/water-level-identification-with-lidar  
**Content:** Synchronized data from LiDAR, ultrasonic sensors, and IMU  
**Use Case:** Water level identification and sensor fusion techniques  
**Citation:** Ranieri, C.M., et al. (2024). Water level identification with laser sensors, inertial units, and machine learning. Engineering Applications of Artificial Intelligence, 127, 107235.

---

## 4. Model Architecture

### Multi-Modal Approach

The Edge Impulse model will integrate three data streams:

1. **Visual Stream (CNN):** Detect blockage indicators (debris, water level anomalies)
2. **Ultrasonic Stream (Time-Series):** Monitor water level changes and flow patterns
3. **Sensor Fusion Stream (IMU/Environmental):** Combine weather data for flood prediction

### Model Design

**Phase 1: Visual Blockage Detection**
- Input: Camera frames (1600x1200 → resized to 96x96 for efficiency)
- Architecture: MobileNetV2 or EfficientNet (optimized for edge)
- Output: Classification (blockage/no blockage) or object detection (debris location)
- Latency Target: <500ms per inference

**Phase 2: Water Level Monitoring**
- Input: Ultrasonic/Lidar distance measurements (time-series)
- Architecture: 1D CNN or LSTM for temporal pattern recognition
- Output: Water level classification (normal/elevated/critical)
- Latency Target: <100ms per inference

**Phase 3: Flood Prediction**
- Input: Sensor fusion (temperature, humidity, pressure, rainfall, water level)
- Architecture: Gradient boosting or random forest (via Edge Impulse)
- Output: Flood risk score (0-100) and alert threshold
- Latency Target: <50ms per inference

---

## 5. Edge Impulse Workflow

### Data Preparation
1. Download S-BIRD and Pipe Inspection datasets from open sources
2. Preprocess images: resize, normalize, augment
3. Collect real-world ultrasonic/Lidar data from test deployments
4. Combine sensor readings with environmental data

### Model Training
1. Create Edge Impulse project for DrainSentinel
2. Upload datasets with proper attribution
3. Configure impulse with visual and sensor fusion blocks
4. Train and optimize for ESP32-S3 target
5. Validate model performance on test data

### Deployment
1. Export model as C++ library
2. Integrate into ESP32-S3 firmware
3. Implement alert logic and connectivity
4. Deploy to edge hardware

---

## 6. Application Features

### Core Functionality
- **Real-time Inference:** Run Edge Impulse model on device
- **Multi-Sensor Fusion:** Combine visual and distance sensor data
- **Alert System:** Notify community via Wi-Fi/cellular when blockage detected
- **Data Logging:** Store inference results locally for analysis
- **Low Power Mode:** Adaptive sampling to extend battery life

### Communication
- Wi-Fi connectivity for alert transmission
- Optional cloud sync for historical analysis
- Local API for integration with municipal systems

### User Interface
- Web dashboard for monitoring deployed devices
- Real-time alert notifications
- Historical data visualization
- Device management and configuration

---

## 7. Competition Compliance

### Mandatory Requirements
- ✅ GitHub repository with complete source code
- ✅ Detailed README with development process documentation
- ✅ Edge Impulse model integration (visual + sensor fusion)
- ✅ Deployment to edge hardware (ESP32-S3)
- ✅ Demonstration (video + technical documentation)
- ✅ Edge Impulse public project with summary and links
- ✅ Proper attribution for all open-source datasets

### Evaluation Criteria
- **Innovation:** Multi-modal sensor fusion for drainage monitoring
- **Technical Execution:** Edge Impulse model optimization for ESP32-S3
- **Impact:** Real-world flood prevention in Lagos
- **Edge Impulse Usage:** Effective model training and deployment
- **Engagement:** Clear documentation and demonstration

---

## 8. Timeline and Deliverables

### Phase 1: Model Development (Week 1-2)
- Dataset preparation and preprocessing
- Edge Impulse model training
- Model optimization and testing

### Phase 2: Application Development (Week 2-3)
- ESP32-S3 firmware development
- Sensor integration and calibration
- Alert system implementation

### Phase 3: Documentation (Week 3-4)
- GitHub repository setup
- README and technical documentation
- Demonstration video creation
- Edge Impulse project publication

### Phase 4: Submission (Week 4)
- Final testing and validation
- Submission package preparation
- Competition submission

---

## 9. References

1. **Sewer-ML Dataset:** Haurum, J.B., et al. (2021). A Multi-Label Sewer Defect Classification Dataset and Benchmark. CVPR 2021. https://vap.aau.dk/sewer-ml/

2. **S-BIRD Dataset:** Patil, R.R., et al. (2023). S-BIRD: A Novel Critical Multi-Class Imagery Dataset for Sewer Monitoring and Maintenance Systems. MDPI Sensors, 23(6), 2966.

3. **Water Level Dataset:** Ranieri, C.M., et al. (2024). Water level identification with laser sensors, inertial units, and machine learning. Engineering Applications of Artificial Intelligence, 127, 107235.

4. **Edge Impulse Documentation:** https://docs.edgeimpulse.com/

5. **Seeed XIAO ESP32-S3 Sense:** https://wiki.seeedstudio.com/xiao_esp32s3_sense/

6. **Drainage Blockage Monitoring:** Navia, M., et al. (2024). IoT-Based Detection of Blockages in Stormwater Drains. MDPI, 82(1), 48.

---

## 10. Next Steps

1. **Set up Edge Impulse project** with multi-modal data ingestion
2. **Prepare datasets** with proper attribution and licensing compliance
3. **Develop ESP32-S3 firmware** with sensor integration
4. **Create demonstration** showcasing real-time blockage detection
5. **Prepare submission documentation** for competition

---

**Project Status:** Scope Definition Complete  
**Last Updated:** November 30, 2025  
**Next Phase:** Model Architecture Design and Dataset Preparation
