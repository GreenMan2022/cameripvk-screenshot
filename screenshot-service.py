# screenshot-service.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # ← Добавьте это
import subprocess
import tempfile
import os
import logging

app = Flask(__name__)
CORS(app)  # ✅ Разрешаем все домены (или см. ниже — только свой)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/screenshot', methods=['GET'])
def screenshot():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    logger.info(f"Запрос на скриншот: {url}")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_file.close()

    try:
        # Захват кадра
        result = subprocess.run([
            'ffmpeg', '-y',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-headers', 'Referer: https://glaz.naroda.ru/\r\n',
            '-i', url,
            '-vframes', '1', '-f', 'image2',
            '-t', '00:00:01', '-ss', '00:00:05',
            temp_file.name
        ], timeout=30, capture_output=True)

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"FFmpeg ошибка: {error_msg}")
            return jsonify({"error": "Не удалось захватить кадр", "details": error_msg}), 500

        return send_file(temp_file.name, mimetype='image/jpeg')

    except Exception as e:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        logger.error(f"Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
