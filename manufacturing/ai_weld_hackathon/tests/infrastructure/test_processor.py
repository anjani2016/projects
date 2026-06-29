import pytest
import cv2
import numpy as np
from src.preprocessing.processor import WeldProcessor

@pytest.fixture
def processor():
    return WeldProcessor()

def test_enhance_image(processor, tmp_path):
    # Create a dummy image
    img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    # Save it temporarily
    img_path = tmp_path / "dummy.png"
    cv2.imwrite(str(img_path), img)
    
    enhanced = processor.enhance_image(str(img_path))
    assert enhanced is not None
    assert enhanced.shape == (100, 100)
    assert enhanced.dtype == np.uint8

def test_enhance_image_not_found(processor):
    with pytest.raises(FileNotFoundError):
        processor.enhance_image("nonexistent_image.png")

def test_verify_iqi(processor, sample_iqi_image):
    # sample_iqi_image has 4 distinct lines, should pass
    is_valid, count = processor.verify_iqi(sample_iqi_image)
    assert is_valid is True
    assert count >= 3

    # An empty image will definitely have 0 lines
    is_valid, count = processor.verify_iqi(np.zeros((100, 100), dtype=np.uint8))
    assert is_valid is False
    assert count == 0
