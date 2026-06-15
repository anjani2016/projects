import pytest
import numpy as np
import cv2

@pytest.fixture
def sample_gray_image():
    """Returns a simple 100x100 grayscale noise image."""
    return np.random.randint(0, 255, (100, 100), dtype=np.uint8)

@pytest.fixture
def sample_iqi_image():
    """Returns a synthetic image with distinct lines that look like IQI wires."""
    img = np.zeros((200, 200), dtype=np.uint8)
    # Draw 4 horizontal lines long enough to pass Hough threshold of 100
    cv2.line(img, (10, 20), (180, 20), 255, 2)
    cv2.line(img, (10, 40), (180, 40), 255, 2)
    cv2.line(img, (10, 60), (180, 60), 255, 2)
    cv2.line(img, (10, 80), (180, 80), 255, 2)
    return img
