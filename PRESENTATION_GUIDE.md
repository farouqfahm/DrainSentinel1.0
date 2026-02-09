# DrainSentinel: Presentation Guide

**Duration:** 10-12 minutes  
**Slides:** 12  
**Format:** Problem → Solution → Demo → Impact

---

## Slide 1: Title Slide

### DrainSentinel
**Edge AI for Flood Prevention in Lagos**

*Team: ClimatrixAI*  
*February 2026*

**Visual:** Project logo or hero image of drainage system with tech overlay

---

## Slide 2: The Problem

### Lagos Floods Every Year

**Key Stats:**
- 2-3 major flooding events annually
- Millions of Naira in property damage
- Health risks from contaminated water
- Economic disruption across the city

**Root Cause:** Blocked drains that go undetected until it's too late

**Visual:** Photo of Lagos flooding / news headline

---

## Slide 3: Why Current Solutions Fail

### Reactive, Not Preventive

| Current Method | Problem |
|----------------|---------|
| Manual inspection | Covers only 15% of drains |
| Citizen reports | After flooding starts |
| Fixed sensors | Expensive, no visual confirmation |
| CCTV | Requires 24/7 human operators |

**The gap:** No real-time, autonomous monitoring

**Visual:** Icons representing each failed method

---

## Slide 4: Our Solution

### DrainSentinel: AI-Powered Flood Prevention

**What it does:**
1. 👁️ **SEES** blockages using computer vision
2. 📏 **MEASURES** water levels with ultrasonic sensor
3. 🧠 **PREDICTS** flooding using AI fusion
4. 🚨 **ALERTS** before disaster strikes
5. ⚡ **ACTS** by triggering pumps/sirens

**Key innovation:** All AI runs on edge — no cloud required

**Visual:** System diagram or device photo

---

## Slide 5: Hardware Stack

### Simple. Affordable. Effective.

| Component | Purpose | Cost |
|-----------|---------|------|
| Metis AI Accelerator | Edge compute brain | - |
| USB Camera | See blockages | $20 |
| Arduino + Sensor | Measure water | $27 |
| Sonoff Relay | Control pumps | $15 |

**Total cost per unit: ~$72**

**Visual:** Photo of assembled hardware

---

## Slide 6: How It Works — The AI

### Two-Stream Fusion

**Stream 1: Visual Detection**
- Camera captures drain every 5 seconds
- MobileNetV2 classifies: clear / partial / full blockage
- 87% accuracy

**Stream 2: Water Monitoring**
- Ultrasonic measures water level
- Arduino sends data every second
- Calculates rate of rise

**Fusion:** Risk score combines both for smart alerts

**Visual:** Diagram showing both streams merging

---

## Slide 7: The Risk Algorithm

### Smart Alerts, Not False Alarms

```
Risk = (0.4 × Blockage) + (0.3 × Water Level) + (0.2 × Rise Rate)
```

| Level | Meaning | Action |
|-------|---------|--------|
| 🟢 GREEN | All clear | Log only |
| 🟡 YELLOW | Watch closely | Dashboard alert |
| 🟠 ORANGE | Warning | SMS notification |
| 🔴 RED | Flood imminent | Trigger pump + siren |

**Visual:** Color-coded alert system graphic

---

## Slide 8: Live Demo

### See It In Action

**[SHOW LIVE DASHBOARD]**

Demonstrate:
1. Camera feed with AI detection overlay
2. Real-time water level readings
3. Alert level changing
4. (Optional) Trigger relay

**Visual:** Screenshot of dashboard or switch to live demo

---

## Slide 9: Results

### Proven Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| Detection accuracy | >80% | **87%** |
| Alert latency | <30s | **<10s** |
| Uptime (72hr test) | >95% | **99.2%** |
| Cost per unit | <$150 | **$72** |

**Field test:** 72 hours in Ikeja — detected 3 real blockages

**Visual:** Results chart or checkmarks

---

## Slide 10: Scalability

### From One Drain to All of Lagos

**Phase 1:** Pilot — 10 critical drains  
**Phase 2:** District — 100 drains  
**Phase 3:** City-wide — 1,000+ drains

**Network effect:**
- Central monitoring dashboard
- Pattern detection across locations
- Predictive maintenance scheduling

**Cost for 100 units: ~$7,200** (less than one flood cleanup)

**Visual:** Map of Lagos with deployment points

---

## Slide 11: Impact

### What This Means for Lagos

**For Residents:**
- Early warning = time to prepare
- Reduced property damage
- Safer neighborhoods

**For Government:**
- 24/7 monitoring without staff
- Data-driven maintenance
- Reduced emergency response costs

**For the Environment:**
- Prevent polluted flood water spread
- Better drainage = healthier city

**Visual:** Before/after or impact statistics

---

## Slide 12: Call to Action

### Partner With Us

**What we need:**
- Pilot locations for deployment
- Access to municipal drainage data
- Integration with LASEMA systems

**What we offer:**
- Full system deployment
- Training for maintenance staff
- Ongoing support and updates

**Contact:**
- GitHub: github.com/farouqfahm/DrainSentinel1.0
- Email: founders@climatrixai.com

**Visual:** Contact info + QR code to repo

---

## Bonus Slides (If Time Permits)

### Technical Deep-Dive

- Model training process
- Edge Impulse integration
- Arduino wiring diagram
- Dashboard architecture

### Future Roadmap

- Weather API integration
- Solar power option
- Mobile app
- LoRa for remote areas

---

## Presentation Tips

### Timing
- Slides 1-3: 2 minutes (problem)
- Slides 4-7: 3 minutes (solution)
- Slide 8: 2-3 minutes (demo)
- Slides 9-12: 3 minutes (results + ask)

### Demo Preparation
1. Start dashboard before presentation
2. Have test video ready as backup
3. Prepare "trigger" to show alert change
4. Practice demo flow 3x before

### Key Messages to Emphasize
1. **Prevention, not reaction** — we alert BEFORE flooding
2. **Edge AI** — works without internet
3. **Affordable** — $72 per unit
4. **Proven** — 87% accuracy, field tested

### Anticipated Questions

**Q: What if the camera gets dirty?**
A: Regular cleaning schedule; future version will have wiper

**Q: How does it work at night?**
A: Add IR light source; ultrasonic works in darkness

**Q: What about power outages?**
A: Auto-recovery on power restore; optional battery backup

**Q: How accurate is it really?**
A: 87% in testing; improves with local training data

**Q: Can it integrate with existing systems?**
A: Yes, via webhook API or direct database integration

---

## Visual Assets Needed

1. ☐ DrainSentinel logo
2. ☐ Hardware photo (assembled system)
3. ☐ Dashboard screenshot
4. ☐ System architecture diagram
5. ☐ Lagos flooding photo
6. ☐ Map with deployment points
7. ☐ Results chart
8. ☐ Wiring diagram
9. ☐ Demo video (backup)
10. ☐ QR code to GitHub repo

---

*Good luck with the presentation!*
