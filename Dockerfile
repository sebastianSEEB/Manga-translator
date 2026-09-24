FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/opt/huggingface HF_HUB_DISABLE_TELEMETRY=1 WANDB_MODE=disabled \
    TOKENIZERS_PARALLELISM=false OCR_FORCE_CPU=true
RUN apt-get update && apt-get install -y --no-install-recommends git libgl1 libglib2.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
# CPU wheels avoid installing multi-GB NVIDIA libraries on a CPU host.
RUN pip install --no-cache-dir torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
COPY scripts/setup_detector.py scripts/setup_detector.py
RUN python scripts/setup_detector.py
# Model files are part of the image; user screenshots never enter the build.
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('kha-white/manga-ocr-base')"
COPY backend ./backend
COPY glossaries ./glossaries
COPY scripts/cloud_start.py scripts/cloud_start.py
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
EXPOSE 8000
CMD ["python", "scripts/cloud_start.py"]
