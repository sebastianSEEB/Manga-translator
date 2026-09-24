"""Print OCR JSON to stdout; never create a results file."""
import argparse
import base64
import json
from pathlib import Path
import httpx
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("screenshot", type=Path)
    args = parser.parse_args()
    raw = args.screenshot.read_bytes()
    if len(raw) > 11 * 1024 * 1024:
        parser.error("Screenshot too large; crop or resize it first.")
    try:
        response = httpx.post("http://127.0.0.1:8000/ocr",
            json={"image": base64.b64encode(raw).decode("ascii")},
            headers={"Authorization": "Bearer " + os.getenv("BACKEND_TOKEN", "")}, timeout=180)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise SystemExit(f"HTTP {exc.response.status_code}: {exc.response.text}") from None
    except httpx.RequestError:
        raise SystemExit("Cannot reach OCR backend. Start it and wait for startup to finish.") from None
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
