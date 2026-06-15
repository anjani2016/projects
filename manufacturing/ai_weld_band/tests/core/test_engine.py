import pytest
from src.rule_engine.engine import WeldEngine

@pytest.fixture
def engine():
    return WeldEngine(standard="ASME_B31.3")

def test_engine_calibration(engine):
    # If 10 pixels = 0.8 mm, ratio is 0.08 mm/px
    ratio = engine.calibrate(reference_px=10, physical_mm=0.8)
    assert ratio == 0.08
    assert engine.get_mm(100) == 8.0

def test_validate_defect_crack(engine):
    # Crack is zero tolerance
    passed, msg = engine.validate_defect("crack", {"length": 1.0}, wall_thickness=10.0)
    assert not passed
    assert "REJECT" in msg
    assert "Zero Tolerance" in msg

def test_validate_defect_slag(engine):
    # Slag limit is T / 3. For T=10, limit is 3.333
    passed, msg = engine.validate_defect("slag", {"length": 3.0}, wall_thickness=10.0)
    assert passed
    assert msg == "ACCEPT"

    passed, msg = engine.validate_defect("slag", {"length": 4.0}, wall_thickness=10.0)
    assert not passed
    assert "REJECT" in msg
    assert "Exceeds T/3" in msg

def test_validate_defect_porosity(engine):
    # Porosity limit is min(6.0, T/4). For T=10, limit is 2.5
    passed, msg = engine.validate_defect("porosity", {"length": 2.0}, wall_thickness=10.0)
    assert passed

    passed, msg = engine.validate_defect("porosity", {"length": 3.0}, wall_thickness=10.0)
    assert not passed
    assert "Exceeds rounded indication" in msg

def test_validate_defect_lop(engine):
    # LOP limit is min(3.0, 0.2*T). For T=20, limit is min(3.0, 4.0) = 3.0
    passed, msg = engine.validate_defect("lop", {"length": 2.5}, wall_thickness=20.0)
    assert passed

    passed, msg = engine.validate_defect("lop", {"length": 3.5}, wall_thickness=20.0)
    assert not passed

def test_validate_unimplemented_standard():
    engine = WeldEngine(standard="UNKNOWN_STANDARD")
    passed, msg = engine.validate_defect("slag", {"length": 1.0}, wall_thickness=10.0)
    assert not passed
    assert msg == "Standard Not Found"

def test_validate_sec_viii_fallback():
    """Verify that ASME Section VIII placeholder standard correctly resolves without NoneType crashes."""
    engine = WeldEngine(standard="ASME_SEC_VIII")
    
    # Check accepted defect (passes slag threshold 1.0 < 3.33)
    passed, msg = engine.validate_defect("slag", {"length": 1.0}, wall_thickness=10.0)
    assert passed is True
    assert "ASME Sec VIII Placeholder check passed" in msg
    
    # Check rejected defect (exceeds slag threshold 5.0 > 3.33)
    passed, msg = engine.validate_defect("slag", {"length": 5.0}, wall_thickness=10.0)
    assert passed is False
    assert "REJECT: SLAG" in msg
