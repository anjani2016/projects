import torch
from transformers import AutoImageProcessor, AutoModelForObjectDetection
from PIL import Image, ImageDraw
import sys

def run_inference(image_path, model_path="models/hf_weld_rtdetr_final"):
    print(f"Loading model from {model_path}...")
    processor = AutoImageProcessor.from_pretrained(model_path)
    model = AutoModelForObjectDetection.from_pretrained(model_path)
    
    print(f"Loading image from {image_path}...")
    image = Image.open(image_path).convert("RGB")
    
    inputs = processor(images=image, return_tensors="pt")
    
    print("Running inference...")
    with torch.no_grad():
        outputs = model(**inputs)
        
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.5)[0]
    
    draw = ImageDraw.Draw(image)
    detected = False
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]
        class_name = model.config.id2label[label.item()]
        conf = round(score.item(), 3)
        print(f"Detected {class_name} with confidence {conf} at location {box}")
        
        draw.rectangle(box, outline="red", width=3)
        draw.text((box[0], max(0, box[1] - 15)), f"{class_name}: {conf}", fill="red")
        detected = True
        
    if not detected:
        print("No defects detected with confidence > 0.5")
        
    output_path = "inference_result.jpg"
    image.save(output_path)
    print(f"Saved result image to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_inference.py <image_path>")
    else:
        run_inference(sys.argv[1])
