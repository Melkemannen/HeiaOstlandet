import torch

_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO

if __name__ == "__main__":
    print("Resuming training from epoch 9...", flush=True)
    model = YOLO("C:/repos/HeiaOstlandet/runs/detect/ng_yolov8m_1280/weights/last.pt")
    results = model.train(resume=True)
    print("Training complete!", flush=True)
