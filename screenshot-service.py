# screenshot-service.py
from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/screenshot', methods=['GET'])
def screenshot():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    logger.info(f"Получен запрос на скриншот: {url}")

    # Создаём временный файл
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_file.close()

    try:
        # Используем ffmpeg для захвата кадра
        result = subprocess.run([
            'ffmpeg', '-y', '-i', url,
            '-vframes', '1', '-f', 'image2',
            '-t', '00:00:01', '-ss', '00:00:05',
            temp_file.name
        ], timeout=30, capture_output=True)

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"FFmpeg ошибка: {error_msg}")
            return jsonify({
                "error": "Не удалось сделать скриншот",
                "details": error_msg
            }), 500

        # Читаем файл
        with open(temp_file.name, 'rb') as f:
            image_data = f.read()

        # Удаляем временный файл
        os.unlink(temp_file.name)

        # Возвращаем изображение
        return app.response_class(image_data, content_type='image/jpeg')

    except subprocess.TimeoutExpired:
        os.unlink(temp_file.name)
        logger.error("Таймаут FFmpeg")
        return jsonify({"error": "Таймаут при создании скриншота"}), 504

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
