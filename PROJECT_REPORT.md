# DrainSentinel: Technical Project Report

**Project Name:** DrainSentinel v2.0  
**Team:** ClimatrixAI  
**Date:** February 2026  
**Location:** Lagos, Nigeria

---

## Executive Summary

DrainSentinel is an edge AI-powered drainage monitoring system designed to detect blockages and predict flooding in Lagos, Nigeria. The system uses computer vision and ultrasonic sensing to provide real-time monitoring and early warning alerts, enabling preventive action before flooding occurs.

**Key Results:**
- Real-time blockage detection with ~87% accuracy
- Water level monitoring with ±3mm precision
- Alert latency < 10 seconds from detection to notification
- 24/7 autonomous operation without cloud dependency

---

## 1. Problem Statement

### 1.1 The Challenge

Lagos, Nigeria experiences frequent flooding due to:
- **Blocked drainage systems** — debris, trash, and sediment accumulate
- **Inadequate monitoring** — manual inspection covers only 15% of network
- **Reactive response** — authorities respond after flooding, not before
- **Climate change** — increasingly intense rainfall events

**Impact:**
- 2-3 major flooding events per year
- Property damage in millions of Naira
- Health risks from contaminated flood water
- Economic disruption and lost productivity
- Loss of life in severe cases

### 1.2 Current Solutions and Limitations

| Current Approach | Limitation |
|------------------|------------|
| Manual inspection | Slow, expensive, covers <15% of drains |
| Citizen reports | Reactive, inconsistent quality |
| Fixed sensors | Expensive, no visual confirmation |
| CCTV monitoring | Requires human operators 24/7 |

### 1.3 Our Opportunity

An AI-powered edge device that:
- Monitors continuously (24/7)
- Detects blockages automatically
- Predicts flooding before it happens
- Alerts authorities and residents
- Operates without cloud dependency

---

## 2. Solution Architecture

### 2.1 System Overview

DrainSentinel combines visual AI with ultrasonic sensing to provide comprehensive drainage monitoring.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DRAINSENTINEL SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐      ┌─────────────────────────────────────┐  │
│  │ USB Camera  │─────►│                                     │  │
│  │ (1080p)     │      │      METIS AI ACCELERATOR           │  │
│  └─────────────┘      │                                     │  │
│                       │  • Visual Blockage Detection (CNN)  │  │
│  ┌─────────────┐      │  • Sensor Fusion & Risk Scoring     │  │
│  │ Arduino     │─────►│  • Alert Decision Engine            │  │
│  │ Uno Rev 4   │ USB  │  • Web Dashboard Server             │  │
│  │ + HC-SR04   │      │                                     │  │
│  └─────────────┘      └──────────────┬──────────────────────┘  │
│                                      │                          │
│                                      │ WiFi                     │
│                                      ▼                          │
│                       ┌─────────────────────────────────────┐  │
│                       │  OUTPUTS                            │  │
│                       │  • Web Dashboard                    │  │
│                       │  • SMS/WhatsApp Alerts              │  │
│                       │  • Sonoff Relay → Pump/Siren        │  │
│                       └─────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Hardware Components

| Component | Model | Purpose | Cost |
|-----------|-------|---------|------|
| Edge Compute | Metis AI Accelerator | Run AI models, host dashboard | Provided |
| Camera | USB 1080p | Visual blockage detection | ~$20 |
| Sensor Hub | Arduino Uno Rev 4 | Read ultrasonic sensor | ~$25 |
| Water Sensor | HC-SR04 | Measure water level | ~$2 |
| Relay | Sonoff Pro R3 | Control pump/siren | ~$15 |
| Storage | MicroSD 32GB | OS and data storage | ~$10 |

**Total Hardware Cost:** ~$72 (excluding Metis)

### 2.3 Software Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Operating System | Raspberry Pi OS (64-bit) | Linux base |
| AI Framework | Edge Impulse / OpenCV | Blockage detection |
| Backend | Python 3 + Flask | Application server |
| Frontend | HTML/CSS/JavaScript | Dashboard UI |
| Communication | PySerial | Arduino data link |
| Alerts | Twilio / Requests | SMS and webhook |

---

## 3. Implementation Details

### 3.1 Visual Blockage Detection

**Model Architecture:** MobileNetV2-based classifier

**Input:**
- 224×224 RGB images from USB camera
- Captured every 5 seconds

**Output Classes:**
- `clear` — No blockage detected
- `partial_blockage` — Some debris visible
- `full_blockage` — Drain significantly blocked

**Training:**
- Dataset: S-BIRD sewer imagery + custom local images
- Augmentation: Rotation, brightness, contrast variations
- Training platform: Edge Impulse Studio

**Performance:**
| Metric | Value |
|--------|-------|
| Accuracy | 87% |
| Precision | 85% |
| Recall | 86% |
| Inference Time | ~150ms |

### 3.2 Water Level Monitoring

**Sensor:** HC-SR04 Ultrasonic

**Specifications:**
- Range: 2-400 cm
- Precision: ±3mm
- Beam angle: 15°

**Arduino Processing:**
- Sample rate: 1 Hz
- 5-sample rolling average (noise reduction)
- JSON output via USB serial

**Calibration:**
- Empty level: Distance when drain is empty (0%)
- Critical level: Distance when flooding imminent (100%)
- Automatic percentage calculation

### 3.3 Risk Scoring Algorithm

The system fuses visual and sensor data to calculate flood risk:

```python
risk_score = (
    0.40 × blockage_confidence +
    0.30 × water_level_percent / 100 +
    0.20 × rate_of_rise / 10 +
    0.10 × weather_factor
)

Alert Level:
- GREEN:  risk_score < 0.30
- YELLOW: risk_score < 0.50
- ORANGE: risk_score < 0.70
- RED:    risk_score >= 0.70
```

**Factors:**
- **Blockage confidence:** AI model output (0-1)
- **Water level percent:** From ultrasonic sensor (0-100%)
- **Rate of rise:** cm/minute over last 60 seconds
- **Weather factor:** Optional API integration

### 3.4 Alert System

**Channels:**
1. **Web Dashboard** — Real-time status display
2. **Console/Log** — System logging
3. **SMS** — Via Twilio API
4. **Webhook** — For integration with other systems
5. **Relay** — Physical trigger for pump/siren

**Rate Limiting:**
| Alert Level | Minimum Interval |
|-------------|------------------|
| GREEN | 60 minutes |
| YELLOW | 15 minutes |
| ORANGE | 5 minutes |
| RED | 1 minute |

---

## 4. Results and Validation

### 4.1 Laboratory Testing

**Test Setup:**
- Controlled water tank
- Simulated blockages (debris, plastic, leaves)
- 100+ test scenarios

**Results:**

| Scenario | Detection Rate | False Positive Rate |
|----------|----------------|---------------------|
| Clear drain | 95% | 5% |
| Partial blockage | 84% | 8% |
| Full blockage | 91% | 3% |
| Rising water | 98% | 2% |

### 4.2 Field Testing

**Location:** Test drain in Lagos (Ikeja area)  
**Duration:** 72 hours continuous operation

**Observations:**
- System operated 24/7 without failure
- Detected 3 natural partial blockages
- Water level readings matched manual measurements (±5%)
- Dashboard accessible from mobile devices
- Power consumption: ~8W average

### 4.3 Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| Detection accuracy | >80% | 87% |
| Alert latency | <30s | <10s |
| Uptime | >95% | 99.2% |
| Power consumption | <15W | 8W |
| Cost per unit | <$150 | $72 |

---

## 5. Challenges and Solutions

### Challenge 1: Variable Lighting Conditions

**Problem:** Camera accuracy degraded in low light

**Solution:**
- Added exposure compensation in OpenCV
- Trained model on varied lighting conditions
- Recommended external light source for deployment

### Challenge 2: Sensor Noise

**Problem:** Ultrasonic readings fluctuated ±10cm

**Solution:**
- Implemented 5-sample rolling average on Arduino
- Added outlier rejection (values >2σ from mean)
- Reduced effective noise to ±2cm

### Challenge 3: Serial Communication Reliability

**Problem:** Occasional data corruption over USB serial

**Solution:**
- JSON format with validation
- Timeout handling in Python
- Automatic reconnection on failure

### Challenge 4: Edge AI Performance

**Problem:** Initial model too slow for real-time

**Solution:**
- Switched to MobileNetV2 (optimized for edge)
- Quantized to INT8
- Reduced input size to 224×224
- Achieved <200ms inference

---

## 6. Future Improvements

### Short-term (1-3 months)
- [ ] Weather API integration for predictive alerts
- [ ] Multi-camera support
- [ ] Mobile app for notifications
- [ ] Historical data visualization

### Medium-term (3-6 months)
- [ ] Solar power option
- [ ] LoRa connectivity for remote areas
- [ ] Mesh network of multiple units
- [ ] Integration with LASEMA systems

### Long-term (6-12 months)
- [ ] City-wide deployment
- [ ] Predictive maintenance scheduling
- [ ] AI model retraining pipeline
- [ ] Public flood risk dashboard

---

## 7. Conclusion

DrainSentinel demonstrates that effective flood prevention is achievable with affordable edge AI technology. By combining visual detection with water level sensing, the system provides comprehensive drainage monitoring that can:

1. **Detect blockages** before they cause flooding
2. **Measure water levels** in real-time
3. **Predict flooding** based on multiple factors
4. **Alert stakeholders** within seconds
5. **Operate autonomously** 24/7

The total hardware cost of ~$72 per unit makes city-wide deployment economically feasible, potentially preventing millions of Naira in flood damage annually.

---

## 8. References

1. Edge Impulse Documentation: https://docs.edgeimpulse.com/
2. OpenCV Python Documentation: https://docs.opencv.org/
3. HC-SR04 Datasheet: https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf
4. S-BIRD Dataset: Patil, R.R., et al. (2023). MDPI Sensors, 23(6), 2966.
5. Lagos Flooding Statistics: LASEMA Annual Reports

---

## Appendix A: Bill of Materials

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| Metis AI Accelerator | 1 | Provided | - |
| USB Camera 1080p | 1 | $20 | $20 |
| Arduino Uno Rev 4 | 1 | $25 | $25 |
| HC-SR04 Sensor | 1 | $2 | $2 |
| Sonoff Pro R3 | 1 | $15 | $15 |
| MicroSD 32GB | 1 | $10 | $10 |
| Jumper Wires | 1 set | $3 | $3 |
| Waterproof Enclosure | 1 | $15 | $15 |
| **Total** | | | **$90** |

## Appendix B: Source Code Repository

GitHub: https://github.com/farouqfahm/DrainSentinel1.0

Key files:
- `src/main.py` — Main application entry point
- `src/camera.py` — Camera capture module
- `src/arduino_serial.py` — Arduino communication
- `src/ai_detector.py` — AI inference module
- `src/alert_system.py` — Alert handling
- `src/dashboard.py` — Web dashboard
- `hardware/arduino_sensor.ino` — Arduino firmware

---

*Report prepared by ClimatrixAI Team*  
*February 2026*
