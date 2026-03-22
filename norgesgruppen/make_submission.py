"""
Run this after training is complete to create the submission zip.

Usage:
    python make_submission.py

It will:
1. Copy best.pt from training output
2. Create run.py for submission
3. Package into submission.zip
"""
import zipfile
from pathlib import Path
import json

WEIGHTS_PATH = Path("C:/repos/HeiaOstlandet/runs/detect/ng_yolov8m_1280/weights/best.pt")
OUTPUT_ZIP = Path("submission_yolov8m.zip")

RUN_PY = '''import argparse
import json
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO("best.pt")

    predictions = []
    for img in sorted(Path(args.input).iterdir()):
        if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        image_id = int(img.stem.split("_")[-1])

        with torch.no_grad():
            results = model(str(img), device=device, verbose=False,
                            imgsz=1280, conf=0.1, iou=0.5, max_det=500,
                            augment=True)

        for r in results:
            if r.boxes is None:
                continue
            for i in range(len(r.boxes)):
                x1, y1, x2, y2 = r.boxes.xyxy[i].tolist()
                predictions.append({
                    "image_id": image_id,
                    "category_id": int(r.boxes.cls[i].item()),
                    "bbox": [round(x1, 1), round(y1, 1),
                             round(x2 - x1, 1), round(y2 - y1, 1)],
                    "score": round(float(r.boxes.conf[i].item()), 3),
                })

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f)

if __name__ == "__main__":
    main()
'''

if __name__ == "__main__":
    if not WEIGHTS_PATH.exists():
        print(f"ERROR: {WEIGHTS_PATH} not found. Is training complete?")
        exit(1)

    size_mb = WEIGHTS_PATH.stat().st_size / (1024 * 1024)
    print(f"Model size: {size_mb:.1f} MB")

    if size_mb > 400:
        print("WARNING: Model too large for 420MB limit!")

    # Write run.py
    run_py_path = Path("_submission_run.py")
    run_py_path.write_text(RUN_PY)

    # Create zip
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(run_py_path, "run.py")
        zf.write(WEIGHTS_PATH, "best.pt")

    run_py_path.unlink()

    zip_size = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Submission zip: {OUTPUT_ZIP} ({zip_size:.1f} MB)")
    print("Upload this file to the competition!")
