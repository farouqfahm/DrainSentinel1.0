#!/usr/bin/env python3
"""
DrainSentinel: AI Blockage Detection Module

Handles loading and running the Edge Impulse model for drain blockage detection.
Supports both the Metis AI accelerator and CPU-only inference.
"""

import cv2
import logging
import numpy as np
import os
from pathlib import Path

logger = logging.getLogger('DrainSentinel.AI')

# Try to import Edge Impulse SDK
try:
    from edge_impulse_linux.image import ImageImpulseRunner
    EDGE_IMPULSE_AVAILABLE = True
except ImportError:
    logger.warning("Edge Impulse SDK not available - using mock detector")
    EDGE_IMPULSE_AVAILABLE = False


class BlockageDetector:
    """AI-based drain blockage detection using Edge Impulse."""
    
    # Class labels
    LABELS = ['clear', 'partial_blockage', 'full_blockage']
    
    def __init__(self, model_path=None):
        """
        Initialize the blockage detector.
        
        Args:
            model_path: Path to the .eim model file. If None, uses default location.
        """
        if model_path is None:
            model_path = Path('models/drain_blockage.eim')
        
        self.model_path = Path(model_path)
        self.runner = None
        self.input_size = (224, 224)  # Default, will be updated from model
        
        self._init_model()
        logger.info("BlockageDetector initialized")
    
    def _init_model(self):
        """Initialize the Edge Impulse model."""
        if not EDGE_IMPULSE_AVAILABLE:
            logger.warning("Edge Impulse not available - using mock predictions")
            return
        
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            logger.info("Run 'edge-impulse-linux-runner --download' to get the model")
            return
        
        try:
            self.runner = ImageImpulseRunner(str(self.model_path))
            model_info = self.runner.init()
            
            # Get model metadata
            self.input_size = (
                model_info['model_parameters']['image_input_width'],
                model_info['model_parameters']['image_input_height']
            )
            
            logger.info(f"Model loaded: {model_info['project']['name']}")
            logger.info(f"Input size: {self.input_size}")
            logger.info(f"Labels: {model_info['model_parameters']['labels']}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.runner = None
    
    def preprocess_image(self, image_path):
        """
        Load and preprocess an image for inference.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed numpy array, or None if failed
        """
        try:
            # Load image
            img = cv2.imread(str(image_path))
            
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Resize to model input size
            img = cv2.resize(img, self.input_size)
            
            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            return img
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def detect(self, image_input):
        """
        Run blockage detection on an image.
        
        Args:
            image_input: Either a file path (str/Path) or a numpy array
            
        Returns:
            Dictionary with:
                - blocked: Boolean indicating if blockage detected
                - confidence: Confidence score (0-1)
                - class_name: Predicted class name
                - all_scores: Dictionary of all class scores
        """
        # Handle input type
        if isinstance(image_input, (str, Path)):
            img = self.preprocess_image(image_input)
        else:
            img = image_input
        
        if img is None:
            return self._default_result()
        
        # Use mock detector if Edge Impulse not available
        if self.runner is None:
            return self._mock_detect(img)
        
        try:
            # Run inference
            features = self.runner.get_features_from_image(img)
            result = self.runner.classify(features)
            
            # Parse results
            classifications = result['result']['classification']
            
            # Find best class
            best_class = max(classifications, key=classifications.get)
            best_score = classifications[best_class]
            
            # Determine if blocked
            blocked = best_class in ['partial_blockage', 'full_blockage']
            
            return {
                'blocked': blocked,
                'confidence': best_score,
                'class_name': best_class,
                'all_scores': classifications,
                'inference_time_ms': result['timing']['classification'],
            }
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return self._default_result()
    
    def _mock_detect(self, img):
        """
        Mock detection when Edge Impulse is not available.
        Uses simple image analysis as a placeholder.
        """
        import random
        
        # Simple mock based on image brightness
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        brightness = np.mean(gray)
        
        # Lower brightness = more likely blocked (debris blocks light)
        blockage_probability = 1 - (brightness / 255)
        
        # Add some randomness
        blockage_probability += random.uniform(-0.2, 0.2)
        blockage_probability = max(0, min(1, blockage_probability))
        
        if blockage_probability > 0.7:
            class_name = 'full_blockage'
        elif blockage_probability > 0.4:
            class_name = 'partial_blockage'
        else:
            class_name = 'clear'
        
        blocked = class_name != 'clear'
        
        return {
            'blocked': blocked,
            'confidence': blockage_probability if blocked else (1 - blockage_probability),
            'class_name': class_name,
            'all_scores': {
                'clear': 1 - blockage_probability,
                'partial_blockage': blockage_probability * 0.6,
                'full_blockage': blockage_probability * 0.4,
            },
            'inference_time_ms': 50,  # Mock timing
            'mock': True,
        }
    
    def _default_result(self):
        """Return default result for failed detection."""
        return {
            'blocked': False,
            'confidence': 0.0,
            'class_name': 'unknown',
            'all_scores': {},
            'error': True,
        }
    
    def close(self):
        """Release model resources."""
        if self.runner is not None:
            self.runner.stop()
            logger.info("Model runner stopped")
    
    def __del__(self):
        """Destructor to ensure model is closed."""
        self.close()


class SimpleBlockageDetector:
    """
    Simplified blockage detector using OpenCV (no AI required).
    
    Uses color analysis and edge detection as a fallback when
    Edge Impulse is not available or for quick testing.
    """
    
    def __init__(self):
        """Initialize the simple detector."""
        logger.info("SimpleBlockageDetector initialized (OpenCV-based)")
    
    def detect(self, image_path):
        """
        Detect blockage using simple image analysis.
        
        Looks for:
        1. Dark regions (debris)
        2. Unusual colors (trash, leaves)
        3. Texture changes (water vs. debris)
        """
        try:
            img = cv2.imread(str(image_path))
            
            if img is None:
                return {'blocked': False, 'confidence': 0, 'error': True}
            
            # Convert to different color spaces
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Analyze darkness (blocked drains often darker)
            mean_brightness = np.mean(gray)
            darkness_score = 1 - (mean_brightness / 255)
            
            # Analyze color variance (debris has varied colors)
            h, s, v = cv2.split(hsv)
            color_variance = np.std(h) / 90  # Normalize to 0-1
            
            # Analyze edges (debris has more edges than water)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Combine scores
            blockage_score = (
                0.4 * darkness_score +
                0.3 * color_variance +
                0.3 * min(1.0, edge_density * 10)
            )
            
            # Determine class
            if blockage_score > 0.6:
                class_name = 'full_blockage'
            elif blockage_score > 0.35:
                class_name = 'partial_blockage'
            else:
                class_name = 'clear'
            
            blocked = class_name != 'clear'
            
            return {
                'blocked': blocked,
                'confidence': blockage_score if blocked else (1 - blockage_score),
                'class_name': class_name,
                'all_scores': {
                    'darkness': darkness_score,
                    'color_variance': color_variance,
                    'edge_density': edge_density,
                },
                'simple_detector': True,
            }
            
        except Exception as e:
            logger.error(f"Simple detection failed: {e}")
            return {'blocked': False, 'confidence': 0, 'error': True}


def test_detector():
    """Test the blockage detector."""
    print("Testing blockage detector...")
    
    detector = BlockageDetector()
    
    # Test with a sample image
    test_images = list(Path('data/captures').glob('*.jpg'))
    
    if not test_images:
        print("No test images found in data/captures/")
        print("Capture some images first with: python3 camera.py")
        return
    
    for img_path in test_images[:3]:
        print(f"\nAnalyzing: {img_path.name}")
        result = detector.detect(img_path)
        
        print(f"  Blocked: {result['blocked']}")
        print(f"  Class: {result['class_name']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        
        if 'all_scores' in result:
            print(f"  Scores: {result['all_scores']}")
    
    detector.close()
    print("\nTest complete")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_detector()
