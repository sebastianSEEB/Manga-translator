import sys
from backend.config import ROOT, DETECTOR_SIZE, DETECTOR_CONFIDENCE
from backend.imaging import clamp_box

class ComicDetector:
    def __init__(self):
        source = ROOT / "vendor" / "comic-text-detector"
        weights = ROOT / "models" / "comictextdetector.pt.onnx"
        if not (source / "inference.py").is_file() or not weights.is_file():
            raise RuntimeError("Run python scripts/setup_detector.py first.")
        sys.path.insert(0, str(source))
        from inference import TextDetector
        self.model = TextDetector(str(weights), input_size=DETECTOR_SIZE,
                                  device="cpu", conf_thresh=DETECTOR_CONFIDENCE)

    def detect(self, image):
        import numpy as np
        # Upstream accepts OpenCV BGR pixels and returns original-image coordinates.
        bgr = np.asarray(image)[:, :, ::-1].copy()
        _, _, blocks = self.model(bgr)
        regions = []
        for block in blocks:
            bbox = clamp_box(block.xyxy, image.width, image.height)
            if bbox:
                regions.append({"bbox": bbox, "vertical": bool(block.vertical)})
        return regions
