#!/usr/bin/env python3
"""
DrainSentinel: Calibration Wizard

Interactive calibration tool for setting up the ultrasonic sensor
and camera for your specific drain location.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

logger = logging.getLogger('DrainSentinel.Calibrate')


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print calibration header."""
    print("=" * 60)
    print("    DrainSentinel Calibration Wizard")
    print("=" * 60)
    print()


def wait_for_enter(message="Press Enter to continue..."):
    """Wait for user to press Enter."""
    input(message)


def get_float_input(prompt, default=None):
    """Get a float value from user input."""
    while True:
        try:
            value = input(prompt)
            if value == '' and default is not None:
                return default
            return float(value)
        except ValueError:
            print("Please enter a valid number.")


def run_calibration():
    """Run the interactive calibration wizard."""
    clear_screen()
    print_header()
    
    print("This wizard will help you calibrate DrainSentinel for your")
    print("specific drain location.\n")
    print("You'll need:")
    print("  - The system installed at the drain location")
    print("  - The ultrasonic sensor mounted pointing at the water")
    print("  - The camera pointed at the drain entrance")
    print()
    wait_for_enter()
    
    # Check if we can import GPIO
    try:
        from ultrasonic import UltrasonicSensor
        sensor = UltrasonicSensor()
        has_sensor = True
    except Exception as e:
        print(f"Warning: Could not initialize sensor: {e}")
        print("Calibration will be done with manual values.\n")
        has_sensor = False
        sensor = None
    
    calibration = {}
    
    # Step 1: Measure empty drain distance
    clear_screen()
    print_header()
    print("STEP 1: Empty Drain Baseline")
    print("-" * 40)
    print()
    print("Make sure the drain is empty or at its normal water level.")
    print("This will be your 0% water level reference.")
    print()
    
    if has_sensor:
        wait_for_enter("Press Enter when the drain is at normal level...")
        
        print("\nTaking measurements...")
        readings = []
        for i in range(10):
            d = sensor.get_distance()
            if d is not None:
                readings.append(d)
                print(f"  Reading {i+1}: {d:.1f} cm")
            time.sleep(0.3)
        
        if readings:
            avg = sum(readings) / len(readings)
            print(f"\nAverage distance (empty): {avg:.1f} cm")
            calibration['empty_distance'] = round(avg, 1)
        else:
            print("\nNo readings obtained. Enter manually:")
            calibration['empty_distance'] = get_float_input("Empty distance (cm): ", 100)
    else:
        print("Enter the distance from sensor to water when drain is empty:")
        calibration['empty_distance'] = get_float_input("Empty distance (cm): ", 100)
    
    print()
    wait_for_enter()
    
    # Step 2: Define critical level
    clear_screen()
    print_header()
    print("STEP 2: Critical Water Level")
    print("-" * 40)
    print()
    print("Define the critical water level - the point at which flooding")
    print("is imminent and alerts should be sent.")
    print()
    print(f"Your empty distance is: {calibration['empty_distance']} cm")
    print()
    print("The critical level should be a SMALLER distance (water closer to sensor).")
    print("Example: If empty is 100cm, critical might be 20cm or 30cm.")
    print()
    
    default_critical = calibration['empty_distance'] * 0.2  # 20% of empty
    calibration['full_distance'] = get_float_input(
        f"Critical distance (cm) [{default_critical:.1f}]: ", 
        default_critical
    )
    
    print()
    wait_for_enter()
    
    # Step 3: Verify readings
    if has_sensor:
        clear_screen()
        print_header()
        print("STEP 3: Verify Calibration")
        print("-" * 40)
        print()
        
        sensor.calibrate(
            empty_distance=calibration['empty_distance'],
            full_distance=calibration['full_distance']
        )
        
        print("Current calibration:")
        print(f"  Empty distance: {calibration['empty_distance']} cm (0%)")
        print(f"  Critical distance: {calibration['full_distance']} cm (100%)")
        print()
        print("Taking live readings to verify:")
        print()
        
        try:
            for i in range(10):
                distance = sensor.get_distance()
                percent = sensor.get_water_level_percent()
                if distance and percent is not None:
                    print(f"  Distance: {distance:6.1f} cm | Water Level: {percent:5.1f}%")
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        print()
    
    # Step 4: Alert thresholds
    clear_screen()
    print_header()
    print("STEP 4: Alert Thresholds")
    print("-" * 40)
    print()
    print("Configure when to send different alert levels:")
    print()
    
    calibration['thresholds'] = {
        'yellow': get_float_input("Yellow alert at (%) [40]: ", 40),
        'orange': get_float_input("Orange alert at (%) [60]: ", 60),
        'red': get_float_input("Red alert at (%) [80]: ", 80),
    }
    
    print()
    wait_for_enter()
    
    # Step 5: Camera test
    clear_screen()
    print_header()
    print("STEP 5: Camera Verification")
    print("-" * 40)
    print()
    
    try:
        from camera import Camera
        camera = Camera()
        
        print("Taking a test photo...")
        path = camera.capture()
        
        if path:
            print(f"Photo saved to: {path}")
            print("\nPlease verify the camera has a good view of the drain.")
        else:
            print("Failed to capture photo. Check camera connection.")
        
        camera.release()
    except Exception as e:
        print(f"Camera test skipped: {e}")
    
    print()
    wait_for_enter()
    
    # Save calibration
    clear_screen()
    print_header()
    print("STEP 6: Save Calibration")
    print("-" * 40)
    print()
    
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / 'calibration.json'
    
    print("Calibration Summary:")
    print(json.dumps(calibration, indent=2))
    print()
    
    save = input("Save this calibration? (y/n) [y]: ").lower()
    if save != 'n':
        with open(config_file, 'w') as f:
            json.dump(calibration, f, indent=2)
        print(f"\nCalibration saved to: {config_file}")
    else:
        print("\nCalibration not saved.")
    
    print()
    print("=" * 60)
    print("    Calibration Complete!")
    print("=" * 60)
    print()
    print("You can now start DrainSentinel with:")
    print("    python3 src/main.py")
    print()
    
    # Cleanup
    if has_sensor:
        sensor.cleanup()


def load_calibration():
    """Load calibration from file."""
    config_file = Path('config/calibration.json')
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load calibration: {e}")
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_calibration()
