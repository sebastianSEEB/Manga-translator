from time import perf_counter
from backend.config import MAX_REGIONS
from backend.pipeline.reading_order import reading_order
from backend.schemas import OCRResponse, TextRegion

class OCRService:
    def __init__(self, detector, reader):
        self.detector, self.reader = detector, reader

    def process(self, image):
        start = perf_counter()
        regions = reading_order(self.detector.detect(image))
        detected = perf_counter()
        if len(regions) > MAX_REGIONS:
            raise ValueError("Too many text regions; crop the screenshot and retry.")
        output = []
        for index, region in enumerate(regions):
            x, y, w, h = region["bbox"]
            # Small padding helps preserve edge glyphs. Never rotate vertical text.
            crop = image.crop((max(0, x-3), max(0, y-3),
                               min(image.width, x+w+3), min(image.height, y+h+3)))
            jp = self.reader.read(crop).strip()
            if jp:
                output.append(TextRegion(id=f"b{index:03d}", jp=jp, **region))
        end = perf_counter()
        notes = ["Reading order is heuristic; irregular panels may be misordered."]
        if not output:
            notes.append("No text recognized; try a clearer, larger manga crop.")
        return OCRResponse(width=image.width, height=image.height, regions=output,
            timing_ms={"detection": round((detected-start)*1000, 1),
                       "ocr": round((end-detected)*1000, 1),
                       "total": round((end-start)*1000, 1)}, warnings=notes)
