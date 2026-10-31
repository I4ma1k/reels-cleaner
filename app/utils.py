import os
import time
import socket
import io
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_local_ip() -> str:
    """Finds the primary local LAN IP of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # We connect to a public DNS IP (doesn't send actual packets)
        s.connect(('1.1.1.1', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def generate_qr_code_base64(url: str) -> str:
    """Generates a base64 encoded PNG QR code of the given URL."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#000000", back_color="#ffffff")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"
    except Exception as e:
        logger.error(f"Error generando código QR: {e}")
        return ""

def print_terminal_qr(url: str):
    """Prints an ASCII QR code directly into the terminal."""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.print_ascii(invert=True)
    except Exception:
        pass

def cleanup_old_files(directory: str, max_age_seconds: int = 3600):
    """Deletes files older than max_age_seconds from directory."""
    if not os.path.exists(directory):
        return
    now = time.time()
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.isfile(file_path):
                    if now - os.path.getmtime(file_path) > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Limpieza de archivo temporal antiguo: {file_path}")
            except Exception as e:
                logger.warning(f"No se pudo limpiar {file_path}: {e}")
