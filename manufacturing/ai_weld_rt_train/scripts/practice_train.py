from ultralytics import YOLO
import os

def start_training():
    # 1. Load the model we discussed (Foundational Model)
    model_path = os.path.join('..', 'weights', 'welding_defects_yolo11x.pt')
    model = YOLO(model_path)

    # 2. Run Training
    # We point to 'weld_config.yaml' which maps our images
    model.train(
        data='../weld_config.yaml', 
        epochs=50,          # Increased epochs for actual learning
        imgsz=640,          # Standard resolution for NDT X-rays
        batch=16,           # Adjust based on your GPU/RAM
        name='weld_inspection_v1'
    )

if __name__ == "__main__":
    start_training()