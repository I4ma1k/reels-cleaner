# ✂️ ReelCleaner — Descargador de Instagram Reels sin Final de Marca de Agua

Una herramienta web moderna, rápida y responsiva diseñada tanto para **celulares (Android / iPhone)** como para **computadoras (PC / Mac)**.

Permite descargar Reels de Instagram mediante enlace o subir videos ya guardados, eliminando **automáticamente los últimos 3 segundos** donde aparece la pantalla final con el logotipo y sonido característico de Instagram.

---

## 🚀 Despliegue en la Nube 24/7 (1 Clic y Gratis)

Para que funcione **siempre en internet sin depender de que tu PC esté encendida**, haz clic en cualquiera de estos botones para desplegarlo gratis:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/I4ma1k/reels-cleaner)
&nbsp;
[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=https://github.com/I4ma1k/reels-cleaner&name=reels-cleaner&ports=5050;http;/&env[PORT]=5050)

---

## 🚀 Características Principales

- **📱 100% Optimizado para Móviles y PC**:
  - Interfaz web fluida, oscura y táctil inspirada en la estética moderna de Instagram.
  - Botón de **Pegar directo** desde el portapapeles del celular.
  - **Compartir nativo**: En celulares permite compartir directamente a WhatsApp, Telegram, o Guardar en la Galería con el menú nativo.
  - **Código QR instantáneo**: Al abrirlo en tu PC, muestra un código QR para escanearlo con la cámara del celular y abrir la app en el teléfono sin escribir direcciones IP.

- **✂️ Eliminación Inteligente del Outro**:
  - Quita de forma predeterminada los **últimos 3.0 segundos** (duración exacta del outro de Instagram).
  - Selector de ajustes rápidos: `2.5s`, `3.0s (Normal)`, `3.5s`, `4.0s` o tiempo personalizado en segundos.
  - Interruptor para activar/desactivar el recorte si solo quieres el video original.

- **📥 2 Modos de Uso**:
  1. **Modo Enlace (URL)**: Pega el enlace de cualquier Reel público de Instagram (`https://www.instagram.com/reel/...`).
  2. **Modo Subir Archivo**: Si ya descargaste el video desde la app de Instagram con la marca de agua al final, arrástralo o selecciónalo desde tu galería para limpiarlo en 1 segundo.

- **⚡ Motor de Descarga y Procesamiento**:
  - Doble motor de extracción (`parth-dl` y `yt-dlp`) para máxima fiabilidad.
  - Procesamiento ultra rápido con **FFmpeg** (`H.264`, `AAC`, banderas `+faststart`) garantizando compatibilidad total en reproductores de iOS, Android y navegadores.
  - Reproductor con vista previa en vivo antes de descargar.
  - Limpieza automática de archivos temporales antiguos para no consumir espacio en disco.

---

## 🛠️ Instalación y Uso Rápido

### Requisitos:
- Linux, macOS o Windows (WSL)
- Python 3.10+
- FFmpeg instalado en el sistema (`sudo pacman -S ffmpeg` o `sudo apt install ffmpeg`)

### 1. Iniciar la herramienta:
Simplemente ejecuta el script de inicio en la terminal:

```bash
cd ~/Proyectos/reels-cleaner
./start.sh
```

El script configurará automáticamente el entorno virtual (`venv`), descargará las librerías necesarias y levantará el servidor web.

### 2. Abrir en tus dispositivos:
- **En tu Computadora**: Visita `http://localhost:5050`
- **En tu Celular**: Escanea el código QR que aparecerá directamente en la terminal (o en el botón QR de la web), o abre la dirección IP local indicada (ej: `http://192.168.1.19:5050`) conectado a la misma red Wi-Fi.

---

## 📂 Estructura del Proyecto

```text
reels-cleaner/
├── app/
│   ├── main.py            # API FastAPI y rutas web
│   ├── downloader.py      # Motor de extracción multi-estrategia
│   ├── processor.py       # FFmpeg trim / corte exacto y metadatos
│   ├── utils.py           # Detección de IP LAN, QR y limpieza temporal
│   ├── static/
│   │   ├── css/style.css  # Estilos modernos móviles/desktop
│   │   └── js/app.js      # Lógica de interfaz de usuario
│   └── templates/
│       └── index.html     # Plantilla HTML5
├── downloads/             # Directorio de videos limpios temporales
├── requirements.txt       # Dependencias Python
├── run.py                 # Lanzador con código QR en terminal
├── start.sh               # Script ejecutable de inicio rápido
└── README.md              # Documentación
```
