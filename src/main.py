#!/usr/bin/env python3
"""
DrainSentinel: Main Entry Point

This is the main script that runs the entire DrainSentinel system.
It coordinates the camera, Arduino sensors, AI detection, alerts, and relay control.

Hardware:
- Metis AI Accelerator (main compute)
- USB Camera (blockage detection)
- Arduino Uno Rev 4 (sensor hub via USB serial)
- HC-SR04 Ultrasonic Sensor (connected to Arduino)
- Sonoff Pro R3 Relay (optional, for pump/siren control)

Usage:
    python3 main.py              # Normal operation
    python3 main.py --test       # Test mode (simulates data)
    python3 main.py --calibrate  # Run calibration wizard
"""

import argparse
import logging
import signal
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# Ensure src directory is in path
sys.path.insert(0, str(Path(__file__).parent))

# Local imports
from camera import Camera
from arduino_serial import get_arduino
from ai_detector import BlockageDetector
from alert_system import AlertSystem
from dashboard import start_dashboard

# Configure logging
log_dir = Path('data/logs')
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'drainsentinel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DrainSentinel')


class DrainSentinel:
    """Main DrainSentinel application class."""
    
    def __init__(self, test_mode=False):
        """Initialize the DrainSentinel system."""
        self.test_mode = test_mode
        self.running = False
        
        # Configuration
        self.config = {
            'camera_interval': 5,         # seconds between camera captures
            'sensor_interval': 1,         # Arduino sends every 1 second
            'alert_check_interval': 10,   # seconds between alert checks
            'water_level_critical': 80,   # percentage threshold for critical
            'water_level_warning': 50,    # percentage threshold for warning
            'blockage_threshold': 0.6,    # AI confidence threshold
        }
        
        # Initialize components
        logger.info("=" * 60)
        logger.info("    DrainSentinel v2.0 Starting...")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Initializing components...")
        
        # Camera (always try to initialize)
        try:
            self.camera = Camera()
            logger.info("✓ Camera initialized")
        except Exception as e:
            logger.warning(f"✗ Camera failed: {e}")
            self.camera = None
        
        # Arduino (sensor hub)
        self.arduino = get_arduino(mock=test_mode)
        self.arduino.start_reading()
        logger.info("✓ Arduino sensor hub connected" if not test_mode else "✓ Arduino (mock mode)")
        
        # AI Detector
        try:
            self.detector = BlockageDetector()
            logger.info("✓ AI Detector initialized")
        except Exception as e:
            logger.warning(f"✗ AI Detector failed: {e}")
            self.detector = None
        
        # Alert System
        self.alerts = AlertSystem(test_mode=test_mode)
        logger.info("✓ Alert system initialized")
        
        # State variables
        self.current_state = {
            'water_level_cm': 0,
            'water_level_percent': 0,
            'blockage_detected': False,
            'blockage_confidence': 0,
            'blockage_class': 'unknown',
            'alert_level': 'GREEN',
            'last_image_path': None,
            'last_update': None,
            'rate_of_rise': 0,  # cm per minute
        }
        
        # Historical data for trend analysis
        self.water_history = []  # List of (timestamp, level) tuples
        self.max_history = 3600  # Keep 1 hour of data (at 1/sec = 3600 points)
        
        # Register Arduino callback
        self.arduino.add_callback(self._on_sensor_data)
        
        logger.info("")
        logger.info("DrainSentinel initialized successfully!")
        logger.info("")
    
    def _on_sensor_data(self, data):
        """Callback when new sensor data arrives from Arduino."""
        if not data.get('valid', False):
            return
        
        # Update state
        self.current_state['water_level_cm'] = data.get('water_level_cm', 0)
        self.current_state['water_level_percent'] = data.get('water_level_percent', 0)
        
        # Add to history
        now = time.time()
        level = data.get('water_level_cm', 0)
        self.water_history.append((now, level))
        
        # Trim old history
        cutoff = now - self.max_history
        self.water_history = [(t, l) for t, l in self.water_history if t > cutoff]
        
        # Calculate rate of rise (cm per minute)
        if len(self.water_history) >= 60:  # Need at least 1 minute of data
            old_time, old_level = self.water_history[-60]
            new_time, new_level = self.water_history[-1]
            time_diff = (new_time - old_time) / 60  # Convert to minutes
            if time_diff > 0:
                # Positive rate = water rising (distance decreasing)
                self.current_state['rate_of_rise'] = (old_level - new_level) / time_diff
    
    def update_camera(self):
        """Capture image and run blockage detection."""
        if self.camera is None:
            logger.debug("Camera not available")
            return
        
        try:
            # Capture image
            image_path = self.camera.capture()
            if image_path is None:
                logger.warning("Failed to capture camera image")
                return
            
            self.current_state['last_image_path'] = image_path
            
            # Run AI detection
            if self.detector:
                result = self.detector.detect(image_path)
                
                self.current_state['blockage_detected'] = result.get('blocked', False)
                self.current_state['blockage_confidence'] = result.get('confidence', 0)
                self.current_state['blockage_class'] = result.get('class_name', 'unknown')
                
                logger.debug(f"AI Detection: {result['class_name']} ({result['confidence']:.2%})")
        
        except Exception as e:
            logger.error(f"Camera update error: {e}")
    
    def calculate_alert_level(self):
        """Calculate the current alert level based on all factors."""
        water_pct = self.current_state['water_level_percent']
        blockage = self.current_state['blockage_detected']
        blockage_conf = self.current_state['blockage_confidence']
        rate = self.current_state['rate_of_rise']
        
        # Calculate composite risk score
        water_risk = water_pct / 100
        blockage_risk = blockage_conf if blockage else 0
        rate_risk = min(1.0, max(0, rate) / 10) if rate > 0 else 0  # 10cm/min = max risk
        
        risk_score = (0.4 * water_risk) + (0.4 * blockage_risk) + (0.2 * rate_risk)
        
        # Determine alert level
        if risk_score > 0.8 or water_pct > 90:
            level = 'RED'
        elif risk_score > 0.6 or water_pct > 70 or (blockage and blockage_conf > 0.8):
            level = 'ORANGE'
        elif risk_score > 0.4 or water_pct > 50 or blockage:
            level = 'YELLOW'
        else:
            level = 'GREEN'
        
        old_level = self.current_state['alert_level']
        self.current_state['alert_level'] = level
        
        # Trigger alert if level changed (and not just fluctuating)
        if self._level_priority(level) > self._level_priority(old_level):
            self.alerts.send_alert(level, self.current_state)
            
            # Trigger relay for RED alerts
            if level == 'RED':
                self._trigger_relay(True)
        elif level == 'GREEN' and old_level != 'GREEN':
            # All clear - turn off relay
            self._trigger_relay(False)
        
        logger.debug(f"Alert level: {level} (risk: {risk_score:.2%})")
    
    def _level_priority(self, level):
        """Convert alert level to numeric priority."""
        priorities = {'GREEN': 0, 'YELLOW': 1, 'ORANGE': 2, 'RED': 3}
        return priorities.get(level, 0)
    
    def _trigger_relay(self, on=True):
        """Trigger Sonoff relay (for pump/siren)."""
        # Load relay config
        try:
            import json
            config_file = Path('config/settings.json')
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                
                relay_ip = config.get('sonoff_ip')
                if relay_ip:
                    import requests
                    action = 'on' if on else 'off'
                    url = f"http://{relay_ip}/cm?cmnd=Power%20{action}"
                    response = requests.get(url, timeout=5)
                    logger.info(f"Relay {'activated' if on else 'deactivated'}: {response.text}")
        except Exception as e:
            logger.warning(f"Relay control failed: {e}")
    
    def run_camera_loop(self):
        """Background loop for camera captures."""
        while self.running:
            try:
                self.update_camera()
                time.sleep(self.config['camera_interval'])
            except Exception as e:
                logger.error(f"Camera loop error: {e}")
                time.sleep(1)
    
    def run_alert_loop(self):
        """Background loop for alert checking."""
        while self.running:
            try:
                self.current_state['last_update'] = datetime.now().isoformat()
                self.calculate_alert_level()
                time.sleep(self.config['alert_check_interval'])
            except Exception as e:
                logger.error(f"Alert loop error: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the DrainSentinel monitoring system."""
        logger.info("Starting DrainSentinel monitoring...")
        self.running = True
        
        # Start background threads
        threads = [
            threading.Thread(target=self.run_camera_loop, name='CameraLoop'),
            threading.Thread(target=self.run_alert_loop, name='AlertLoop'),
        ]
        
        for t in threads:
            t.daemon = True
            t.start()
        
        # Start web dashboard (runs in main thread)
        logger.info("Starting web dashboard on port 5000...")
        logger.info("Open http://drainsentinel.local:5000 in your browser")
        logger.info("")
        
        start_dashboard(self)
    
    def stop(self):
        """Stop the DrainSentinel system."""
        logger.info("Stopping DrainSentinel...")
        self.running = False
        
        # Cleanup
        if self.camera:
            self.camera.release()
        if self.arduino:
            self.arduino.close()
        if self.detector:
            self.detector.close()
        
        # Ensure relay is off
        self._trigger_relay(False)
        
        logger.info("DrainSentinel stopped")
    
    def get_status(self):
        """Get current system status as dictionary."""
        return {
            **self.current_state,
            'running': self.running,
            'test_mode': self.test_mode,
            'uptime': time.time(),
            'camera_available': self.camera is not None,
            'arduino_connected': hasattr(self.arduino, 'serial') and self.arduino.serial is not None,
            'ai_available': self.detector is not None,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='DrainSentinel Monitoring System')
    parser.add_argument('--test', action='store_true', help='Run in test mode (mock sensors)')
    parser.add_argument('--calibrate', action='store_true', help='Run calibration wizard')
    args = parser.parse_args()
    
    if args.calibrate:
        from calibrate import run_calibration
        run_calibration()
        return
    
    # Create and start the system
    sentinel = DrainSentinel(test_mode=args.test)
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        sentinel.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    try:
        sentinel.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sentinel.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
