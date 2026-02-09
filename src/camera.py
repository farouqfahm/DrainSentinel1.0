#!/usr/bin/env python3
"""
DrainSentinel: Camera Module

Handles camera capture and image preprocessing for the blockage detection system.
Supports USB cameras on Raspberry Pi.
"""

import cv2
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('DrainSentinel.Camera')


class Camera:
    """Camera capture and image management."""
    
    def __init__(self, device_id=0, resolution=(1280, 720)):
        """
        Initialize the camera.
        
        Args:
            device_id: Camera device ID (usually 0 for first USB camera)
            resolution: Capture resolution (width, height)
        """
        self.device_id = device_id
        self.resolution = resolution
        self.capture_dir = Path('data/captures')
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize camera
        self.cap = None
        self._init_camera()
        
        logger.info(f"Camera initialized: device {device_id}, resolution {resolution}")
    
    def _init_camera(self):
        """Initialize the camera capture object."""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.device_id}")
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Read a test frame
            ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Failed to read test frame from camera")
            
            actual_res = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                         int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            logger.info(f"Camera actual resolution: {actual_res}")
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            self.cap = None
            raise
    
    def capture(self, save=True):
        """
        Capture a single frame from the camera.
        
        Args:
            save: Whether to save the image to disk
            
        Returns:
            Path to saved image, or None if capture failed
        """
        if self.cap is None or not self.cap.isOpened():
            logger.error("Camera not available")
            return None
        
        try:
            # Capture frame
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                logger.error("Failed to capture frame")
                return None
            
            if save:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"capture_{timestamp}.jpg"
                filepath = self.capture_dir / filename
                
                # Save image
                cv2.imwrite(str(filepath), frame)
                logger.debug(f"Captured image: {filepath}")
                
                # Also save as "latest.jpg" for dashboard
                latest_path = self.capture_dir / 'latest.jpg'
                cv2.imwrite(str(latest_path), frame)
                
                return str(filepath)
            else:
                return frame
            
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None
    
    def capture_for_ai(self, target_size=(224, 224)):
        """
        Capture and preprocess image for AI model.
        
        Args:
            target_size: Size to resize image to (width, height)
            
        Returns:
            Preprocessed numpy array, or None if failed
        """
        frame = self.capture(save=False)
        
        if frame is None:
            return None
        
        try:
            # Resize for AI model
            resized = cv2.resize(frame, target_size)
            
            # Convert BGR to RGB (OpenCV uses BGR by default)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Normalize to 0-1 range
            normalized = rgb.astype('float32') / 255.0
            
            return normalized
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def get_stream_frame(self):
        """
        Get a frame for live streaming (JPEG encoded).
        
        Returns:
            JPEG encoded bytes, or None if failed
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                return None
            
            # Resize for streaming (lower resolution for bandwidth)
            stream_size = (640, 480)
            resized = cv2.resize(frame, stream_size)
            
            # Encode as JPEG
            ret, jpeg = cv2.imencode('.jpg', resized, 
                                      [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                return None
            
            return jpeg.tobytes()
            
        except Exception as e:
            logger.error(f"Stream frame failed: {e}")
            return None
    
    def release(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            logger.info("Camera released")
    
    def __del__(self):
        """Destructor to ensure camera is released."""
        self.release()


def test_camera():
    """Test camera functionality."""
    print("Testing camera...")
    
    try:
        cam = Camera()
        
        # Test capture
        print("Capturing image...")
        path = cam.capture()
        
        if path:
            print(f"Image saved to: {path}")
            print("Camera test PASSED")
        else:
            print("Failed to capture image")
            print("Camera test FAILED")
        
        cam.release()
        
    except Exception as e:
        print(f"Camera test FAILED: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_camera()
