#!/usr/bin/env python3
"""
DrainSentinel: Arduino Serial Communication Module

Handles reading sensor data from Arduino Uno Rev 4 via USB serial.
The Arduino sends JSON-formatted water level readings.
"""

import json
import logging
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Dict, Callable

logger = logging.getLogger('DrainSentinel.Arduino')


class ArduinoSerial:
    """Communicate with Arduino sensor hub via USB serial."""
    
    def __init__(self, port: str = None, baud_rate: int = 9600):
        """
        Initialize Arduino serial connection.
        
        Args:
            port: Serial port (e.g., '/dev/ttyACM0'). Auto-detect if None.
            baud_rate: Serial baud rate (must match Arduino)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.running = False
        self.read_thread = None
        
        # Latest sensor data
        self.latest_data = {
            'water_level_cm': 0,
            'water_level_percent': 0,
            'distance_raw': 0,
            'valid': False,
            'timestamp': 0,
        }
        
        # Callbacks for data updates
        self.callbacks = []
        
        # Connect
        self._connect()
    
    def _find_arduino_port(self) -> Optional[str]:
        """Auto-detect Arduino serial port."""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Look for common Arduino identifiers
            if 'Arduino' in port.description:
                logger.info(f"Found Arduino: {port.device} - {port.description}")
                return port.device
            if 'ttyACM' in port.device or 'ttyUSB' in port.device:
                logger.info(f"Found potential Arduino: {port.device}")
                return port.device
            if 'usbmodem' in port.device:  # macOS
                logger.info(f"Found potential Arduino: {port.device}")
                return port.device
        
        logger.warning("No Arduino found. Available ports:")
        for port in ports:
            logger.warning(f"  {port.device}: {port.description}")
        
        return None
    
    def _connect(self) -> bool:
        """Establish serial connection to Arduino."""
        # Auto-detect port if not specified
        if self.port is None:
            self.port = self._find_arduino_port()
        
        if self.port is None:
            logger.error("No Arduino port found")
            return False
        
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=2
            )
            
            # Wait for Arduino to reset after connection
            time.sleep(2)
            
            # Clear any startup messages
            self.serial.reset_input_buffer()
            
            logger.info(f"Connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            self.serial = None
            return False
    
    def start_reading(self):
        """Start background thread to read sensor data."""
        if self.serial is None:
            logger.error("Cannot start reading: not connected")
            return
        
        self.running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        logger.info("Started Arduino reading thread")
    
    def stop_reading(self):
        """Stop the reading thread."""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=2)
        logger.info("Stopped Arduino reading thread")
    
    def _read_loop(self):
        """Background loop to read serial data."""
        while self.running:
            try:
                if self.serial is None or not self.serial.is_open:
                    logger.warning("Serial connection lost, attempting reconnect...")
                    time.sleep(5)
                    self._connect()
                    continue
                
                # Read line from Arduino
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    
                    if line:
                        self._parse_data(line)
                else:
                    time.sleep(0.1)
                    
            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                self.serial = None
                time.sleep(5)
            except Exception as e:
                logger.error(f"Read loop error: {e}")
                time.sleep(1)
    
    def _parse_data(self, line: str):
        """Parse JSON data from Arduino."""
        try:
            data = json.loads(line)
            
            # Check if it's sensor data (has water_level_cm)
            if 'water_level_cm' in data:
                self.latest_data.update(data)
                self.latest_data['last_update'] = time.time()
                
                logger.debug(f"Sensor data: {data}")
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            
            # Log calibration or status messages
            elif 'calibration' in data or 'set' in data:
                logger.info(f"Arduino calibration: {data}")
            elif 'status' in data:
                logger.info(f"Arduino status: {data}")
                
        except json.JSONDecodeError:
            # Not JSON - might be debug message
            logger.debug(f"Arduino: {line}")
    
    def get_latest(self) -> Dict:
        """Get the latest sensor reading."""
        return self.latest_data.copy()
    
    def get_water_level(self) -> Optional[float]:
        """Get current water level in cm."""
        if self.latest_data['valid']:
            return self.latest_data['water_level_cm']
        return None
    
    def get_water_level_percent(self) -> Optional[float]:
        """Get current water level as percentage."""
        if self.latest_data['valid']:
            return self.latest_data['water_level_percent']
        return None
    
    def add_callback(self, callback: Callable):
        """Add a callback function to be called on new data."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def send_command(self, command: str) -> bool:
        """Send a command to Arduino."""
        if self.serial is None or not self.serial.is_open:
            logger.error("Cannot send command: not connected")
            return False
        
        try:
            self.serial.write(f"{command}\n".encode('utf-8'))
            logger.info(f"Sent command: {command}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def calibrate_empty(self):
        """Tell Arduino to calibrate empty level (current reading)."""
        return self.send_command("CAL_EMPTY")
    
    def calibrate_full(self):
        """Tell Arduino to calibrate full/critical level (current reading)."""
        return self.send_command("CAL_FULL")
    
    def set_empty_distance(self, distance: float):
        """Set empty distance manually."""
        return self.send_command(f"SET_EMPTY:{distance}")
    
    def set_full_distance(self, distance: float):
        """Set full/critical distance manually."""
        return self.send_command(f"SET_FULL:{distance}")
    
    def get_status(self):
        """Request calibration status from Arduino."""
        return self.send_command("STATUS")
    
    def close(self):
        """Close serial connection."""
        self.stop_reading()
        if self.serial and self.serial.is_open:
            self.serial.close()
        logger.info("Arduino connection closed")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


class MockArduinoSerial:
    """Mock Arduino for testing without hardware."""
    
    def __init__(self):
        """Initialize mock Arduino."""
        self.running = False
        self.read_thread = None
        self.callbacks = []
        self.latest_data = {
            'water_level_cm': 50,
            'water_level_percent': 30,
            'distance_raw': 50,
            'valid': True,
            'timestamp': 0,
        }
        logger.info("Using MockArduinoSerial (no hardware)")
    
    def start_reading(self):
        """Start generating mock data."""
        self.running = True
        self.read_thread = threading.Thread(target=self._mock_loop, daemon=True)
        self.read_thread.start()
    
    def stop_reading(self):
        """Stop mock data generation."""
        self.running = False
    
    def _mock_loop(self):
        """Generate mock sensor data."""
        import random
        base_level = 50
        
        while self.running:
            # Simulate gradual water level changes
            change = random.uniform(-2, 3)  # Slight upward bias
            base_level = max(10, min(95, base_level + change))
            
            # Add some noise
            level = base_level + random.uniform(-1, 1)
            
            self.latest_data = {
                'water_level_cm': 100 - level,  # Invert for distance
                'water_level_percent': level,
                'distance_raw': 100 - level,
                'valid': True,
                'timestamp': int(time.time() * 1000),
            }
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(self.latest_data)
                except Exception as e:
                    logger.error(f"Mock callback error: {e}")
            
            time.sleep(1)
    
    def get_latest(self) -> Dict:
        return self.latest_data.copy()
    
    def get_water_level(self) -> Optional[float]:
        return self.latest_data['water_level_cm']
    
    def get_water_level_percent(self) -> Optional[float]:
        return self.latest_data['water_level_percent']
    
    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def calibrate_empty(self):
        logger.info("Mock: calibrate_empty")
        return True
    
    def calibrate_full(self):
        logger.info("Mock: calibrate_full")
        return True
    
    def close(self):
        self.stop_reading()


def get_arduino(mock: bool = False) -> ArduinoSerial:
    """
    Get Arduino interface (real or mock).
    
    Args:
        mock: If True, return mock interface for testing
        
    Returns:
        ArduinoSerial or MockArduinoSerial instance
    """
    if mock:
        return MockArduinoSerial()
    
    try:
        arduino = ArduinoSerial()
        if arduino.serial is not None:
            return arduino
    except Exception as e:
        logger.warning(f"Failed to connect to real Arduino: {e}")
    
    logger.info("Falling back to mock Arduino")
    return MockArduinoSerial()


def test_arduino():
    """Test Arduino connection."""
    print("Testing Arduino connection...")
    print("Press Ctrl+C to stop\n")
    
    arduino = get_arduino(mock=False)
    arduino.start_reading()
    
    try:
        while True:
            data = arduino.get_latest()
            print(f"Water Level: {data['water_level_percent']:.1f}% | "
                  f"Distance: {data['water_level_cm']:.1f} cm | "
                  f"Valid: {data['valid']}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest complete")
    finally:
        arduino.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_arduino()
