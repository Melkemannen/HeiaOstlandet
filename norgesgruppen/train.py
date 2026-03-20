from ultralytics import YOLO

# Load a COCO-pretrained model
model = YOLO("yolov8n.pt")

# Train on your dataset (adjust paths and parameters as needed)
results = model.train(
    data="yolo_dataset/dataset.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    device="0",  # Use GPU if available
    name="norgesgruppen_yolov8"
)

# Save the best model
model.export(format="onnx", imgsz=640, opset=17)
