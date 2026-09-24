"""Install pinned upstream source and published ONNX weights, not manga data."""
import hashlib
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "440b978563c71b758e31aaa315d100faba1efa2f"
URL = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.2.1/comictextdetector.pt.onnx"

def main():
    source = ROOT / "vendor" / "comic-text-detector"
    source.parent.mkdir(exist_ok=True)
    if not source.exists():
        subprocess.run(["git", "clone", "https://github.com/dmMaze/comic-text-detector.git", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "checkout", "--detach", REVISION], check=True)
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise SystemExit("Existing detector has a different revision; move it aside before setup.")
    target = ROOT / "models" / "comictextdetector.pt.onnx"
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        temporary = target.with_suffix(".download")
        try:
            print("Downloading detector weights…")
            with urllib.request.urlopen(URL, timeout=120) as response, temporary.open("wb") as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            if temporary.stat().st_size < 1_000_000:
                raise RuntimeError("Unexpectedly small model download.")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print(f"Detector ready. Local SHA256: {digest}")
    print("This digest records the download; it is not an upstream checksum verification.")

if __name__ == "__main__":
    main()
