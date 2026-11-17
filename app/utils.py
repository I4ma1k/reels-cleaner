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

def cleanup_old_files(directory: str, max_age_seconds: int = 600, max_folder_size_mb: int = 150):
    """
    Guarantees the disk never fills up:
    1. Removes any files older than max_age_seconds (default 10 minutes).
    2. Enforces an LRU quota: if total folder size exceeds max_folder_size_mb (150MB),
       it deletes the oldest files first until the folder is well within limits.
    """
    if not os.path.exists(directory):
        return

    now = time.time()
    file_list = []

    # 1. Clean by age
    for root, _, files in os.walk(directory):
        for file in files:
            if file == ".gitkeep":
                continue
            file_path = os.path.join(root, file)
            try:
                if os.path.isfile(file_path):
                    mtime = os.path.getmtime(file_path)
                    size = os.path.getsize(file_path)
                    if now - mtime > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Limpieza por tiempo: {file_path}")
                    else:
                        file_list.append((file_path, mtime, size))
            except Exception as e:
                logger.warning(f"Error inspeccionando {file_path}: {e}")

    # 2. Clean by quota (LRU: oldest files removed first if > max_folder_size_mb)
    total_size = sum(f[2] for f in file_list)
    max_bytes = max_folder_size_mb * 1024 * 1024

    if total_size > max_bytes:
        # Sort oldest first
        file_list.sort(key=lambda x: x[1])
        for file_path, _, size in file_list:
            if total_size <= max_bytes * 0.7:  # clear down to 70% of quota
                break
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    total_size -= size
                    logger.info(f"Limpieza por cuota de disco (LRU): {file_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {file_path}: {e}")
