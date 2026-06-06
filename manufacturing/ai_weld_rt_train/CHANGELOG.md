# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Hugging Face Training Pipeline**: Introduced a complete, proprietary-friendly training pipeline using Hugging Face's `transformers` library (`scripts/train_hf_detr.py`).
- **Dataset Converter**: Added `scripts/convert_yolo_to_coco.py` to seamlessly convert YOLO formatted data into the standard COCO JSON format required by DETR architectures.
- **Dynamic UI Checklist**: The NDT Verification Checklist in `main.py` now dynamically filters out generic COCO classes (e.g., cars, bicycles) to exclusively show relevant welding defect terminology.

### Changed
- Replaced the AGPL-3.0 licensed Ultralytics RT-DETR training pipeline with an Apache 2.0 licensed Hugging Face implementation (`PekingU/rtdetr_r50vd`) to ensure 100% commercial ownership without Enterprise licensing fees.
- Reduced the CPU training pipeline data subset dynamically to prevent memory crashes during local Mac testing (100-epoch validation runs).
- Updated the User Interface to explicitly bypass the "Technical Audits & Coordinates" panel when an AI model confidently predicts a 100% clear / defect-free weld.
