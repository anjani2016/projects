# scripts/train_hf_detr.py
import os
import torch
import torchvision
from transformers import AutoImageProcessor, AutoModelForObjectDetection, TrainingArguments, Trainer

def collate_fn(batch, processor):
    pixel_values = [item[0] for item in batch]
    labels = [item[1] for item in batch]
    batch_dict = {}
    batch_dict["pixel_values"] = torch.stack(pixel_values)
    batch_dict["labels"] = labels
    return batch_dict

class CocoDetectionWrapper(torchvision.datasets.CocoDetection):
    def __init__(self, img_folder, ann_file, processor):
        super().__init__(img_folder, ann_file)
        self.processor = processor

    def __getitem__(self, idx):
        img, target = super().__getitem__(idx)
        image_id = self.ids[idx]
        target = {"image_id": image_id, "annotations": target}
        encoding = self.processor(images=img, annotations=target, return_tensors="pt")
        pixel_values = encoding["pixel_values"].squeeze()
        target = encoding["labels"][0]
        return pixel_values, target

def main():
    model_checkpoint = "PekingU/rtdetr_r50vd"
    data_dir = "/Users/anjanid/projects/manufacturing/ai_weld_rt_train/data/gazpromneft_kaggle"
    
    print(f"Loading processor and model from {model_checkpoint}...")
    processor = AutoImageProcessor.from_pretrained(model_checkpoint)
    
    # Define classes based on our gazpromneft_kaggle dataset
    id2label = {
        0: "porosity", 1: "inclusion", 2: "undercut", 3: "burn_through",
        4: "crack", 5: "overlap", 6: "reference_standard_1", 7: "reference_standard_2",
        8: "reference_standard_3", 9: "hidden_porosity", 10: "crater",
        11: "lack_of_fusion", 12: "incomplete_root_penetration"
    }
    label2id = {v: k for k, v in id2label.items()}
    
    model = AutoModelForObjectDetection.from_pretrained(
        model_checkpoint,
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True
    )
    
    print("Loading COCO datasets...")
    train_dataset = CocoDetectionWrapper(
        os.path.join(data_dir, "train", "images"),
        os.path.join(data_dir, "train.json"),
        processor
    )
    
    val_dataset = CocoDetectionWrapper(
        os.path.join(data_dir, "val", "images"),
        os.path.join(data_dir, "val.json"),
        processor
    )
    
    # Use a small random subset to prevent breaking the system on CPU
    print("Subsetting datasets for safe CPU training...")
    train_indices = torch.randperm(len(train_dataset))[:500].tolist()
    val_indices = torch.randperm(len(val_dataset))[:100].tolist()
    
    train_dataset = torch.utils.data.Subset(train_dataset, train_indices)
    val_dataset = torch.utils.data.Subset(val_dataset, val_indices)
    
    training_args = TrainingArguments(
        output_dir="models/hf_weld_rtdetr",
        per_device_train_batch_size=2,
        num_train_epochs=100,
        fp16=False, # Use False on Mac unless MPS supports it well
        use_cpu=True, # RT-DETR has a float64 bug on Apple Silicon MPS
        save_steps=500,
        logging_steps=50,
        learning_rate=1e-5,
        weight_decay=1e-4,
        save_total_limit=2,
        remove_unused_columns=False,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=lambda batch: collate_fn(batch, processor),
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=processor,
    )
    
    import glob
    checkpoints = glob.glob(os.path.join(training_args.output_dir, "checkpoint-*"))
    if checkpoints:
        print("Found existing checkpoints. Resuming training from the last saved step...")
        trainer.train(resume_from_checkpoint=True)
    else:
        print("Starting training from scratch...")
        trainer.train()
    
    print("Training complete! Saving final model...")
    trainer.save_model("models/hf_weld_rtdetr_final")

if __name__ == "__main__":
    main()
