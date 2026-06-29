#!/usr/bin/env python3
import os
import argparse
import shutil
import random
import yaml
import numpy as np
from collections import Counter
from sklearn.model_selection import StratifiedKFold, train_test_split

CLASS_NAMES = {
    0: "porosity",
    1: "inclusion",
    2: "undercut",
    3: "burn_through",
    4: "crack",
    5: "overlap",
    6: "reference_standard_1",
    7: "reference_standard_2",
    8: "reference_standard_3",
    9: "hidden_porosity",
    10: "crater",
    11: "lack_of_fusion",
    12: "incomplete_root_penetration"
}

def parse_args():
    parser = argparse.ArgumentParser(description="Stratified Train/Val/Test Splitter with 5-Fold Cross-Validation")
    parser.add_argument("--dataset_dir", type=str, default="/Users/anjanid/projects/manufacturing/ai_weld_rt_train/data/gazpromneft_kaggle",
                        help="Path to the original Gazprom dataset")
    parser.add_argument("--output_dir", type=str, default="data/split_folds",
                        help="Directory to output the splits and YAML files")
    parser.add_argument("--subset_size", type=int, default=None,
                        help="If provided, uses a random subset of this size (e.g. 500) for rapid validation")
    parser.add_argument("--folds", type=int, default=5,
                        help="Number of cross-validation folds")
    parser.add_argument("--test_size", type=float, default=0.15,
                        help="Fraction of dataset to reserve for test set")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    return parser.parse_args()

def collect_images_and_labels(dataset_dir):
    """
    Scans the train/val directories of the Gazprom dataset and returns a list of
    dict elements: {'image_path': ..., 'label_path': ..., 'has_labels': bool}
    """
    records = []
    # Loop over original split directories 'train' and 'val'
    for split in ["train", "val"]:
        split_dir = os.path.join(dataset_dir, split)
        img_dir = os.path.join(split_dir, "images")
        lbl_dir = os.path.join(split_dir, "labels")
        
        if not os.path.exists(img_dir):
            continue
            
        for img_name in os.listdir(img_dir):
            if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            
            img_path = os.path.join(img_dir, img_name)
            
            # Match label file name
            basename = os.path.splitext(img_name)[0]
            lbl_path = os.path.join(lbl_dir, basename + ".txt")
            
            has_labels = os.path.exists(lbl_path)
            records.append({
                "image_path": img_path,
                "label_path": lbl_path if has_labels else None,
                "has_labels": has_labels
            })
            
    print(f"Collected {len(records)} image-label pairs from {dataset_dir}")
    return records

def analyze_classes_and_assign_strata(records):
    """
    Ranks classes by rarity and assigns each image to its rarest class stratum.
    Images with no labels are assigned to class -1 (background/noise).
    """
    # 1. Count class frequencies
    class_counts = Counter()
    image_classes = {} # map index -> list of classes in that image
    
    for idx, rec in enumerate(records):
        classes_in_image = []
        if rec["has_labels"]:
            try:
                with open(rec["label_path"], "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            cls_id = int(parts[0])
                            classes_in_image.append(cls_id)
            except Exception as e:
                print(f"Error reading label file {rec['label_path']}: {e}")
                
        class_counts.update(classes_in_image)
        image_classes[idx] = classes_in_image

    # 2. Sort classes by frequency (ascending = rarest first)
    sorted_classes_by_rarity = [cls for cls, count in class_counts.most_common()[::-1]]
    
    print("\nDefect class counts and rarity ranking:")
    for rank, cls in enumerate(sorted_classes_by_rarity):
        name = CLASS_NAMES.get(cls, f"class_{cls}")
        print(f"  Rank {rank+1}: Class {cls} ({name}) -> {class_counts[cls]} instances")

    # 3. Assign each image to its rarest class stratum
    y_strata = []
    for idx in range(len(records)):
        classes = image_classes[idx]
        if not classes:
            y_strata.append(-1) # Background stratum
        else:
            # Find the rarest class in this image
            rarest_cls = min(classes, key=lambda c: sorted_classes_by_rarity.index(c))
            y_strata.append(rarest_cls)
            
    return np.array(y_strata)

def copy_split_files(records, indices, dest_dir):
    """Copies images and label files to destination folders."""
    img_dest = os.path.join(dest_dir, "images")
    lbl_dest = os.path.join(dest_dir, "labels")
    os.makedirs(img_dest, exist_ok=True)
    os.makedirs(lbl_dest, exist_ok=True)
    
    for idx in indices:
        rec = records[idx]
        # Copy image
        shutil.copy(rec["image_path"], img_dest)
        
        # Copy label file if exists, otherwise create empty file for background/noise
        img_name = os.path.basename(rec["image_path"])
        basename = os.path.splitext(img_name)[0]
        lbl_name = basename + ".txt"
        lbl_dest_file = os.path.join(lbl_dest, lbl_name)
        
        if rec["has_labels"]:
            shutil.copy(rec["label_path"], lbl_dest_file)
        else:
            # Create an empty file to indicate background image
            open(lbl_dest_file, "a").close()

def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    records = collect_images_and_labels(args.dataset_dir)
    if not records:
        print("Error: No images found. Check your --dataset_dir path.")
        return
        
    # Apply subset if requested
    if args.subset_size and args.subset_size < len(records):
        print(f"\nSubsetting: randomly selecting {args.subset_size} images out of {len(records)} for rapid validation.")
        records = random.sample(records, args.subset_size)
        
    y_strata = analyze_classes_and_assign_strata(records)
    
    # Clean output directory
    if os.path.exists(args.output_dir):
        print(f"Cleaning existing output directory: {args.output_dir}")
        shutil.rmtree(args.output_dir)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # --- Split 1: Isolate 15% Holdout Test Set ---
    # We use stratify to ensure test set represents all classes
    indices = np.arange(len(records))
    
    # Stratified split requires at least 2 instances per class. 
    # If some rare class has only 1 instance in our subset, sklearn train_test_split might complain.
    # We handle this by falling back to non-stratified split if any class count is 1.
    strata_counts = Counter(y_strata)
    min_class_count = min(strata_counts.values())
    
    stratify_args = y_strata if min_class_count >= 2 else None
    if stratify_args is None:
        print("\nWARNING: Some strata have less than 2 instances. Falling back to non-stratified split.")
        
    train_val_idx, test_idx = train_test_split(
        indices, 
        test_size=args.test_size, 
        random_state=args.seed,
        stratify=stratify_args
    )
    
    # Copy test files
    test_dest = os.path.join(args.output_dir, "test")
    print(f"\nWriting Holdout Test Set ({len(test_idx)} images) to {test_dest}...")
    copy_split_files(records, test_idx, test_dest)
    
    # Save test YAML config
    test_yaml_path = os.path.join(args.output_dir, "data_test.yaml")
    test_config = {
        "path": os.path.abspath(test_dest),
        "train": "images",
        "val": "images",
        "nc": len(CLASS_NAMES),
        "names": CLASS_NAMES
    }
    with open(test_yaml_path, "w") as f:
        yaml.dump(test_config, f, default_flow_style=False)
    print(f"Created: {test_yaml_path}")
    
    # --- Split 2: Stratified 5-Fold Cross Validation on Train/Val Pool ---
    pool_records = [records[i] for i in train_val_idx]
    pool_y = y_strata[train_val_idx]
    pool_indices = np.arange(len(pool_records))
    
    pool_strata_counts = Counter(pool_y)
    pool_min_count = min(pool_strata_counts.values())
    
    # Setup K-Fold
    if pool_min_count >= args.folds:
        skf = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=args.seed)
        folds_generator = skf.split(pool_indices, pool_y)
        print(f"\nRunning Stratified {args.folds}-Fold Cross Validation Splitting...")
    else:
        # Fall back to standard K-Fold
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=args.folds, shuffle=True, random_state=args.seed)
        folds_generator = kf.split(pool_indices)
        print(f"\nWARNING: Rarest class count ({pool_min_count}) is less than number of folds ({args.folds}).")
        print(f"Falling back to standard K-Fold Cross Validation Splitting...")

    for fold, (train_fold_idx, val_fold_idx) in enumerate(folds_generator, start=1):
        fold_dir = os.path.join(args.output_dir, f"fold_{fold}")
        train_dir = os.path.join(fold_dir, "train")
        val_dir = os.path.join(fold_dir, "val")
        
        print(f"\n--- Processing Fold {fold} ---")
        print(f"  Train samples: {len(train_fold_idx)}")
        print(f"  Val samples: {len(val_fold_idx)}")
        
        # Copy files for train fold
        copy_split_files(pool_records, train_fold_idx, train_dir)
        # Copy files for val fold
        copy_split_files(pool_records, val_fold_idx, val_dir)
        
        # Save fold dataset yaml
        fold_yaml_path = os.path.join(args.output_dir, f"data_fold_{fold}.yaml")
        fold_config = {
            "path": os.path.abspath(fold_dir),
            "train": "train/images",
            "val": "val/images",
            "nc": len(CLASS_NAMES),
            "names": CLASS_NAMES
        }
        with open(fold_yaml_path, "w") as f:
            yaml.dump(fold_config, f, default_flow_style=False)
        print(f"Created: {fold_yaml_path}")
        
    print("\nDataset partitioning complete!")

if __name__ == "__main__":
    main()
