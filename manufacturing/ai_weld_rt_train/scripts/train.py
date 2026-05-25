# scripts/train.py
import os
import torch
import logging
from ultralytics import YOLO

# Set up logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def train_custom_model(config_name="visual_welding_defect_dataset.yaml", epochs=50, batch_size=16):
    """
    Step-by-step training runner for custom weld defect detection models.
    Supports CPU, NVIDIA GPU (CUDA), and Apple Silicon GPU (MPS) acceleration.
    """
    logging.info("=== Starting Custom YOLO Training Pipeline ===")
    
    # 1. Resolve paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "configs", config_name)
    foundation_model_path = os.path.join(project_root, "weights", "welding_defects_yolo11x.pt")
    fallback_model_path = os.path.join(project_root, "yolov8n.pt")
    
    # Verify dataset configuration exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Dataset configuration YAML not found at: {config_path}")
    
    # 2. Hardware Acceleration Detection (Crucial for Mac)
    if torch.cuda.is_available():
        device = "0"  # NVIDIA GPU
        logging.info("Detected NVIDIA GPU (CUDA). Running on GPU 0.")
    elif torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon GPU (Metal)
        logging.info("Detected Apple Silicon GPU (MPS). Running with Metal acceleration.")
    else:
        device = "cpu"  # CPU Fallback
        logging.warning("No GPU hardware acceleration detected. Falling back to CPU training.")

    # 3. Select starting weights
    if os.path.exists(foundation_model_path):
        starting_weights = foundation_model_path
        logging.info(f"Loading pre-trained foundation weights from: {foundation_model_path}")
    else:
        starting_weights = fallback_model_path
        logging.info(f"Foundation weights not found. Initializing with default model: {fallback_model_path}")

    # Load YOLO Model
    model = YOLO(starting_weights)

    # 4. Run Training
    logging.info(f"Initiating training on dataset: {config_name}")
    logging.info(f"Hyperparameters -> Epochs: {epochs}, Batch Size: {batch_size}, Device: {device}")
    
    # Train using Ultralytics engine
    results = model.train(
        data=config_path,
        epochs=epochs,
        batch=batch_size,
        imgsz=640,             # Standard high resolution for NDT radiography details
        device=device,
        project=os.path.join(project_root, "runs"),
        name=config_name.replace(".yaml", "_run"),
        save=True,             # Save checkpoints
        plots=True             # Generate loss/accuracy graphs
    )
    
    logging.info("=== Training Completed Successfully ===")
    
    # Locate output weights
    run_dir = os.path.join(project_root, "runs", config_name.replace(".yaml", "_run"))
    best_weights = os.path.join(run_dir, "weights", "best.pt")
    
    if os.path.exists(best_weights):
        logging.info(f"🏆 Best model weights saved at: {best_weights}")
        logging.info(f"To use this model in Streamlit, move it to weights/{config_name.replace('.yaml', '')}/best.pt")
    else:
        logging.warning(f"Could not locate best.pt in run directory: {run_dir}")

if __name__ == "__main__":
    # You can change config_name to train other datasets (e.g. gazpromneft_kaggle.yaml)
    train_custom_model(config_name="visual_welding_defect_dataset.yaml", epochs=50, batch_size=16)
