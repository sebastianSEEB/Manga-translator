from backend.config import FORCE_CPU

class MangaReader:
    def __init__(self):
        # Upstream logs recognized text at DEBUG; suppress its logger before loading.
        from loguru import logger
        logger.disable("manga_ocr")
        from manga_ocr import MangaOcr
        self.model = MangaOcr(force_cpu=FORCE_CPU)

    def read(self, image):
        return self.model(image)
