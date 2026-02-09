# DrainSentinel: Hardware Wiring Guide

## Overview

This document shows how to connect all hardware components for the DrainSentinel system.

---

## Component List

| Component | Quantity | Notes |
|-----------|----------|-------|
| Metis AI Accelerator | 1 | Main compute unit |
| USB Camera (1080p) | 1 | For visual detection |
| Arduino Uno Rev 4 | 1 | Sensor hub |
| HC-SR04 Ultrasonic Sensor | 1 | Water level |
| Sonoff Pro R3 Relay | 1 | Optional, for pump/siren |
| USB-A to USB-B Cable | 1 | Connect Arduino to Metis |
| Jumper Wires | 4 | Connect sensor to Arduino |
| MicroSD Card (32GB+) | 1 | For Metis OS |

---

## System Connections

```
                                    ┌─────────────────────────────────┐
                                    │       METIS AI ACCELERATOR      │
                                    │                                 │
                                    │   USB Ports         Ethernet    │
                                    │   [1] [2] [3]       [  RJ45  ]  │
                                    │    │   │                        │
                                    │    │   │                        │
                                    │   SD Card Slot      Power       │
                                    │   [ MicroSD ]       [  5V  ]    │
                                    └────┼───┼────────────────────────┘
                                         │   │
                                         │   │
           ┌─────────────────────────────┘   └──────────────────┐
           │ USB                                           USB  │
           ▼                                                    ▼
┌─────────────────────┐                            ┌────────────────────┐
│    USB CAMERA       │                            │   ARDUINO UNO R4   │
│    (1080p)          │                            │                    │
│                     │                            │  5V ─────────┐     │
│  Point at drain     │                            │  GND ────────┼──┐  │
│  entrance           │                            │  Pin 9 ──────┼──┼──┼─► TRIG
│                     │                            │  Pin 10 ─────┼──┼──┼─► ECHO
└─────────────────────┘                            │              │  │  │
                                                   └──────────────┼──┼──┘
                                                                  │  │
                                                                  │  │
                                                   ┌──────────────┼──┼──────┐
                                                   │   HC-SR04    │  │      │
                                                   │   ULTRASONIC │  │      │
                                                   │              │  │      │
                                                   │  VCC ◄───────┘  │      │
                                                   │  GND ◄──────────┘      │
                                                   │  TRIG                  │
                                                   │  ECHO                  │
                                                   │                        │
                                                   │  Point down at water   │
                                                   └────────────────────────┘
```

---

## Detailed Wiring: HC-SR04 to Arduino

### Pin Connections

| HC-SR04 Pin | Arduino Pin | Wire Color (suggested) |
|-------------|-------------|------------------------|
| VCC | 5V | Red |
| GND | GND | Black |
| TRIG | Pin 9 | Yellow |
| ECHO | Pin 10 | Green |

### Wiring Diagram

```
          HC-SR04 Sensor                    Arduino Uno Rev 4
    ┌──────────────────────┐         ┌──────────────────────────┐
    │                      │         │                          │
    │  ┌───┐ ┌───┐        │         │    ┌─────────────────┐   │
    │  │ T │ │ R │  Eyes  │         │    │ USB-B Connector │   │
    │  └───┘ └───┘        │         │    └────────┬────────┘   │
    │                      │         │             │            │
    │  VCC  TRIG ECHO GND │         │             │ to Metis   │
    │   │    │    │    │  │         │             │            │
    └───┼────┼────┼────┼──┘         │   ┌────────────────────┐ │
        │    │    │    │            │   │  Digital Pins      │ │
        │    │    │    │            │   │  ...  9  10  ...   │ │
        │    │    │    │            │   └──────┬───┬─────────┘ │
        │    │    │    │            │          │   │           │
        │    │    └────┼────────────┼──────────┼───┘           │
        │    │         │            │          │               │
        │    └─────────┼────────────┼──────────┘               │
        │              │            │                          │
        │              │            │   ┌────────────────────┐ │
        │              │            │   │  Power Pins        │ │
        │              │            │   │  5V  GND  ...      │ │
        │              │            │   └──┬───┬─────────────┘ │
        │              │            │      │   │               │
        └──────────────┼────────────┼──────┘   │               │
                       │            │          │               │
                       └────────────┼──────────┘               │
                                    │                          │
                                    └──────────────────────────┘

Wire Connections:
    VCC  (Red)    ──────────────► 5V
    GND  (Black)  ──────────────► GND
    TRIG (Yellow) ──────────────► Pin 9
    ECHO (Green)  ──────────────► Pin 10
```

### Physical Pin Locations on Arduino Uno Rev 4

```
    Arduino Uno Rev 4 (Top View)
    ┌────────────────────────────────────────────────────┐
    │  [USB-B]                              [DC Jack]    │
    │                                                    │
    │  [SCL SDA AREF GND 13 12 11 10  9  8]             │
    │                           ▲   ▲                    │
    │                        ECHO TRIG                   │
    │                                                    │
    │                                                    │
    │                                                    │
    │  [IOREF RST 3.3V 5V GND GND VIN]                  │
    │                  ▲   ▲                             │
    │                 VCC GND                            │
    │                                                    │
    │  [ 0  1  2  3  4  5  A0 A1 A2 A3 A4 A5]           │
    │                                                    │
    └────────────────────────────────────────────────────┘
```

---

## USB Connections to Metis

### Camera
- Plug USB camera into any available USB port on Metis
- USB 3.0 ports (usually blue) recommended for better performance

### Arduino
- Connect Arduino to Metis using USB-A to USB-B cable
- Arduino will appear as `/dev/ttyACM0` on Linux

```
Metis USB Ports:
┌─────────────────┐
│ [USB1] [USB2]   │  ← Plug camera and Arduino here
│ [USB3] [USB4]   │
└─────────────────┘
```

---

## Optional: Sonoff Pro R3 Relay

The Sonoff relay connects via WiFi, not wires.

### Setup Steps:
1. Flash with Tasmota firmware
2. Connect to your WiFi network
3. Note IP address
4. Configure in DrainSentinel settings

### Control:
- Metis sends HTTP commands to Sonoff
- When RED alert triggers → Sonoff activates pump/siren

```
┌─────────────────┐     WiFi      ┌─────────────────┐
│      METIS      │ ~~~~~~~~~~~~~ │  SONOFF PRO R3  │
│                 │               │                 │
│  HTTP Commands  │               │   ┌─────────┐   │
│  "Power on"     │ ──────────────│───│ RELAY   │───│──► Pump/Siren
│  "Power off"    │               │   └─────────┘   │
└─────────────────┘               └─────────────────┘
```

---

## Sensor Positioning

### Camera Position
- Point at drain opening/entrance
- Ensure clear view of blockage area
- 0.5-2 meters from drain
- Slight downward angle
- Protected from direct rain

```
      Camera
        │
        │  ╲
        │   ╲  Line of sight
        │    ╲
        ▼     ╲
     ┌──────────╲────────┐
     │           ╲       │
     │  Drain     ╲      │
     │  Opening    •     │
     │  (monitor   └─────│──── Blockage visible here
     │   this area)      │
     └───────────────────┘
```

### Ultrasonic Sensor Position
- Point straight down at water surface
- 20-100 cm above expected water level
- Perpendicular to water (not angled)
- Away from walls (avoid false echoes)

```
      Sensor
        │
        │ Sound waves
        ▼ ▼ ▼ ▼ ▼
     ~~~~~~~~~~~~~~~  ← Water surface
        │
        │  Measure this
        │  distance
        ▼
     ───────────────  ← Drain bottom
```

---

## Power Requirements

| Component | Voltage | Current | Power |
|-----------|---------|---------|-------|
| Metis AI Accelerator | 5V | 2-3A | 10-15W |
| USB Camera | 5V (USB) | 0.5A | 2.5W |
| Arduino Uno Rev 4 | 5V (USB) | 0.2A | 1W |
| HC-SR04 | 5V (from Arduino) | 15mA | 0.08W |

**Total System Power:** ~15-20W

**Power Supply:** Use a good quality 5V/3A+ power supply for the Metis

---

## Checklist Before Power On

- [ ] MicroSD card with OS inserted in Metis
- [ ] USB Camera connected to Metis
- [ ] Arduino connected to Metis via USB
- [ ] HC-SR04 connected to Arduino (VCC→5V, GND→GND, TRIG→9, ECHO→10)
- [ ] Arduino code uploaded
- [ ] Power supply connected to Metis
- [ ] WiFi credentials configured (for remote access)

---

## Troubleshooting

| Symptom | Possible Cause | Solution |
|---------|----------------|----------|
| Camera not detected | USB issue | Try different port, check `lsusb` |
| Arduino not detected | Cable/driver | Check `/dev/ttyACM*`, try different cable |
| Sensor reads -1 | Wiring wrong | Verify TRIG→9, ECHO→10, check power |
| Erratic readings | Noise/interference | Check connections, add averaging |
| Sonoff not responding | Network issue | Verify IP, check Tasmota config |

---

*For detailed software setup, see IMPLEMENTATION_ROADMAP.md*
