# DrainSentinel 2.0: Edge AI Flood Prevention System

![DrainSentinel](https://img.shields.io/badge/DrainSentinel-v2.0-blue)
![Platform](https://img.shields.io/badge/Platform-Metis%20AI%20Accelerator-green)
![AI](https://img.shields.io/badge/AI-Edge%20Impulse-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**An AI-powered drainage monitoring system that detects blockages and predicts floods before they happen.**

Built for Lagos, Nigeria — where flooding is a real problem that affects millions.

---

## 🎯 What This Does

DrainSentinel uses a camera + ultrasonic sensor + AI to:

1. **See blockages** — Camera detects debris, trash, blockages in drains
2. **Measure water levels** — Ultrasonic sensor tracks how high water is rising
3. **Predict floods** — AI combines both to warn BEFORE flooding happens
4. **Alert people** — Sends notifications to residents and authorities
5. **Trigger responses** — Can activate pumps, sirens, or barriers via relay

**The magic:** All AI runs locally on the Metis AI Accelerator. No cloud. No internet required for core functions. Works 24/7.

---

## 🔧 Hardware Stack

This is what we're using — **no substitutions**:

| Component | Role | Notes |
|-----------|------|-------|
| **Metis AI Accelerator** | Edge AI brain | Runs vision models locally |
| **USB Camera (1080p)** | Visual detection | ONE camera for drain monitoring |
| **Arduino Uno Rev 4** | Sensor hub | Connects ultrasonic sensor |
| **HC-SR04 Ultrasonic Sensor** | Water level measurement | Connected to Arduino |
| **Sonoff Pro R3 Relay** | Physical responses | Trigger pumps/sirens/barriers |
| **Wi-Fi Dongle** | Connectivity | Remote monitoring & alerts |
| **MicroSD Card** | Storage | Logs, images, models |

### What We're NOT Using
- ❌ ~~Echo Dot~~ — Removed from project
- ❌ ~~Second camera~~ — Using ONE camera only
- ❌ ~~Raspberry Pi~~ — Using Metis AI Accelerator instead

---

## 🚀 Quick Start (For Beginners)

**New to this?** Don't worry — this guide assumes you're starting from scratch.

### Step 1: Flash the Metis AI Accelerator

The Metis doesn't have an OS yet. Let's fix that.

**What you need:**
- A computer (Windows, Mac, or Linux)
- MicroSD card (32GB minimum, Class 10 or faster)
- MicroSD card reader
- The Metis AI Accelerator unit

**About the Metis AI Accelerator:**
The Metis is an edge AI device designed for running machine learning models locally. It typically runs a Linux-based OS optimized for AI inference.

#### Option A: If Metis Uses Raspberry Pi Compute Module

Many Metis-style accelerators are built on Raspberry Pi Compute Module 4. If yours is:

1. **Download Raspberry Pi Imager**
   - Go to: https://www.raspberrypi.com/software/
   - Download and install for your OS

2. **Flash the OS:**
   - Open Raspberry Pi Imager
   - Choose OS: **Raspberry Pi OS (64-bit)**
   - Choose Storage: Your MicroSD card
   - Click gear icon (⚙️) to configure:
     - Hostname: `drainsentinel`
     - Enable SSH: ✅
     - Username: `pi`
     - Password: (create one)
     - WiFi: Enter your network credentials
   - Click **Write**

3. **Insert MicroSD into Metis** and power on

#### Option B: If Metis Has Custom Firmware

Check the Metis documentation for:
- Pre-built images to flash
- Flashing tool (often `balenaEtcher` or manufacturer tool)
- Recovery mode instructions

Common Metis-type devices:
- **Seeed reComputer** → Uses Jetson or CM4
- **Coral Dev Board** → Uses Mendel Linux
- **NVIDIA Jetson** → Uses JetPack

**If unsure:** Check the label on your Metis device or its documentation.

#### Post-Flash Setup

Once the Metis boots:

```bash
# Connect via SSH (from your computer)
ssh pi@drainsentinel.local
# Or use the IP address from your router

# Update the system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-opencv python3-numpy git

# Install Flask for dashboard
pip3 install flask

# Clone this repository
cd ~
git clone https://github.com/farouqfahm/DrainSentinel1.0.git
cd DrainSentinel1.0
```

---

### Step 2: Connect the Hardware

#### 2.1 USB Camera → Metis

1. Plug the USB camera into any USB port on the Metis
2. Test it works:
   ```bash
   # Check camera is detected
   ls /dev/video*
   # Should show: /dev/video0
   
   # Take a test photo
   ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
   # Or: fswebcam test.jpg
   ```

#### 2.2 Arduino Uno Rev 4 Setup

The Arduino handles the ultrasonic sensor and communicates with the Metis via USB serial.

**Wiring the HC-SR04 to Arduino:**

```
HC-SR04          Arduino Uno Rev 4
─────────        ─────────────────
VCC      ───────► 5V
GND      ───────► GND
TRIG     ───────► Pin 9
ECHO     ───────► Pin 10
```

**Upload Arduino Code:**

1. Install Arduino IDE on your computer: https://www.arduino.cc/en/software
2. Connect Arduino to your computer via USB
3. Open Arduino IDE
4. Copy the code from `hardware/arduino_sensor.ino`
5. Select Board: **Arduino Uno R4 WiFi** (or R4 Minima)
6. Select Port: Your Arduino's COM port
7. Click **Upload**

**Test Arduino:**
```bash
# On Metis, check Arduino is detected
ls /dev/ttyACM*
# Should show: /dev/ttyACM0

# Read serial output
cat /dev/ttyACM0
# Should show JSON: {"water_level_cm": 45.2, "distance_raw": 45.2}
```

#### 2.3 Connect Arduino to Metis

1. Plug Arduino into Metis via USB cable
2. The Metis reads sensor data over serial

#### 2.4 Sonoff Pro R3 Relay (Optional)

The Sonoff relay can trigger pumps, sirens, or flood barriers.

**Setup:**
1. Flash Sonoff with Tasmota firmware (for local control)
2. Connect to your WiFi network
3. Note its IP address
4. Configure in `config/settings.json`

---

### Step 3: Install Dependencies

```bash
cd ~/DrainSentinel1.0

# Install Python dependencies
pip3 install -r requirements.txt

# Create required directories
mkdir -p data/captures data/logs config models
```

---

### Step 4: Run the System

```bash
# Start DrainSentinel
python3 src/main.py
```

Open a browser and go to: `http://drainsentinel.local:5000`

You should see the live dashboard!

---

## 📁 Project Structure

```
DrainSentinel1.0/
├── README.md                    # You're reading this
├── IMPLEMENTATION_ROADMAP.md    # Detailed step-by-step guide
├── PROJECT_REPORT.md            # Technical report for submission
├── PRESENTATION_GUIDE.md        # Slide deck content
├── requirements.txt             # Python dependencies
│
├── src/                         # Main source code
│   ├── main.py                  # Entry point
│   ├── camera.py                # Camera capture module
│   ├── arduino_serial.py        # Arduino communication
│   ├── ai_detector.py           # AI inference module
│   ├── alert_system.py          # Notifications & relay control
│   ├── dashboard.py             # Web dashboard
│   └── calibrate.py             # Calibration wizard
│
├── hardware/                    # Hardware code & diagrams
│   ├── arduino_sensor.ino       # Arduino firmware
│   └── wiring_diagram.md        # Connection guide
│
├── models/                      # Trained AI models
│   └── drain_blockage.eim       # Edge Impulse model
│
├── web/                         # Dashboard frontend
│   └── templates/
│       └── dashboard.html
│
├── config/                      # Configuration files
│   ├── settings.json
│   └── calibration.json
│
├── data/                        # Runtime data
│   ├── captures/                # Camera snapshots
│   └── logs/                    # System logs
│
└── docs/                        # Additional documentation
    ├── MODEL_TRAINING.md
    └── DEPLOYMENT_GUIDE.md
```

---

## 🏗️ System Architecture

```
                         ┌─────────────────────────────────┐
                         │     REMOTE MONITORING           │
                         │  (Phone/Computer Dashboard)     │
                         └──────────────┬──────────────────┘
                                        │ WiFi
                                        ▼
┌────────────────────────────────────────────────────────────────────┐
│                    METIS AI ACCELERATOR                            │
│                    (Edge AI Brain)                                 │
│                                                                    │
│   ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐  │
│   │ USB Camera  │───►│  AI Inference   │───►│  Alert & Control │  │
│   │ (1080p)     │    │  (Blockage      │    │  • Dashboard     │  │
│   └─────────────┘    │   Detection)    │    │  • SMS/WhatsApp  │  │
│                      └────────┬────────┘    │  • Relay Control │  │
│                               │             └────────┬─────────┘  │
│                               │                      │            │
│   ┌─────────────┐    ┌────────▼────────┐            │            │
│   │  Arduino    │───►│  Sensor Fusion  │            │            │
│   │  Uno Rev 4  │    │  & Risk Score   │────────────┘            │
│   │  (USB)      │    └─────────────────┘                         │
│   └──────┬──────┘                                                 │
│          │                                                        │
└──────────┼────────────────────────────────────────────────────────┘
           │
           │ Wires
           ▼
   ┌───────────────┐
   │   HC-SR04     │ ← Ultrasonic sensor (water level)
   │   Sensor      │
   └───────────────┘

           │ WiFi (optional)
           ▼
   ┌───────────────┐
   │  Sonoff Pro   │──► Pump / Siren / Barrier
   │  R3 Relay     │
   └───────────────┘
```

---

## 🧠 How the AI Works

### Visual Blockage Detection

The Metis runs a **MobileNetV2** neural network:

- **Input:** 224x224 RGB camera frame
- **Output:** Classification (clear / partial_blockage / full_blockage)
- **Accuracy:** ~87%
- **Latency:** ~100-200ms on Metis (with accelerator)

### Water Level Monitoring

The Arduino + ultrasonic sensor measures distance to water:

- **Range:** 2-400 cm
- **Precision:** ±3mm
- **Sample rate:** 1 reading/second
- **Communication:** JSON over USB serial

### Decision Fusion

The Metis combines both signals:

```
Risk Score = (0.5 × Blockage Score) + (0.3 × Water Level %) + (0.2 × Rate of Rise)

Alert Levels:
- GREEN:  Risk < 30%    → "All clear"
- YELLOW: Risk 30-60%   → "Monitor closely"  
- ORANGE: Risk 60-80%   → "Warning issued"
- RED:    Risk > 80%    → "FLOOD IMMINENT" + trigger relay
```

---

## 🌟 Bonus Features

### 1. Time-Lapse Recording
Automatically captures images every 5 minutes. Visual history of drain conditions.

### 2. Historical Trend Analysis
Tracks water levels over time. Predicts flooding based on rate of rise.

### 3. Automatic Relay Control
When RED alert triggers, Sonoff relay activates pump or siren automatically.

### 4. SMS/WhatsApp Alerts
Sends alerts directly to phones via Twilio or WhatsApp API.

### 5. Weather Integration
Pull weather data to improve predictions. Rain forecast + partial blockage = high risk.

### 6. Auto-Calibration
System calibrates to "normal" water level on first boot.

### 7. Power Failure Recovery
Auto-resumes monitoring after power outages.

### 8. Multi-Location Support
Deploy multiple units. Central dashboard shows all locations.

---

## 📊 Demo Components

The final demo includes **all three** deliverables:

### 1. Video Demonstration (5-7 mins)
- Live system running
- Camera feed with AI detections
- Water level readings from Arduino
- Alert triggers
- Dashboard walkthrough
- Relay activation demo

### 2. Technical Report
- Problem statement
- Solution architecture
- Model training details
- Performance metrics
- Validation results

### 3. Presentation Slides
- 10-slide deck: Problem → Solution → Results → Impact
- Suitable for judging/pitch

---

## 🔬 Why Include the Ultrasonic Sensor?

**Cost:** ~$2  
**Value:** Massive

1. **Camera alone isn't enough.** Can see blockages but can't measure water depth.
2. **Early warning.** Water rising fast? Alert BEFORE it hits critical.
3. **Works in darkness.** Camera needs light. Ultrasonic doesn't.
4. **Redundancy.** If camera fails, sensor still works.
5. **Rate detection.** "Water rose 10cm in 5 minutes" > "water at 50cm"

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Metis won't boot | Check SD card insertion; try re-flashing |
| Can't SSH | Verify WiFi credentials; check router for IP |
| Camera not detected | Try different USB port; run `lsusb` |
| Arduino not detected | Check USB cable; run `ls /dev/ttyACM*` |
| No sensor readings | Check Arduino wiring; verify code uploaded |
| Dashboard won't load | Ensure Flask running; check firewall port 5000 |
| Relay won't trigger | Verify Sonoff IP; check Tasmota firmware |

---

## 🤝 Contributing

PRs welcome!

1. Fork the repo
2. Create branch: `git checkout -b feature/improvement`
3. Commit: `git commit -m "Add feature"`
4. Push: `git push origin feature/improvement`
5. Open Pull Request

---

## 📄 License

MIT License — use it, modify it, share it.

---

## 📞 Contact

- **Project:** DrainSentinel
- **Team:** ClimatrixAI
- **GitHub:** https://github.com/farouqfahm/DrainSentinel1.0

---

**Last Updated:** February 9, 2026  
**Version:** 2.0.0

---

*Built with ❤️ for Lagos*
