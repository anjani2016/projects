import cv2
import numpy as np

def enhance_rt_image(image_path):
    # Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced_img = clahe.apply(img)
    
    # Denoising to remove film grain while keeping defect edges
    denoised = cv2.fastNlMeansDenoising(enhanced_img, None, 10, 7, 21)
    
    return denoised

def detect_iqi_wires(image):
    # Edge detection
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Detect lines using Probabilistic Hough Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
    
    wire_count = 0
    if lines is not None:
        wire_count = len(lines)
        
    return wire_count

# Example Usage
processed_image = enhance_rt_image('weld_sample.jpg')
wires_found = detect_iqi_wires(processed_image)

if wires_found < 3: # Example threshold for ASME sensitivity
    print("WARNING: Insufficient Sensitivity. Required IQI wires not detected.")
else:
    print(f"IQI Validated: {wires_found} wires detected.")