#!/usr/bin/env python3
import os
import argparse
import logging
import yaml
import mlflow
import optuna
from types import SimpleNamespace

# Configure MLflow to use a local SQLite database to prevent filesystem tracking errors
mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Import the training function from train_pipeline
from src.training.train_pipeline import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_args():
    parser = argparse.ArgumentParser(description="Optuna Hyperparameter Optimization for Weld Radiography Model")
    parser.add_argument("--data_dir", type=str, default="data/split_folds",
                        help="Directory containing the fold dataset configs")
    parser.add_argument("--modelweights", type=str, default="weights/rtdetr-l.pt",
                        help="Initial model weights path")
    parser.add_argument("--epochs_per_trial", type=int, default=10,
                        help="Number of epochs to train in each tuning trial")
    parser.add_argument("--n_trials", type=int, default=10,
                        help="Number of HPO trials to run")
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stopping patience for each trial")
    parser.add_argument("--output_config", type=str, default="data/best_hyperparameters.yaml",
                        help="Path to save the best hyperparameters")
    parser.add_argument("--device", type=str, default=None,
                        help="Device to use for training (e.g. '0', 'cpu', 'cuda')")
    parser.add_argument("--study_name", type=str, default="weld_hpo_optimization",
                        help="Name of the Optuna study")
    return parser.parse_args()

def run_hpo():
    args = parse_args()
    
    # Set up MLflow experiment
    experiment_name = "weld_joint_hpo"
    mlflow.set_experiment(experiment_name)
    
    # We will search on fold 1 for rapid execution
    data_yaml = os.path.join(args.data_dir, "data_fold_1.yaml")
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"Dataset config {data_yaml} not found. Did you run stratified_splitter.py first?")

    # Define the objective function for Optuna
    def objective(trial):
        # 1. Define hyperparameter search space
        lr0 = trial.suggest_float("lr0", 1e-5, 1e-2, log=True)
        weight_decay = trial.suggest_float("weight_decay", 1e-4, 1e-2)
        batch = trial.suggest_categorical("batch", [16, 32, 64])
        box = trial.suggest_float("box", 2.0, 10.0)
        
        # Fixed baseline weights for other loss components (defaults)
        cls_val = 0.5
        dfl_val = 1.5
        fl_gamma_val = 0.0 # Standard training baseline, user can override manually in guide
        
        logging.info(f"\n--- Starting Optuna Trial {trial.number} ---")
        logging.info(f"Parameters: lr0={lr0:.6f}, weight_decay={weight_decay:.6f}, batch={batch}, box={box:.4f}")

        # Set up a nested MLflow run to log this trial
        run_name = f"trial_{trial.number}"
        with mlflow.start_run(run_name=run_name, nested=True) as run:
            # Log Optuna trial parameters
            mlflow.log_params({
                "trial_number": trial.number,
                "learning_rate": lr0,
                "weight_decay": weight_decay,
                "batch_size": batch,
                "box_loss_gain": box,
                "cls_loss_gain": cls_val,
                "dfl_loss_gain": dfl_val,
                "focal_loss_gamma": fl_gamma_val
            })
            
            # Construct training namespace
            train_args = SimpleNamespace(
                modelweights=args.modelweights,
                data=data_yaml,
                epochs=args.epochs_per_trial,
                imgsz=640,
                batch=batch,
                device=args.device,
                box=box,
                cls=cls_val,
                dfl=dfl_val,
                fl_gamma=fl_gamma_val,
                lr0=lr0,
                weight_decay=weight_decay,
                patience=args.patience,
                project="weld_hpo",
                name=f"trial_{trial.number}",
                mlflow_run_id=run.info.run_id
            )
            
            # 2. Train model and catch early pruning
            try:
                results = train_model(train_args, trial=trial)
                
                # Extract final validation mAP@0.5:0.95 as score
                val_map = 0.0
                if hasattr(results, 'results_dict') and results.results_dict:
                    for k, v in results.results_dict.items():
                        if "mAP50-95" in k:
                            val_map = float(v)
                            break
                            
                mlflow.log_metric("final_val_mAP50_95", val_map)
                logging.info(f"Trial {trial.number} finished with score (mAP@0.5:0.95): {val_map:.4f}")
                return val_map
                
            except optuna.TrialPruned as e:
                mlflow.set_tag("status", "pruned")
                raise e
            except Exception as e:
                logging.error(f"Trial {trial.number} failed due to training error: {e}")
                mlflow.set_tag("status", "failed")
                return 0.0

    study = optuna.create_study(
        study_name=args.study_name,
        direction="maximize",
        pruner=optuna.pruners.MedianPruner(n_startup_trials=2, n_warmup_steps=2)
    )
    
    with mlflow.start_run(run_name="optuna_hpo_parent") as parent_run:
        logging.info("Starting Hyperparameter Optimization Study...")
        study.optimize(objective, n_trials=args.n_trials)
        
        logging.info("\n--- Optimization Study Finished ---")
        logging.info(f"Number of finished trials: {len(study.trials)}")
        logging.info(f"Best trial value (mAP@0.5:0.95): {study.best_value:.4f}")
        logging.info("Best hyperparameters:")
        for k, v in study.best_params.items():
            logging.info(f"  {k}: {v}")
            
        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_val_mAP50_95", study.best_value)
        
        os.makedirs(os.path.dirname(args.output_config), exist_ok=True)
        best_config = {
            "model_type": "RT-DETR" if "rtdetr" in args.modelweights.lower() else "YOLO",
            "study_name": args.study_name,
            "best_value": float(study.best_value),
            "hyperparameters": study.best_params
        }
        with open(args.output_config, "w") as f:
            yaml.dump(best_config, f, default_flow_style=False)
        logging.info(f"Saved best parameters config to: {args.output_config}")

if __name__ == "__main__":
    run_hpo()
