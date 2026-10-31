import os
import uuid
import shutil
import logging
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from .downloader import download_reel, clean_instagram_url
from .processor import clean_and_trim_video, get_video_info
from .utils import get_local_ip, generate_qr_code_base64, cleanup_old_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(title="ReelCleaner", description="Descargador de Instagram Reels sin marca de agua final")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class ProcessUrlRequest(BaseModel):
    url: str
    trim_end: float = 3.0
    auto_trim: bool = True

@app.on_event("startup")
async def startup_event():
    cleanup_old_files(DOWNLOADS_DIR)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    local_ip = get_local_ip()
    port = request.url.port or 5050
    network_url = f"http://{local_ip}:{port}"
    qr_b64 = generate_qr_code_base64(network_url)
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "local_ip": local_ip,
            "port": port,
            "network_url": network_url,
            "qr_b64": qr_b64
        }
    )

@app.get("/api/network-info")
async def network_info(request: Request):
    local_ip = get_local_ip()
    port = request.url.port or 5050
    network_url = f"http://{local_ip}:{port}"
    qr_b64 = generate_qr_code_base64(network_url)
    return {
        "local_ip": local_ip,
        "port": port,
        "network_url": network_url,
        "qr_b64": qr_b64
    }

@app.post("/api/process-url")
async def api_process_url(payload: ProcessUrlRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Debes proporcionar un enlace de Instagram Reel.")

    # Cleanup old temp files periodically
    cleanup_old_files(DOWNLOADS_DIR)

    trim_seconds = payload.trim_end if payload.auto_trim else 0.0

    try:
        # Step 1: Download raw reel
        logger.info(f"Descargando reel de URL: {url}")
        meta = download_reel(url, DOWNLOADS_DIR)
        raw_file = meta["raw_path"]
        shortcode = meta["shortcode"]

        # Step 2: Trim the ending watermark (default 3.0s)
        clean_filename = f"clean_{shortcode}_{uuid.uuid4().hex[:6]}.mp4"
        clean_file_path = os.path.join(DOWNLOADS_DIR, clean_filename)

        logger.info(f"Procesando y recortando final ({trim_seconds}s)...")
        trim_res = clean_and_trim_video(raw_file, clean_file_path, trim_end_seconds=trim_seconds)

        # Remove raw video to save space
        try:
            if os.path.exists(raw_file):
                os.remove(raw_file)
        except Exception:
            pass

        return {
            "status": "success",
            "file_id": clean_filename,
            "download_url": f"/api/download/{clean_filename}",
            "stream_url": f"/api/stream/{clean_filename}",
            "title": meta.get("title") or f"Reel_{shortcode}",
            "author": meta.get("author") or "Instagram",
            "thumbnail": meta.get("thumbnail"),
            "original_duration": trim_res["original_duration"],
            "clean_duration": trim_res["clean_duration"],
            "seconds_removed": trim_res["seconds_removed"],
            "file_size_mb": trim_res["file_size_mb"],
            "method": meta.get("method")
        }
    except Exception as e:
        logger.error(f"Error procesando URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-upload")
async def api_process_upload(
    file: UploadFile = File(...),
    trim_end: float = Form(3.0),
    auto_trim: bool = Form(True)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo no válido")

    cleanup_old_files(DOWNLOADS_DIR)

    upload_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    temp_upload_path = os.path.join(DOWNLOADS_DIR, f"upload_{upload_id}{ext}")

    try:
        with open(temp_upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        trim_seconds = trim_end if auto_trim else 0.0
        clean_filename = f"clean_upload_{upload_id}.mp4"
        clean_file_path = os.path.join(DOWNLOADS_DIR, clean_filename)

        trim_res = clean_and_trim_video(temp_upload_path, clean_file_path, trim_end_seconds=trim_seconds)

        try:
            if os.path.exists(temp_upload_path):
                os.remove(temp_upload_path)
        except Exception:
            pass

        return {
            "status": "success",
            "file_id": clean_filename,
            "download_url": f"/api/download/{clean_filename}",
            "stream_url": f"/api/stream/{clean_filename}",
            "title": file.filename,
            "author": "Video Subido",
            "thumbnail": None,
            "original_duration": trim_res["original_duration"],
            "clean_duration": trim_res["clean_duration"],
            "seconds_removed": trim_res["seconds_removed"],
            "file_size_mb": trim_res["file_size_mb"],
            "method": "upload"
        }
    except Exception as e:
        logger.error(f"Error procesando archivo subido: {e}", exc_info=True)
        if os.path.exists(temp_upload_path):
            try:
                os.remove(temp_upload_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/{file_id}")
async def stream_video(file_id: str):
    # Safety check against path traversal
    safe_filename = os.path.basename(file_id)
    file_path = os.path.join(DOWNLOADS_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video no encontrado o expirado.")
    return FileResponse(file_path, media_type="video/mp4")

@app.get("/api/download/{file_id}")
async def download_video(file_id: str):
    safe_filename = os.path.basename(file_id)
    file_path = os.path.join(DOWNLOADS_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video no encontrado o expirado.")
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=f"Reel_Sin_Final_{safe_filename}"
    )
