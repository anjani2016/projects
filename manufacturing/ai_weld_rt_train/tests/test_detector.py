import pytest
from unittest.mock import patch, MagicMock
from src.detection.detector import WeldDetector
import numpy as np

@patch("src.detection.detector.YOLO")
def test_detector_initialization(mock_yolo):
    detector = WeldDetector(model_id="dummy_model.pt")
    # Using the path handling in the code, it uses model_id if passed
    mock_yolo.assert_called_once_with("dummy_model.pt")
    assert detector.model == mock_yolo.return_value.to.return_value

@patch("src.detection.detector.YOLO")
def test_detect(mock_yolo):
    # Setup mock return values for YOLO model
    mock_model = MagicMock()
    # model.names dictionary
    mock_model.names = {0: 'porosity', 1: 'crack'}
    
    # Mock result object with bounding boxes
    mock_box1 = MagicMock()
    mock_box1.cls = [0]
    mock_xyxy = MagicMock()
    mock_xyxy.tolist.return_value = [10.0, 20.0, 30.0, 40.0]
    mock_box1.xyxy = [mock_xyxy]
    mock_box1.conf = [0.85]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box1]
    
    mock_model.predict.return_value = [mock_result]
    
    # When YOLO is instantiated, return our mocked model
    mock_yolo.return_value.to.return_value = mock_model
    
    detector = WeldDetector(model_id="dummy.pt")
    # Provide a dummy 3-channel image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    detections = detector.detect(img)
    
    assert len(detections) == 1
    assert detections[0]["type"] == "porosity"
    assert detections[0]["confidence"] == 0.85
    assert detections[0]["bbox"] == [10.0, 20.0, 30.0, 40.0]
    assert detections[0]["dims"]["length"] == 20.0

@patch("src.detection.detector.YOLO")
def test_detector_read_only_names(mock_yolo):
    """
    Verify that if YOLO.names is a read-only property (raising AttributeError on assignment),
    WeldDetector handles the exception gracefully using our dictionary mutation backup.
    """
    # Create a mock class with a read-only property returning a mutable dict
    class ReadOnlyMock:
        def __init__(self):
            self._names = {0: 'пора'}
            
        @property
        def names(self):
            return self._names

    read_only_obj = ReadOnlyMock()
    mock_yolo.return_value.to.return_value = read_only_obj
    
    # This should initialize without crashing by falling back to dictionary mutation
    detector = WeldDetector(model_id="ru_model.pt")
    
    # Assert that the dictionary was updated in-place successfully to English
    assert detector.model.names[0] == "porosity"
