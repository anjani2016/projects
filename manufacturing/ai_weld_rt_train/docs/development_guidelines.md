# Automated Weld Radiography Analyzer — Development Guidelines & Philosophy

Welcome to the engineering guidelines for the Automated Weld Radiography Analyzer codebase. This document outlines the technical standards, defensive coding principles, and architectural philosophies that all developers (human and AI agents) must follow when contributing to this project.

---

## 🏛️ Core Philosophy: Defensive Coding & Safety First

This application is designed for **Non-Destructive Testing (NDT)** in highly critical industries (Oil & Gas pipelines, nuclear reactors, pressure vessels). An undetected structural weld defect can lead to catastrophic hardware failures and severe safety risks. 

Therefore, our primary engineering directive is: **We never fail silently, and we design for safety at every layer.**

---

## 📦 1. Layered Architecture & Separation of Concerns

The codebase is strictly separated into modular, isolated packages. This makes the system highly testable and permits swapping out detection backbones without breaking the core business rules.

```text
┌────────────────────────────────────────────────────────┐
│               PHASE 1: PRE-PROCESSING                  │
│  - Location: src/preprocessing/processor.py           │
│  - Tasks: Contrast enhancement (CLAHE), IQI checks    │
└──────────────────────────┬─────────────────────────────┘
                           │ (Clean gray image)
                           ▼
┌────────────────────────────────────────────────────────┐
│               PHASE 2: AI INFERENCE                    │
│  - Location: src/detection/detector.py                 │
│  - Tasks: Object detection & coordinate mapping        │
└──────────────────────────┬─────────────────────────────┘
                           │ (Normalized bounding boxes)
                           ▼
┌────────────────────────────────────────────────────────┐
│               PHASE 3: ENGINEERING JUDGE               │
│  - Location: src/rule_engine/engine.py                 │
│  - Tasks: Real-world calibration & ASME standards      │
└──────────────────────────┬─────────────────────────────┘
                           │ (Accept / Reject status)
                           ▼
┌────────────────────────────────────────────────────────┐
│               PHASE 4: STREAMLIT UI                    │
│  - Location: main.py                                   │
│  - Tasks: User interaction, file upload, visualization │
└────────────────────────────────────────────────────────┘
```

**Rule of Thumb**: 
*   **The AI Model is a tape measure only**: It does not decide if a weld is "Good" or "Bad". It only reports *what* is there and *how large* it is.
*   **The Rule Engine is the judge**: All business/standards logic (ASME, API, AWS) lives exclusively in `src/rule_engine/`.

---

## 🛡️ 2. Exception Handling Standards

We adhere to strict defensive programming guidelines when handling runtime errors.

### A. Safe Imports & Environment Diagnostics
Since Streamlit and PyTorch depend heavily on paths and system dependencies, all entry-point imports (like in `main.py`) must be wrapped in safe import blocks to provide actionable diagnostics to the user rather than raw tracebacks:
```python
try:
    from src.preprocessing.processor import WeldProcessor
    # ...
except ModuleNotFoundError as e:
    st.error("### 🛑 Environment Configuration Error...\n"
             "Please run the app with PYTHONPATH set: `export PYTHONPATH=$(pwd)`")
    sys.exit(1)
```

### B. Graceful Model Fallbacks
If a GPU device is out of memory (OOM) or a specialized model weight file (like `m60.pt`) fails to load due to file corruption, the code must gracefully log the traceback, switch to a safe fallback model (like `yolov8n.pt` on the CPU), and notify the operator in the UI instead of crashing.

### C. Use Custom Domain Exceptions
Avoid throwing generic python exceptions (`ValueError`, `Exception`). Define custom exceptions that document specific failure states:
```python
class NDTValidationError(Exception):
    """Base exception for NDT pipeline failures."""
    pass

class SensitivityRequirementNotMetError(NDTValidationError):
    """Raised when visible IQI wires do not meet ASME V requirements."""
    pass
```

---

## 🧪 3. Testing Mandates

All new features must be accompanied by comprehensive tests in the `tests/` directory.

1.  **Mock Heavy Dependencies**: Do not download or initialize large `.pt` weights during unit testing. Mock the Ultralytics YOLO models (or other detectors) using `unittest.mock` to ensure unit tests remain extremely fast and runnable on standard CPUs.
2.  **Negative Testing (Asserting Failures)**: Write tests that verify the system handles exceptions correctly. Use `pytest.raises` to assert that the code raises the correct custom exception when fed invalid data:
    ```python
    def test_enhance_image_not_found(processor):
        with pytest.raises(FileNotFoundError):
            processor.enhance_image("nonexistent.png")
    ```
3.  **Path and Module Health**: Include import-validation tests (`tests/test_imports.py`) to verify that all subpackages resolve correctly on disk.

---

## ⚖️ 4. Commercial Licensing Compliance

When adding new models, frameworks, or datasets, developers must comply with the commercial licensing architecture:

1.  **No Non-Commercial Data in Production**: Datasets protected under `CC BY-NC` (such as the Gazpromneft dataset) may only be used for **internal R&D, algorithm validation, and demos**. Commercial models must be trained on commercially cleared data (such as proprietary company images or public domain datasets).
2.  **Permissive Model Licenses**: To sell the product as a closed-source service (SaaS) without incurring thousands of dollars in license fees or violating AGPL copyleft triggers:
    *   Prioritize detectors with **Apache 2.0** or **MIT** licenses, such as **RT-DETR** or **YOLOv10**.
    *   Avoid using AGPL-licensed frameworks in closed-source SaaS pipelines.
