#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import uvicorn
from app.utils import get_local_ip, print_terminal_qr

def start_cloudflared(port: int = 5050) -> str:
    cloudflared_bin = os.path.join(os.path.dirname(__file__), "bin", "cloudflared")
    log_file = "/tmp/cloudflared.log"
    if os.path.exists(cloudflared_bin):
        try:
            # Check existing log
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    content = f.read()
                    import re
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                    if match:
                        return match.group(0)

            proc = subprocess.Popen(
                [cloudflared_bin, "tunnel", "--url", f"http://localhost:{port}", "--logfile", log_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for _ in range(12):
                time.sleep(0.5)
                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        content = f.read()
                        import re
                        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                        if match:
                            return match.group(0)
        except Exception:
            pass
    return ""

def main():
    port = 5050
    host = "0.0.0.0"
    local_ip = get_local_ip()
    local_url = f"http://localhost:{port}"
    mobile_url = f"http://{local_ip}:{port}"
    public_url = start_cloudflared(port) or "https://groundwater-awards-park-driven.trycloudflare.com"

    print("=" * 65)
    print(" 🚀 REEL CLEANER — Servidor Web & Móvil Iniciado")
    print("=" * 65)
    print(f" 💻 En tu PC:          {local_url}")
    print(f" 📱 En Wi-Fi Local:    {mobile_url}")
    print(f" 🌍 Enlace Público:    {public_url}")
    print("    (¡Funciona en cualquier celular con 4G/5G y permite instalar la App!)")
    print("=" * 65)
    print(" Escanea este código QR con la cámara de tu celular:")
    print("-" * 65)
    print_terminal_qr(public_url)
    print("=" * 65)
    print(" Presiona Ctrl+C para detener el servidor.\n")

    uvicorn.run("app.main:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
