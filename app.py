from flask import Flask, request, jsonify
import tempfile
import os
import mimetypes
import requests
import easyocr
import unicodedata
from bs4 import BeautifulSoup

app = Flask(__name__)
reader = easyocr.Reader(['de', 'en'], gpu=False)

TIKA_URL = "http://tika-service:9998/tika"
IMAGE_MIME_TYPES = {
    "image/png", "image/jpeg", "image/jpg",
    "image/webp", "image/gif", "image/tiff", "image/bmp"
}

def normalize_text(text: str) -> str:
    """Bereinigt Unicode-Sonderzeichen, Leerzeilen, Duplikate."""
    text = unicodedata.normalize("NFKC", text)
    lines = text.splitlines()
    clean_lines = []
    seen = set()
    for line in lines:
        line = line.strip()
        if line and line not in seen:
            clean_lines.append(line)
            seen.add(line)
    return "\n".join(clean_lines)

def extract_text_from_html(html: str) -> str:
    """Extrahiert Klartext aus HTML-Body (Tika)"""
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

@app.route("/process", methods=["PUT"])
def process():
    filename = request.headers.get("X-Filename", "uploaded_file")
    content_type = request.headers.get("Content-Type", "application/octet-stream")
    api_key = request.headers.get("Authorization", None)

    ext = os.path.splitext(filename)[-1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(request.data)
        temp_path = f.name

    text = ""
    processor = ""

    try:
        if content_type in IMAGE_MIME_TYPES:
            result = reader.readtext(temp_path, detail=0, paragraph=True)
            text = "\n".join(result).strip()
            processor = "easyocr"
        else:
            with open(temp_path, "rb") as f:
                tika_response = requests.put(
                    TIKA_URL,
                    data=f,
                    headers={"Content-Type": content_type},
                    timeout=60,
                )
            if tika_response.status_code != 200:
                raise Exception(f"Tika error: {tika_response.text}")
            
            raw_output = tika_response.text
            if "<html" in raw_output.lower():
                text = extract_text_from_html(raw_output)
            else:
                text = raw_output
            processor = "tika"

        # Text normalisieren
        text = normalize_text(text)

        return jsonify({
            "page_content": text,
            "metadata": {
                "title": filename,
                "type": ext.lstrip("."),
                "content_type": content_type,
                "processor": processor
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

