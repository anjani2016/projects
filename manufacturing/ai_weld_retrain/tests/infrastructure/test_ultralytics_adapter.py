import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from src.infrastructure.adapters.ultralytics_adapter import UltralyticsAdapter
from src.core.domain.entities import Defect

@patch("src.infrastructure.adapters.ultralytics_adapter.YOLO")
def test_ultralytics_adapter_yolo_initialization(mock_yolo):
    adapter = UltralyticsAdapter(model_path="dummy_yolo.pt")
    mock_yolo.assert_called_once_with("dummy_yolo.pt")
    assert adapter.model == mock_yolo.return_value.to.return_value

@patch("src.infrastructure.adapters.ultralytics_adapter.RTDETR")
def test_ultralytics_adapter_rtdetr_initialization(mock_rtdetr):
    adapter = UltralyticsAdapter(model_path="dummy_rtdetr.pt")
    mock_rtdetr.assert_called_once_with("dummy_rtdetr.pt")
    assert adapter.model == mock_rtdetr.return_value.to.return_value

@patch("src.infrastructure.adapters.ultralytics_adapter.YOLO")
def test_ultralytics_adapter_detection(mock_yolo):
    # Setup mock return values for YOLO model
    mock_model = MagicMock()
    del mock_model.model
    mock_model.names = {0: 'пора', 1: 'трещина'}
    
    # Mock result object with bounding boxes
    mock_box1 = MagicMock()
    mock_box1.cls = [0]
    mock_box1.conf = [0.85]
    
    mock_xyxy = MagicMock()
    mock_xyxy.tolist.return_value = [10.0, 20.0, 30.0, 40.0]
    mock_box1.xyxy = [mock_xyxy]
    
    mock_result = MagicMock()
    mock_result.boxes = [mock_box1]
    mock_model.predict.return_value = [mock_result]
    
    # When YOLO is instantiated, return our mocked model
    mock_yolo.return_value.to.return_value = mock_model
    
    adapter = UltralyticsAdapter(model_path="dummy.pt")
    # Provide a dummy grayscale image
    img = np.zeros((100, 100), dtype=np.uint8)
    
    detections = adapter.detect(img)
    
    assert len(detections) == 1
    # Should be translated to English "porosity"
    assert detections[0].type == "porosity"
    assert detections[0].confidence == 0.85
    assert detections[0].bbox == [10.0, 20.0, 30.0, 40.0]
    assert detections[0].dims["length"] == 20.0  # 30 - 10

@patch("src.infrastructure.adapters.ultralytics_adapter.YOLO")
def test_ultralytics_adapter_read_only_names(mock_yolo):
    """
    Verify that if model.names is a read-only property,
    UltralyticsAdapter handles the exception gracefully.
    """
    class ReadOnlyMock:
        def __init__(self):
            self._names = {0: 'пора'}
            
        @property
        def names(self):
            return self._names

    read_only_obj = ReadOnlyMock()
    mock_yolo.return_value.to.return_value = read_only_obj
    
    # This should initialize without crashing
    adapter = UltralyticsAdapter(model_path="ru_model.pt")
    assert adapter.model.names[0] == "porosity"

@patch("src.infrastructure.adapters.ultralytics_adapter.os.path.isdir")
@patch("src.infrastructure.adapters.ultralytics_adapter.os.path.exists")
@patch("src.infrastructure.adapters.ultralytics_adapter.AutoImageProcessor")
@patch("src.infrastructure.adapters.ultralytics_adapter.AutoModelForObjectDetection")
def test_ultralytics_adapter_hf_model(mock_hf_model_class, mock_hf_proc_class, mock_exists, mock_isdir):
    # Setup mock file structure to identify HF model
    mock_isdir.return_value = True
    mock_exists.return_value = True
    
    # Mock return values for processor and model
    mock_processor = MagicMock()
    mock_hf_proc_class.from_pretrained.return_value = mock_processor
    
    mock_model = MagicMock()
    mock_model.config.id2label = {0: "porosity", 1: "crack"}
    mock_hf_model_class.from_pretrained.return_value.to.return_value = mock_model
    
    adapter = UltralyticsAdapter(model_path="dummy_hf_checkpoint")
    assert adapter.is_hf is True
    
    # Mock detection outputs
    img = np.zeros((100, 100), dtype=np.uint8)
    
    import torch
    mock_processor.post_process_object_detection.return_value = [{
        "scores": torch.tensor([0.9]),
        "labels": torch.tensor([0]),
        "boxes": torch.tensor([[10.0, 20.0, 30.0, 40.0]])
    }]
    
    detections = adapter.detect(img)
    assert len(detections) == 1
    assert detections[0].type == "porosity"
    assert detections[0].confidence == pytest.approx(0.9)
    assert detections[0].bbox == [10.0, 20.0, 30.0, 40.0]

