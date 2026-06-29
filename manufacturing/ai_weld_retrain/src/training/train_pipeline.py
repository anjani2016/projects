#!/usr/bin/env python3
import os
import argparse
import logging
import torch
from ultralytics import YOLO, RTDETR
import mlflow

# Configure MLflow to use a local SQLite database to prevent filesystem tracking errors
mlflow.set_tracking_uri("sqlite:///mlflow.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global state to track custom early stopping metrics
class OverfitMonitor:
    def __init__(self, patience=10):
        self.patience = patience
        self.best_val_loss = float('inf')
        self.val_loss_no_improve_epochs = 0
        
        self.train_loss_history = []
        self.val_loss_history = []
        
    def check_overfitting(self, trainer):
        # 1. Get current train and val losses
        if not hasattr(trainer, 'loss_items') or trainer.loss_items is None:
            return False
            
        train_loss = sum([float(x) for x in trainer.loss_items])
        
        # Check if validation ran and validator exists
        if not hasattr(trainer, 'validator') or trainer.validator is None:
            return False
            
        if not hasattr(trainer.validator, 'loss_items') or trainer.validator.loss_items is None:
            return False
            
        val_loss = sum([float(x) for x in trainer.validator.loss_items])
        
        self.train_loss_history.append(train_loss)
        self.val_loss_history.append(val_loss)
        
        epoch = trainer.epoch
        logging.info(f"Epoch {epoch}: Train Loss = {train_loss:.4f}, Val Loss = {val_loss:.4f}")
        
        # We need at least some epochs to detect a trend
        if len(self.train_loss_history) < 2:
            return False
            
        # 2. Check if validation loss is improving
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.val_loss_no_improve_epochs = 0
        else:
            self.val_loss_no_improve_epochs += 1
            
        # 3. Check if training loss is generally decreasing
        # We compare the average loss of the last few epochs or just check if it decreased
        recent_train_decreased = train_loss < self.train_loss_history[-2]
        
        # Overfitting criteria:
        # - Validation loss has not improved for 'patience' epochs
        # - Training loss has decreased (is lower than the previous epoch, showing gradient updates are active)
        if self.val_loss_no_improve_epochs >= self.patience:
            window = self.patience
            train_window = self.train_loss_history[-window:]
            val_window = self.val_loss_history[-window:]
            
            # Simple check: is the train loss overall decreasing in this window, while val loss is not?
            train_trend = train_window[-1] < train_window[0]
            val_trend = val_window[-1] >= min(self.val_loss_history[:-window] + [self.best_val_loss])
            
            if train_trend and val_trend:
                logging.warning(
                    f"\n[EARLY STOPPING TRIGGERED] Overfitting signature detected at epoch {epoch}!"
                    f"\n  - Training loss decreased from {train_window[0]:.4f} to {train_window[-1]:.4f}."
                    f"\n  - Validation loss failed to improve for {self.val_loss_no_improve_epochs} epochs."
                    f"\n  - Best Validation Loss: {self.best_val_loss:.4f}"
                )
                return True
                
        return False

# Instantiate monitor globally so callbacks can reference it
overfit_monitor = None
optuna_trial = None
fl_gamma_val = 0.0

def register_custom_callbacks(model, patience, fl_gamma, trial=None):
    """Registers custom MLflow and early stopping callbacks on the trainer."""
    global overfit_monitor, optuna_trial, fl_gamma_val
    overfit_monitor = OverfitMonitor(patience=patience)
    optuna_trial = trial
    fl_gamma_val = fl_gamma
    
    # Callback triggered right before training loop starts, after criterion initialization
    def on_pretrain_routine_end(trainer):
        global fl_gamma_val
        if fl_gamma_val > 0.0:
            logging.info(f"\n[FOCAL LOSS CALLBACK] Dynamically patching training loss to use Focal Loss (gamma={fl_gamma_val})")
            from ultralytics.utils.loss import FocalLoss
            
            # 1. Patch standard YOLO detection criterion
            if hasattr(trainer, 'criterion') and trainer.criterion:
                criterion = trainer.criterion
                if hasattr(criterion, 'bce'):
                    # Replace standard BCEWithLogitsLoss with FocalLoss wrapper
                    criterion.bce = FocalLoss(gamma=fl_gamma_val, alpha=0.25)
                    logging.info("[FOCAL LOSS CALLBACK] Successfully patched YOLO criterion.bce with FocalLoss")
                
                # 2. Patch RT-DETR loss criterion
                if hasattr(criterion, 'fl'):
                    criterion.fl = FocalLoss(gamma=fl_gamma_val, alpha=0.25)
                    logging.info("[FOCAL LOSS CALLBACK] Successfully patched RT-DETR criterion.fl with FocalLoss")
    
    # Callback triggered after training and validation end for an epoch
    def on_fit_epoch_end(trainer):
        global overfit_monitor, optuna_trial
        epoch = trainer.epoch
        
        # --- 1. Custom Overfitting Monitor & Early Stopping ---
        if overfit_monitor.check_overfitting(trainer):
            trainer.stop = True  # Tell Ultralytics to stop training cleanly
            
        # --- 2. Log Metrics to MLflow ---
        if mlflow.active_run():
            # Train losses
            loss_list = [float(x) for x in trainer.loss_items]
            if len(loss_list) >= 3:
                mlflow.log_metric("train/box_loss", loss_list[0], step=epoch)
                mlflow.log_metric("train/cls_loss", loss_list[1], step=epoch)
                mlflow.log_metric("train/dfl_loss", loss_list[2], step=epoch)
                mlflow.log_metric("train/total_loss", sum(loss_list), step=epoch)
            
            # Val losses
            if hasattr(trainer, 'validator') and trainer.validator and hasattr(trainer.validator, 'loss_items') and trainer.validator.loss_items is not None:
                val_loss_list = [float(x) for x in trainer.validator.loss_items]
                if len(val_loss_list) >= 3:
                    mlflow.log_metric("val/box_loss", val_loss_list[0], step=epoch)
                    mlflow.log_metric("val/cls_loss", val_loss_list[1], step=epoch)
                    mlflow.log_metric("val/dfl_loss", val_loss_list[2], step=epoch)
                    mlflow.log_metric("val/total_loss", sum(val_loss_list), step=epoch)
            
            # Validation metrics
            if hasattr(trainer, 'metrics') and trainer.metrics:
                for k, v in trainer.metrics.items():
                    # Strip "metrics/" and "(B)" prefix/suffix for clean plotting
                    clean_k = k.replace("metrics/", "").replace("(B)", "")
                    mlflow.log_metric(f"metrics/{clean_k}", float(v), step=epoch)
            
            # Learning rates
            if hasattr(trainer, 'lr') and trainer.lr:
                for i, lr_val in enumerate(trainer.lr):
                    mlflow.log_metric(f"lr/pg{i}", float(lr_val), step=epoch)
                    
        # --- 3. Report to Optuna for Median Pruning ---
        if optuna_trial is not None:
            # Optuna uses validation mAP@0.5:0.95 (represented as metrics/mAP50-95(B)) as objective
            val_map = 0.0
            if hasattr(trainer, 'metrics') and trainer.metrics:
                for k, v in trainer.metrics.items():
                    if "mAP50-95" in k:
                        val_map = float(v)
                        break
            
            optuna_trial.report(val_map, epoch)
            
            # Check if this trial should be pruned early
            if optuna_trial.should_prune():
                logging.warning(f"Optuna Trial {optuna_trial.number} PRUNED at epoch {epoch}.")
                import optuna
                raise optuna.TrialPruned()

    model.add_callback("on_pretrain_routine_end", on_pretrain_routine_end)
    model.add_callback("on_fit_epoch_end", on_fit_epoch_end)

def parse_args():
    parser = argparse.ArgumentParser(description="Custom Weld Joint Model Training Pipeline")
    parser.add_argument("--modelweights", type=str, default="weights/rtdetr-l.pt",
                        help="Initial model weights path (e.g. weights/rtdetr-l.pt, weights/welding_defects_yolo11x.pt)")
    parser.add_argument("--data", type=str, default="data/split_folds/data_fold_1.yaml",
                        help="Path to YOLO dataset yaml config file")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of epochs to train")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Training image size")
    parser.add_argument("--batch", type=int, default=16,
                        help="Training batch size")
    parser.add_argument("--device", type=str, default=None,
                        help="Device to use for training (e.g., '0', 'cpu', 'cuda')")
    parser.add_argument("--box", type=float, default=7.5,
                        help="Bounding box loss gain (lambda_box)")
    parser.add_argument("--cls", type=float, default=0.5,
                        help="Classification loss gain (lambda_cls)")
    parser.add_argument("--dfl", type=float, default=1.5,
                        help="Distribution focal loss gain (lambda_dfl)")
    parser.add_argument("--fl_gamma", type=float, default=0.0,
                        help="Focal Loss gamma for classification (set > 0, e.g. 2.0 to activate)")
    parser.add_argument("--lr0", type=float, default=0.01,
                        help="Initial learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.0005,
                        help="Optimizer weight decay")
    parser.add_argument("--patience", type=int, default=10,
                        help="Epochs to wait for early stopping (overfitting monitor)")
    parser.add_argument("--project", type=str, default="weld_retrain",
                        help="YOLO save project directory")
    parser.add_argument("--name", type=str, default="rtdetr_fold_1",
                        help="YOLO run name")
    parser.add_argument("--mlflow_run_id", type=str, default=None,
                        help="Internal run ID if managed by outer Optuna loop")
    return parser.parse_args()

def train_model(args, trial=None):
    # Determine device automatically if not specified
    if args.device is None:
        device = 0 if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
        
    logging.info(f"Using device: {device}")
    logging.info(f"Hyperparameters: lambda_box={args.box}, lambda_cls={args.cls}, lambda_dfl={args.dfl}, fl_gamma={args.fl_gamma}")
    logging.info(f"Optimizer: lr0={args.lr0}, weight_decay={args.weight_decay}, batch_size={args.batch}")

    # Load appropriate Ultralytics model wrapper
    is_rtdetr = "rtdetr" in args.modelweights.lower()
    
    if is_rtdetr:
        logging.info("Initializing RT-DETR model...")
        model = RTDETR(args.modelweights)
    else:
        logging.info("Initializing YOLO model...")
        model = YOLO(args.modelweights)

    # Register our custom telemetry, early stopping, and focal loss callbacks
    register_custom_callbacks(model, args.patience, args.fl_gamma, trial=trial)
    
    # Run training
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        box=args.box,
        cls=args.cls,
        dfl=args.dfl,
        lr0=args.lr0,
        weight_decay=args.weight_decay,
        project=args.project,
        name=args.name,
        plots=True,
        save=True,
        val=True,
        cache=False,
        verbose=True
    )
    
    return results

def main():
    args = parse_args()
    
    # Check if run is already managed by MLflow (e.g., from hpo_pipeline)
    if args.mlflow_run_id:
        train_model(args)
    else:
        # Start a clean MLflow run manually
        mlflow.set_experiment("weld_joint_radiography_retrain")
        with mlflow.start_run(run_name=args.name) as run:
            # Log all training hyperparameters
            mlflow.log_params({
                "model_type": "RT-DETR" if "rtdetr" in args.modelweights.lower() else "YOLO",
                "base_weights": args.modelweights,
                "epochs": args.epochs,
                "batch_size": args.batch,
                "box_loss_gain": args.box,
                "cls_loss_gain": args.cls,
                "dfl_loss_gain": args.dfl,
                "focal_loss_gamma": args.fl_gamma,
                "initial_learning_rate": args.lr0,
                "weight_decay": args.weight_decay,
                "patience": args.patience
            })
            
            train_model(args)

if __name__ == "__main__":
    main()
