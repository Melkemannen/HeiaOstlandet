from ultralytics import YOLO

# --- Paths ---
DATASET_YAML = "dataset.yaml"
MODEL = "yolov8n.pt"  # Nano YOLOv8 variant (smallest/fastest)
OUTPUT_NAME = "norgesgruppen_yolov8n_augmented"

# --- Training Configuration ---
CONFIG = {
    "data": DATASET_YAML,
    "model": MODEL,
    "epochs": 100,
    "imgsz": [640, 800, 1024],  # Multi-scale training
    "batch": 32,  # Larger batch size for nano model
    "optimizer": "AdamW",
    "lr0": 0.01,
    "lrf": 0.01,  # Cosine learning rate decay
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3.0,
    "cos_lr": True,  # Cosine annealing
    "box": 7.5,  # CIoU loss weight
    "cls": 0.5,  # Classification loss weight
    "dfl": 1.5,  # Distribution Focal Loss weight
    "hsv_h": 0.015,  # Color jitter: hue
    "hsv_s": 0.7,   # Color jitter: saturation
    "hsv_v": 0.4,   # Color jitter: value
    "degrees": 15,  # Random rotate ±15°
    "shear": 0.5,   # Random shear ±10°
    "perspective": 0.0001,  # Perspective transform
    "mosaic": 1.0,  # Mosaic augmentation
    "mixup": 0.5,   # MixUp augmentation
    "copy_paste": 0.5,  # Copy-paste augmentation
    "auto_augment": "rand",  # Auto augmentation
    "autoanchor": True,  # Auto anchor optimization
    "patience": 50,  # Early stopping
    "augment": True,  # Enable all augmentations
    "val": True,  # Validate during training
    "device": "0",  # Use GPU 0
    "name": OUTPUT_NAME,
    "exist_ok": True,  # Overwrite previous runs
}

# --- Train the Model ---
if __name__ == "__main__":
    model = YOLO(CONFIG["model"])
    results = model.train(**CONFIG)

    # --- Export to ONNX ---
    model.export(
        format="onnx",
        imgsz=CONFIG["imgsz"][0],
        opset=17,
        dynamic=False,
        simplify=True,
    )
    print(f"Model exported to: {OUTPUT_NAME}.onnx")

