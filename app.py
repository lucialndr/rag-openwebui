from flask import Flask, request, jsonify
import tempfile
import os
import requests
import easyocr
import unicodedata

# -------------------------
# CONFIG
# -------------------------
TIKA_URL = "http://tika-service:9998/tika/text"  # JSON Endpoint verwenden
IMAGE_MIME_TYPES = {
    "image/png", "image/jpeg", "image/jpg",
    "image/webp", "image/gif", "image/tiff", "image/bmp"
}

# Flask-App
app = Flask(__name__)

# EasyOCR-Reader laden
reader = easyocr.Reader(['de', 'en'], gpu=False)


# -------------------------
# HILFSFUNKTIONEN
# -------------------------
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


# -------------------------
# ROUTE
# -------------------------
@app.route("/process", methods=["PUT"])
def process():
    filename = request.headers.get("X-Filename", "uploaded_file")
    content_type = request.headers.get("Content-Type", "application/octet-stream")
    api_key = request.headers.get("Authorization", None)  # falls später nötig

    # Temporäre Datei speichern
    ext = os.path.splitext(filename)[-1].lower()
    temp_path = tempfile.mktemp(suffix=ext)

    try:
        with open(temp_path, "wb") as f:
            f.write(request.data)

        text = ""
        processor = ""

        # -------------------------
        # 1️⃣ OCR-Verarbeitung für Bilder
        # -------------------------
        if content_type in IMAGE_MIME_TYPES:
            text = "\n".join(reader.readtext(temp_path, detail=0, paragraph=True)).strip()
            processor = "easyocr"

        # -------------------------
        # 2️⃣ Tika für alle anderen Formate
        # -------------------------
        else:
            headers = {"Content-Type": content_type}
            with open(temp_path, "rb") as f:
                tika_response = requests.put(
                    TIKA_URL,
                    data=f,
                    headers=headers,
                    timeout=60
                )

            if not tika_response.ok:
                raise Exception(f"Tika request failed ({tika_response.status_code}): {tika_response.reason}")

            # Versuche JSON zu lesen
            try:
                raw_metadata = tika_response.json()
                text = raw_metadata.get("X-TIKA:content", "").strip()
                if not text:
                    text = "<No text content found>"
            except ValueError:
                # Fallback auf reinen Text
                text = tika_response.text.strip()

            processor = "tika"

        # -------------------------
        # Text normalisieren
        # -------------------------
        text = normalize_text(text)

        # -------------------------
        # Antwort zurückgeben
        # -------------------------
        return jsonify({
            "page_content": text,
            "metadata": {
                "title": filename,
                "type": ext.lstrip('.'),
                "content_type": content_type,
                "processor": processor
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

