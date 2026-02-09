# DrainSentinel: Step-by-Step Implementation Roadmap

**For Beginners** — No prior experience required. Just follow each step.

---

## 📋 Overview

This roadmap breaks down the entire project into manageable phases. Each phase has clear goals, estimated time, and detailed instructions.

**Total Estimated Time:** 12-16 hours (over 1-2 days)

---

## Your Hardware Stack

Before we start, confirm you have all these components:

| Component | Purpose | Check |
|-----------|---------|-------|
| **Metis AI Accelerator** | Main compute / edge AI brain | ☐ |
| **USB Camera (1080p)** | Visual blockage detection | ☐ |
| **Arduino Uno Rev 4** | Sensor hub (connects ultrasonic) | ☐ |
| **HC-SR04 Ultrasonic Sensor** | Water level measurement | ☐ |
| **Sonoff Pro R3 Relay** | Trigger pumps/sirens (optional) | ☐ |
| **Wi-Fi Dongle** | Remote connectivity | ☐ |
| **MicroSD Card (32GB+)** | Storage for OS and data | ☐ |
| **USB cables** | Connect Arduino + Camera to Metis | ☐ |
| **Jumper wires** | Connect sensor to Arduino | ☐ |

### What We're NOT Using
- ❌ Echo Dot — Removed from project
- ❌ Second camera — Using ONE camera only

---

## Phase 0: Preparation

**Time:** 30 minutes  
**Goal:** Gather materials and understand the system

### 0.1 Download Required Software

On your computer (Windows/Mac/Linux), download:

1. **Raspberry Pi Imager** (for flashing Metis)
   - https://www.raspberrypi.com/software/

2. **Arduino IDE** (for programming Arduino)
   - https://www.arduino.cc/en/software

3. **A terminal app** (for SSH access)
   - Windows: Use PowerShell or install PuTTY
   - Mac/Linux: Terminal is built-in

### 0.2 Gather Physical Items

- MicroSD card reader
- USB-A to USB-B cable (for Arduino)
- USB extension cable (optional, for camera positioning)
- Small flathead screwdriver (for some terminals)

---

## Phase 1: Flash the Metis AI Accelerator

**Time:** 45-60 minutes  
**Goal:** Install an operating system on the Metis

The Metis has no OS yet. We need to flash one.

### 1.1 Identify Your Metis Type

Check the label or documentation on your Metis. Common types:

| Type | Based On | Flash Method |
|------|----------|--------------|
| CM4-based | Raspberry Pi Compute Module 4 | Use Raspberry Pi Imager |
| Jetson-based | NVIDIA Jetson | Use NVIDIA SDK Manager |
| Custom | Varies | Check manufacturer docs |

**Most Metis devices are CM4-based.** We'll assume that here.

### 1.2 Flash the MicroSD Card

1. **Insert MicroSD card** into your computer's card reader

2. **Open Raspberry Pi Imager**

3. **Choose Device:**
   - Click "Choose Device"
   - Select "Raspberry Pi 4" (CM4 is compatible)

4. **Choose OS:**
   - Click "Choose OS"
   - Select **"Raspberry Pi OS (64-bit)"**
   - This includes desktop environment

5. **Choose Storage:**
   - Click "Choose Storage"  
   - Select your MicroSD card
   - ⚠️ **Warning:** This will erase everything on the card!

6. **Configure Settings (CRITICAL!):**
   
   Click the **gear icon ⚙️** (or press `Ctrl+Shift+X`)
   
   Fill in:
   | Setting | Value |
   |---------|-------|
   | Set hostname | `drainsentinel` |
   | Enable SSH | ✅ Check this |
   | Use password authentication | ✅ |
   | Set username | `pi` |
   | Set password | `YourSecurePassword123` |
   | Configure wireless LAN | ✅ Check this |
   | SSID | Your WiFi network name |
   | Password | Your WiFi password |
   | Wireless LAN country | NG (Nigeria) |
   | Set locale settings | ✅ Set your timezone |
   
   Click **Save**

7. **Write the Image:**
   - Click "Write"
   - Confirm the warning
   - Wait 10-15 minutes
   - When done, click "Continue"

8. **Eject safely** and remove the MicroSD card

### 1.3 First Boot

1. **Insert MicroSD** into the Metis AI Accelerator
2. **Connect power** to the Metis
3. **Wait 2-3 minutes** for first boot (it's setting up)
4. The status LEDs should blink, then stabilize

### 1.4 Connect via SSH

From your computer's terminal:

```bash
# Try connecting using hostname
ssh pi@drainsentinel.local

# If that fails, find the IP from your router and use:
ssh pi@192.168.1.XXX
```

When prompted:
- Type `yes` to accept the fingerprint
- Enter your password

**Success!** You should see:
```
pi@drainsentinel:~ $
```

### 1.5 Update the System

```bash
# Update package lists
sudo apt update

# Upgrade all packages (this takes 5-10 minutes)
sudo apt full-upgrade -y

# Clean up
sudo apt autoremove -y

# Reboot
sudo reboot
```

Wait 30 seconds, then reconnect:
```bash
ssh pi@drainsentinel.local
```

---

## Phase 2: Install Software on Metis

**Time:** 30-45 minutes  
**Goal:** Install all required packages and libraries

### 2.1 Install System Packages

```bash
# Core packages
sudo apt install -y python3-pip python3-opencv python3-numpy python3-serial

# Camera tools
sudo apt install -y fswebcam v4l-utils

# Web server dependencies
sudo apt install -y python3-flask

# Git for cloning the repo
sudo apt install -y git

# Serial port tools
sudo apt install -y screen minicom
```

### 2.2 Install Python Packages

```bash
pip3 install flask flask-socketio pyserial requests pillow
```

### 2.3 Clone the DrainSentinel Repository

```bash
cd ~
git clone https://github.com/farouqfahm/DrainSentinel1.0.git
cd DrainSentinel1.0

# Create required directories
mkdir -p data/captures data/logs config models
```

### 2.4 Verify Installation

```bash
# Check Python
python3 --version  # Should be 3.9+

# Check OpenCV
python3 -c "import cv2; print(cv2.__version__)"

# Check Flask
python3 -c "import flask; print(flask.__version__)"

# Check serial
python3 -c "import serial; print(serial.__version__)"
```

---

## Phase 3: Set Up Arduino Uno Rev 4

**Time:** 30-45 minutes  
**Goal:** Program Arduino to read ultrasonic sensor and send data

### 3.1 Wire the Ultrasonic Sensor to Arduino

**Components:**
- Arduino Uno Rev 4
- HC-SR04 Ultrasonic Sensor
- 4 jumper wires

**Wiring:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    HC-SR04 Sensor              Arduino Uno Rev 4            │
│    ┌───────────────┐           ┌─────────────────┐         │
│    │               │           │                 │         │
│    │  VCC ●────────┼───────────┼─► 5V            │         │
│    │               │           │                 │         │
│    │  GND ●────────┼───────────┼─► GND           │         │
│    │               │           │                 │         │
│    │  TRIG ●───────┼───────────┼─► Pin 9         │         │
│    │               │           │                 │         │
│    │  ECHO ●───────┼───────────┼─► Pin 10        │         │
│    │               │           │                 │         │
│    └───────────────┘           └─────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Wire Colors (suggestion):
- VCC  → Red wire
- GND  → Black wire
- TRIG → Yellow wire
- ECHO → Green wire
```

**Step by step:**

1. **VCC pin** (sensor) → **5V pin** (Arduino)
2. **GND pin** (sensor) → **GND pin** (Arduino)
3. **TRIG pin** (sensor) → **Pin 9** (Arduino)
4. **ECHO pin** (sensor) → **Pin 10** (Arduino)

⚠️ **Note:** Arduino Uno Rev 4 is 5V tolerant on GPIO, so no voltage divider needed (unlike Raspberry Pi!)

### 3.2 Upload Arduino Code

1. **Connect Arduino to your computer** via USB

2. **Open Arduino IDE**

3. **Select Board:**
   - Tools → Board → Arduino UNO R4 Boards → Arduino UNO R4 WiFi
   - (Or "Arduino UNO R4 Minima" if you have that version)

4. **Select Port:**
   - Tools → Port → Select your Arduino's port
   - Windows: `COM3` or similar
   - Mac: `/dev/cu.usbmodem*`
   - Linux: `/dev/ttyACM0`

5. **Create New Sketch:**
   - File → New

6. **Copy the code** from `hardware/arduino_sensor.ino` in this repository
   - Or copy from below:

```cpp
// Pin definitions
#define TRIG_PIN 9
#define ECHO_PIN 10

// Configuration
#define SERIAL_BAUD 9600
#define MEASUREMENT_INTERVAL_MS 1000

float emptyDistance = 100.0;
float fullDistance = 10.0;

void setup() {
    Serial.begin(SERIAL_BAUD);
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    digitalWrite(TRIG_PIN, LOW);
    Serial.println("{\"status\": \"DrainSentinel Arduino started\"}");
    delay(500);
}

float measureDistance() {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);
    if (duration == 0) return -1;
    
    float distance = (duration * 0.0343) / 2.0;
    if (distance < 2 || distance > 400) return -1;
    
    return distance;
}

float distanceToPercent(float distance) {
    if (distance < 0) return -1;
    float percent = 100.0 - ((distance - fullDistance) / (emptyDistance - fullDistance) * 100.0);
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    return percent;
}

void loop() {
    float distance = measureDistance();
    float percent = distanceToPercent(distance);
    bool valid = (distance > 0);
    
    Serial.print("{\"water_level_cm\": ");
    Serial.print(distance, 1);
    Serial.print(", \"water_level_percent\": ");
    Serial.print(percent, 1);
    Serial.print(", \"valid\": ");
    Serial.print(valid ? "true" : "false");
    Serial.println("}");
    
    delay(MEASUREMENT_INTERVAL_MS);
}
```

7. **Upload:**
   - Click the Upload button (→ arrow)
   - Wait for "Done uploading"

8. **Test:**
   - Tools → Serial Monitor
   - Set baud rate to `9600`
   - You should see JSON data every second:
     ```
     {"water_level_cm": 45.2, "water_level_percent": 39.1, "valid": true}
     ```

### 3.3 Connect Arduino to Metis

1. **Disconnect Arduino from computer**
2. **Connect Arduino to Metis** via USB cable
3. On the Metis, verify detection:

```bash
# Check Arduino is detected
ls /dev/ttyACM*
# Should show: /dev/ttyACM0

# Read serial data
cat /dev/ttyACM0
# Should show JSON lines

# Press Ctrl+C to stop
```

---

## Phase 4: Set Up USB Camera

**Time:** 15-20 minutes  
**Goal:** Connect camera and verify it works

### 4.1 Connect Camera to Metis

1. **Plug USB camera** into any USB port on the Metis
2. Position camera so it will point at the drain

### 4.2 Verify Camera Detection

```bash
# List video devices
ls /dev/video*
# Should show: /dev/video0

# Get camera info
v4l2-ctl --list-devices
```

### 4.3 Test Camera Capture

```bash
# Take a test photo
cd ~/DrainSentinel1.0
fswebcam -r 1280x720 --no-banner data/captures/test.jpg

# Check the file was created
ls -la data/captures/test.jpg
```

**To view the test image:**

Option A: Copy to your computer
```bash
# On your computer:
scp pi@drainsentinel.local:~/DrainSentinel1.0/data/captures/test.jpg ./
```

Option B: View via web (after dashboard is running)

---

## Phase 5: Configure the System

**Time:** 15-20 minutes  
**Goal:** Set up configuration files

### 5.1 Create Settings File

```bash
cd ~/DrainSentinel1.0

# Create config file
cat > config/settings.json << 'EOF'
{
    "camera_interval": 5,
    "alert_check_interval": 10,
    "water_level_critical": 80,
    "water_level_warning": 50,
    "blockage_threshold": 0.6,
    "sonoff_ip": null,
    "alerts": {
        "sms_enabled": false,
        "email_enabled": false,
        "webhook_enabled": false
    }
}
EOF
```

### 5.2 Run Calibration (Optional but Recommended)

```bash
cd ~/DrainSentinel1.0
python3 src/calibrate.py
```

Follow the wizard to:
1. Set the "empty" water level (normal conditions)
2. Set the "critical" water level (flood imminent)
3. Verify readings are accurate

---

## Phase 6: Run DrainSentinel

**Time:** 10 minutes  
**Goal:** Start the system and verify everything works

### 6.1 Run in Test Mode First

```bash
cd ~/DrainSentinel1.0
python3 src/main.py --test
```

This uses simulated data. You should see:
```
============================================================
    DrainSentinel v2.0 Starting...
============================================================

Initializing components...
✓ Camera initialized
✓ Arduino (mock mode)
✓ AI Detector initialized
✓ Alert system initialized

DrainSentinel initialized successfully!

Starting web dashboard on port 5000...
Open http://drainsentinel.local:5000 in your browser
```

### 6.2 Open the Dashboard

On any device connected to the same network:
1. Open a web browser
2. Go to: `http://drainsentinel.local:5000`
3. You should see the live dashboard!

### 6.3 Run with Real Hardware

Stop the test mode (Ctrl+C), then run for real:

```bash
python3 src/main.py
```

Now it uses:
- Real camera feed
- Real Arduino sensor data
- Real AI detection

---

## Phase 7: Set Up Auto-Start

**Time:** 15 minutes  
**Goal:** Make DrainSentinel start automatically on boot

### 7.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/drainsentinel.service
```

Paste this content:

```ini
[Unit]
Description=DrainSentinel Monitoring Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/DrainSentinel1.0
ExecStart=/usr/bin/python3 /home/pi/DrainSentinel1.0/src/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/DrainSentinel1.0/data/logs/service.log
StandardError=append:/home/pi/DrainSentinel1.0/data/logs/service.log

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### 7.2 Enable and Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable drainsentinel

# Start the service now
sudo systemctl start drainsentinel

# Check status
sudo systemctl status drainsentinel
```

### 7.3 Useful Service Commands

```bash
# Stop the service
sudo systemctl stop drainsentinel

# Restart the service
sudo systemctl restart drainsentinel

# View logs
journalctl -u drainsentinel -f

# Disable auto-start
sudo systemctl disable drainsentinel
```

---

## Phase 8: Optional - Set Up Sonoff Relay

**Time:** 30-45 minutes  
**Goal:** Enable automatic pump/siren activation

### 8.1 Flash Sonoff with Tasmota

The Sonoff Pro R3 needs custom firmware for local control:

1. **Download Tasmota** firmware from: https://tasmota.github.io/
2. **Flash using** Tasmotizer or similar tool
3. **Connect Sonoff to WiFi**
4. **Note its IP address**

### 8.2 Configure in DrainSentinel

Edit `config/settings.json`:

```bash
nano config/settings.json
```

Change:
```json
"sonoff_ip": "192.168.1.XXX"
```

Replace with your Sonoff's actual IP.

### 8.3 Test Relay

```bash
# Turn on
curl "http://192.168.1.XXX/cm?cmnd=Power%20on"

# Turn off
curl "http://192.168.1.XXX/cm?cmnd=Power%20off"
```

---

## Phase 9: Physical Deployment

**Time:** 1-2 hours  
**Goal:** Install the system at the actual drain location

### 9.1 Mounting Guidelines

**Camera:**
- Point at drain opening
- Clear view of potential blockage area
- Protected from direct rain
- Good lighting (or add light source)

**Ultrasonic Sensor:**
- Point straight down at water surface
- 20-100 cm above expected water level
- Perpendicular to water surface
- Protected from splash

**Metis + Arduino:**
- In waterproof enclosure
- Ventilation holes (covered with mesh)
- Easy access for maintenance
- Secure power connection

### 9.2 Power Options

1. **Mains power** with weatherproof extension
2. **Solar + battery** for remote locations
3. **PoE** if available (requires adapter)

### 9.3 Weatherproofing

- IP65+ rated enclosure
- Cable glands for wires
- Silicone sealant on joints
- Desiccant packs inside enclosure

---

## Phase 10: Create Demo Materials

**Time:** 2-3 hours  
**Goal:** Prepare video, report, and presentation

### 10.1 Record Demo Video (5-7 minutes)

Capture:
1. Hardware overview — show all components
2. System startup — boot process
3. Dashboard tour — explain each section
4. Live detection — show camera + AI working
5. Sensor demo — show water level readings
6. Alert demo — trigger a warning
7. (Optional) Relay demo — show pump activation

### 10.2 Write Technical Report

Use the `PROJECT_REPORT.md` template. Include:
- Problem statement
- Solution architecture
- Implementation details
- Performance metrics
- Challenges and solutions
- Future improvements

### 10.3 Create Presentation

Use the `PRESENTATION_GUIDE.md` for slide content:
- 10-12 slides
- Problem → Solution → Demo → Impact
- Include screenshots and diagrams

---

## 🎉 Congratulations!

You've built a complete AI-powered drainage monitoring system!

### What You've Accomplished:

- ✅ Flashed and configured the Metis AI Accelerator
- ✅ Programmed Arduino for sensor data collection
- ✅ Connected camera and ultrasonic sensor
- ✅ Deployed AI blockage detection
- ✅ Built real-time web dashboard
- ✅ Set up automatic alerts
- ✅ Created demo materials

### Next Steps:

- Deploy to actual drain location
- Monitor and collect real-world data
- Fine-tune AI model with local images
- Scale to multiple locations
- Integrate with city infrastructure

---

## Troubleshooting Reference

| Problem | Possible Causes | Solutions |
|---------|-----------------|-----------|
| Metis won't boot | Bad SD card, corrupt image | Re-flash with new image |
| Can't SSH | Wrong WiFi, hostname issue | Check router for IP, use IP directly |
| Camera not detected | USB issue, driver problem | Try different port, run `lsusb` |
| Arduino not detected | Cable issue, wrong port | Check cable, try `/dev/ttyUSB0` |
| No sensor readings | Wiring error, code issue | Verify wiring, re-upload code |
| Dashboard not loading | Flask not running, port blocked | Check service status, firewall |
| AI detection slow | CPU limited | Use Edge Impulse optimized model |
| False alerts | Calibration off | Re-run calibration wizard |

---

*Questions? Open an issue on GitHub!*
