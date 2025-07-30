FROM python:3.11-slim

WORKDIR /app

# PyTorch (CPU only)
RUN pip install --no-cache-dir --default-timeout=600 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# EasyOCR & Flask
RUN pip install --no-cache-dir --default-timeout=600 \
    easyocr flask requests


COPY app.py .

CMD ["python", "app.py"]

