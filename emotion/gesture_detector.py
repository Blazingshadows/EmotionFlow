import cv2
import numpy as np


class GestureDetector:
    def __init__(self):
        """Initialize gesture detection with contour analysis"""
        # Skin color range in HSV
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    
    def detect_yo_gesture(self, frame):
        """
        Detect rock gesture (peace sign: hand with specific shape).
        Returns (is_rock_gesture, confidence)
        
        Uses contour analysis to detect if hand is in peace sign position:
        - Hand must be large enough
        - Must have specific solidity (fingers separated)
        - Shape must be consistent with two extended fingers
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect skin color
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, 
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return False, 0.0
        
        # Get largest contour (hand)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Hand must be large enough (minimum 8% of frame area)
        frame_area = frame.shape[0] * frame.shape[1]
        min_area = frame_area * 0.08
        
        if area < min_area:
            return False, 0.0
        
        # Get convex hull for shape analysis
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        if hull_area <= 0:
            return False, 0.0
        
        # Solidity = hand area / convex hull area
        # Peace sign (2 fingers extended): solidity 0.45-0.75
        # Fist (closed): solidity 0.80+
        # Open hand: solidity 0.30-0.45
        solidity = area / hull_area
        
        # Rock gesture: moderate solidity (not fully open, not fully closed)
        if 0.45 < solidity < 0.75:
            # High confidence rock gesture
            confidence = 0.85
            return True, confidence
        
        return False, 0.0