import argparse
import json
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory containing shelf images")
    parser.add_argument("--output", required=True, help="Path to output JSON predictions")
    args = parser.parse_args()

    # Load your trained model (GPU auto-detected in sandbox)
    model = YOLO("model.onnx")  # or "model.pt"

    predictions = []
    for img in sorted(Path(args.input).iterdir()):
        if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        image_id = int(img.stem.split("_")[-1])
        results = model(str(img), device="cuda" if torch.cuda.is_available() else "cpu")
        for r in results:
            for box in r.boxes:
                predictions.append({
                    "image_id": image_id,
                    "category_id": int(box.cls.item()),
                    "bbox": [round(coord, 1) for coord in box.xywh[0].tolist()],
                    "score": round(float(box.conf.item()), 3),
                })

    # Write predictions to JSON
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f)

if __name__ == "__main__":
    main()
