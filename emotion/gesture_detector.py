import cv2
import numpy as np

class GestureDetector:
    def __init__(self):
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    
    def detect_yo_gesture(self, frame):
        """Detect 'yo' hand gesture (peace sign/victory) using skin detection"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect skin color
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return False, 0.0
        
        # Get largest contour (hand)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Hand must be large enough
        if area < 5000:
            return False, 0.0
        
        # Get convex hull and defects
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        
        # Simple yo gesture: if hand is compact and has good shape
        if hull_area > 0:
            solidity = area / hull_area
            # Yo gesture has moderate solidity (not fully open, not fully closed)
            if 0.4 < solidity < 0.8:
                return True, 0.85
        
        return False, 0.0