"""
upload_server.py
局域网内的简易照片上传服务——同事只要手机连着跟这台电脑同一个WiFi/内网，
用手机浏览器打开一个网址，就能直接把护理记录/透析机照片传过来，
不需要装Phone Link这类"一对一配对"的软件，谁的手机都能用。

照片全程留在本机文件夹里(uploads_incoming/)，不会经过任何云端服务，
跟main.py是同一台电脑、同一份文件，main.py那边可以直接读取导入。
"""

import os
import socket
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 让Pillow能认识iPhone拍照默认存的HEIC/HEIF格式(装了pillow-heif才有效，
# 没装也不影响其他格式的照片正常使用)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

try:
    from flask import Flask, request, render_template_string, send_from_directory
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

INCOMING_DIR = os.path.join("uploads_incoming")
IMPORTED_SUBDIR = "imported"  # 已经被main.py导入过的照片，移到这个子文件夹留底，不再出现在待选列表里

UPLOAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>透析记录照片上传</title>
<style>
  body { font-family: -apple-system, "Segoe UI", sans-serif; max-width: 480px; margin: 0 auto;
         padding: 16px; background: #f2f4f7; color: #222; }
  h2 { color: #1a1a2e; }
  h3 { color: #444; font-size: 15px; margin-top: 24px; }
  .upload-box { background: white; border-radius: 12px; padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
  input[type=file] { display: block; width: 100%; margin: 12px 0; padding: 10px;
                      box-sizing: border-box; }
  button { width: 100%; padding: 14px; background: #2d7dd2; color: white; border: none;
           border-radius: 8px; font-size: 16px; }
  button:active { background: #245fa3; }
  .thumb { display: inline-block; width: 100px; margin: 6px; text-align: center; font-size: 11px;
            vertical-align: top; }
  .thumb img { width: 100px; height: 100px; object-fit: cover; border-radius: 8px;
               border: 1px solid #ddd; }
  .msg { color: #1a7f37; background: #e6f6ea; padding: 10px; border-radius: 8px; margin-bottom: 14px; }
  .err { color: #b42318; background: #fdeceb; padding: 10px; border-radius: 8px; margin-bottom: 14px; }
  .empty { color: #888; font-size: 13px; }
</style>
</head>
<body>
  <h2>📷 透析记录照片上传</h2>
  {% if uploaded %}<div class="msg">✓ 上传成功！可以继续拍下一张，或者关闭网页。</div>{% endif %}
  {% if error_msg %}<div class="err">✗ {{ error_msg }}</div>{% endif %}
  <div class="upload-box">
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="photo" accept="image/*" required>
      <button type="submit">上传 Upload</button>
    </form>
  </div>
  <h3>待处理照片 Pending ({{ files|length }})</h3>
  {% if files %}
    <div>
      {% for f in files %}
        <div class="thumb">
          <img src="/photo/{{ f }}">
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty">还没有照片，上传一张试试</div>
  {% endif %}
</body>
</html>
"""


def _save_as_jpeg(file_storage, timestamp):
    """
    把上传的照片(不管原始格式是HEIC/PNG/WEBP/JPG什么的)统一转换成标准JPG存起来。
    这样后面desktop端预览/OCR用的PIL/cv2/pytesseract都能正常打开，
    不会因为iPhone默认拍照是HEIC格式而在"从手机导入"那一步静默失败。
    成功返回保存的文件路径，失败返回None。
    """
    from PIL import Image

    safe_name = f"{timestamp}.jpg"
    save_path = os.path.join(INCOMING_DIR, safe_name)

    try:
        img = Image.open(file_storage.stream)
        img = img.convert("RGB")  # PNG/HEIC可能带透明通道，JPG不支持，统一转RGB
        img.save(save_path, "JPEG", quality=92)
        return save_path
    except Exception as e:
        logger.warning(f"⚠️  转换上传照片失败: {e}")
        # 兜底: 转换失败就按原始格式直接存一份，至少不会丢失这张照片，
        # 只是后续desktop端可能打不开，需要另外处理
        try:
            ext = os.path.splitext(file_storage.filename or "")[1] or ".dat"
            fallback_name = f"{timestamp}{ext}"
            fallback_path = os.path.join(INCOMING_DIR, fallback_name)
            file_storage.stream.seek(0)
            file_storage.save(fallback_path)
            logger.warning(f"⚠️  已按原始格式保存(未转换): {fallback_name}")
            return fallback_path
        except Exception as e2:
            logger.error(f"❌ 连原始格式都保存失败: {e2}")
            return None


def get_local_ip():
    """获取本机在局域网里的IP地址(不需要真的联网，只是借用socket算出网卡地址)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def create_app():
    os.makedirs(INCOMING_DIR, exist_ok=True)
    app = Flask(__name__)
    app.logger.disabled = True
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # 别让flask的请求日志刷屏

    @app.route("/", methods=["GET", "POST"])
    def upload():
        uploaded = False
        error_msg = None
        if request.method == "POST":
            file = request.files.get("photo")
            if file and file.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_path = _save_as_jpeg(file, timestamp)
                if saved_path:
                    uploaded = True
                    logger.info(f"📥 收到手机上传的照片: {os.path.basename(saved_path)}")
                else:
                    error_msg = "这张照片没能正常保存，格式可能不支持，换一张试试"

        files = [
            f for f in sorted(os.listdir(INCOMING_DIR), reverse=True)
            if os.path.isfile(os.path.join(INCOMING_DIR, f))
        ]
        return render_template_string(
            UPLOAD_PAGE, uploaded=uploaded, files=files, error_msg=error_msg
        )

    @app.route("/photo/<filename>")
    def photo(filename):
        return send_from_directory(INCOMING_DIR, filename)

    return app


def start_server_in_background(port=5001):
    """
    在后台线程里启动上传服务，不阻塞主程序运行。
    返回 (local_ip, port, success)，success=False代表flask没装/启动失败。
    """
    if not FLASK_AVAILABLE:
        logger.warning("⚠️ 缺少flask，无法启动手机上传服务。请运行: pip install flask")
        return None, None, False

    try:
        app = create_app()
        local_ip = get_local_ip()

        def run():
            try:
                app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"上传服务运行时出错: {e}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        return local_ip, port, True
    except Exception as e:
        logger.error(f"上传服务启动失败: {e}")
        return None, None, False


def list_incoming_photos():
    """列出所有待处理的照片路径(供main.py桌面端调用，用于弹窗选择要导入哪一张)，按时间新到旧排列"""
    os.makedirs(INCOMING_DIR, exist_ok=True)
    files = [
        f for f in sorted(os.listdir(INCOMING_DIR), reverse=True)
        if os.path.isfile(os.path.join(INCOMING_DIR, f))
    ]
    return [os.path.join(INCOMING_DIR, f) for f in files]


def archive_incoming_photo(path):
    """
    某张照片被main.py导入使用后，移到 uploads_incoming/imported/ 子文件夹留底，
    不再出现在"待处理"列表里，避免被重复导入。
    """
    processed_dir = os.path.join(INCOMING_DIR, IMPORTED_SUBDIR)
    os.makedirs(processed_dir, exist_ok=True)
    try:
        filename = os.path.basename(path)
        new_path = os.path.join(processed_dir, filename)
        os.replace(path, new_path)
        return new_path
    except Exception as e:
        logger.warning(f"移动已导入照片失败: {e}")
        return path