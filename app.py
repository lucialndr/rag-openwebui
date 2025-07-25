from flask import Flask, request, jsonify
import tempfile, os, imghdr
from markitdown import MarkItDown
import easyocr

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "bmp", "tiff", "jpg"}

app = Flask(__name__)
converter = MarkItDown()
reader = easyocr.Reader(['en', 'de'], gpu=False)

@app.route("/process", methods=["PUT"])
def process():
    filename = request.headers.get("X-Filename", "uploaded_file")
    content_type = request.headers.get("Content-Type", "application/octet-stream")
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # Optional token validation

    ext = os.path.splitext(filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(request.data)
        temp_path = f.name

    try:
        file_type = imghdr.what(temp_path)
        if file_type in ALLOWED_IMAGE_TYPES:
            # OCR für Bilder
            text = reader.readtext(temp_path, detail=0)
            extracted_text = "\n".join(text)
            processor = "easyocr"
        else:
            # Alles andere an MarkItDown
            result = converter.convert(temp_path)
            extracted_text = result.text_content.strip()
            processor = "markitdown"
    except Exception as e:
        os.unlink(temp_path)
        return jsonify({"error": str(e)}), 500

    os.unlink(temp_path)

    return jsonify({
        "page_content": extracted_text,
        "metadata": {
            "title": filename,
            "type": ext,
            "content_type": content_type,
            "processor": processor
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

