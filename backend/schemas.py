from pydantic import BaseModel, Field

class OCRRequest(BaseModel):
    image: str = Field(min_length=1, max_length=16 * 1024 * 1024)

class TextRegion(BaseModel):
    id: str
    bbox: tuple[int, int, int, int]
    jp: str
    vertical: bool

class OCRResponse(BaseModel):
    width: int
    height: int
    coordinate_space: str = "screenshot_pixels"
    regions: list[TextRegion]
    timing_ms: dict[str, float]
    warnings: list[str]
