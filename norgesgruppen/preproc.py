import json
from pathlib import Path
import shutil
import yaml

def coco_to_yolo(coco_annotations_path, output_dir="yolo_dataset"):
    # Read COCO annotations
    with open(coco_annotations_path) as f:
        coco = json.load(f)

    # Create output directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, "images").mkdir(exist_ok=True)
    Path(output_dir, "labels").mkdir(exist_ok=True)

    # Copy images to output/images
    for img in coco["images"]:
        src = Path("NM_NGD_coco_dataset", "images", img["file_name"])
        dst = Path(output_dir, "images", img["file_name"])
        shutil.copy(src, dst)

    # Create dataset.yaml
    categories = {cat["id"]: cat["name"] for cat in coco["categories"]}
    nc = len(categories)

    dataset_yaml = {
        "path": output_dir,
        "train": "images",
        "val": "images",
        "test": "images",
        "names": categories,
    }

    with open(Path(output_dir, "dataset.yaml"), "w") as f:
        yaml.dump(dataset_yaml, f)

    # Convert annotations to YOLO format
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        img = next(img for img in coco["images"] if img["id"] == img_id)
        img_width, img_height = img["width"], img["height"]

        # Get YOLO format: class_id, x_center, y_center, width, height (normalized)
        x_center = (ann["bbox"][0] + ann["bbox"][2] / 2) / img_width
        y_center = (ann["bbox"][1] + ann["bbox"][3] / 2) / img_height
        width = ann["bbox"][2] / img_width
        height = ann["bbox"][3] / img_height

        # Write to label file
        label_path = Path(output_dir, "labels", img["file_name"].replace(".jpg", ".txt"))
        with open(label_path, "a") as f:
            f.write(f"{ann['category_id']} {x_center} {y_center} {width} {height}\n")

# Usage
coco_to_yolo("norgesgruppen/NM_NGD_coco_dataset/annotations.json")
