import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
# No telemetry is needed for local inference.
os.environ["WANDB_MODE"] = "disabled"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
MAX_BODY = 16 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_REGIONS = int(os.getenv("MAX_REGIONS", "80"))
DETECTOR_SIZE = int(os.getenv("DETECTOR_INPUT_SIZE", "1024"))
DETECTOR_CONFIDENCE = float(os.getenv("DETECTOR_CONFIDENCE", "0.4"))
FORCE_CPU = os.getenv("OCR_FORCE_CPU", "false").lower() == "true"
