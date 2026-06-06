import os
import json
import cv2
from pathlib import Path

def get_classes():
    return [
        "porosity",
        "inclusion",
        "undercut",
        "burn_through",
        "crack",
        "overlap",
        "reference_standard_1",
        "reference_standard_2",
        "reference_standard_3",
        "hidden_porosity",
        "crater",
        "lack_of_fusion",
        "incomplete_root_penetration"
    ]

def convert_yolo_to_coco(data_dir, split="train"):
    images_dir = os.path.join(data_dir, split, "images")
    labels_dir = os.path.join(data_dir, split, "labels")
    
    classes = get_classes()
    
    coco_format = {
        "info": {"description": f"Weld RT {split} dataset"},
        "images": [],
        "annotations": [],
        "categories": []
    }
    
    for i, cls in enumerate(classes):
        coco_format["categories"].append({"id": i, "name": cls})
        
    if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
        print(f"Directory {split} not found. Skipping.")
        return
        
    image_id = 0
    annotation_id = 0
    
    for img_name in os.listdir(images_dir):
        if not img_name.endswith((".jpg", ".png", ".jpeg")):
            continue
            
        img_path = os.path.join(images_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        h, w, _ = img.shape
        
        coco_format["images"].append({
            "id": image_id,
            "file_name": img_name,
            "width": w,
            "height": h
        })
        
        label_name = os.path.splitext(img_name)[0] + ".txt"
        label_path = os.path.join(labels_dir, label_name)
        
        if os.path.exists(label_path):
            with open(label_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        x_center = float(parts[1]) * w
                        y_center = float(parts[2]) * h
                        box_w = float(parts[3]) * w
                        box_h = float(parts[4]) * h
                        
                        x_min = x_center - box_w / 2
                        y_min = y_center - box_h / 2
                        
                        coco_format["annotations"].append({
                            "id": annotation_id,
                            "image_id": image_id,
                            "category_id": cls_id,
                            "bbox": [x_min, y_min, box_w, box_h],
                            "area": box_w * box_h,
                            "iscrowd": 0
                        })
                        annotation_id += 1
                        
        image_id += 1
        
    out_file = os.path.join(data_dir, f"{split}.json")
    with open(out_file, "w") as f:
        json.dump(coco_format, f, indent=4)
    print(f"Successfully created {out_file} with {image_id} images and {annotation_id} annotations.")

if __name__ == "__main__":
    dataset_path = "/Users/anjanid/projects/manufacturing/ai_weld_rt_train/data/gazpromneft_kaggle"
    convert_yolo_to_coco(dataset_path, "train")
    convert_yolo_to_coco(dataset_path, "val")
