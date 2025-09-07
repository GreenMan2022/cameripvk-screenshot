import subprocess
import tempfile
import os
import logging
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
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
        # Сначала получаем истинный URL потока через yt-dlp
        result = subprocess.run([
            'yt-dlp', '--get-url', '--format', 'best', url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            logger.error(f"yt-dlp get-url ошибка: {result.stderr}")
            return jsonify({"error": "Не удалось получить URL потока"}), 500

        direct_url = result.stdout.strip().split('\n')[0]
        logger.info(f"Прямой URL потока: {direct_url}")

        # Теперь делаем скриншот
        result = subprocess.run([
            'ffmpeg', '-y',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-headers', 'Referer: https://glaz.naroda.ru/\r\n',
            '-i', direct_url,
            '-vframes', '1', '-f', 'image2',
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
