import os
import json
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_video_info(file_path: str) -> Dict[str, Any]:
    """Inspects video metadata using ffprobe."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,codec_type,width,height,duration,r_frame_rate",
        "-of", "json",
        file_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Error al analizar video con ffprobe: {result.stderr}")
        raise RuntimeError(f"Error al analizar video: {result.stderr}")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    try:
        duration = float(format_info.get("duration", 0.0))
        if duration <= 0 and video_stream and "duration" in video_stream:
            duration = float(video_stream["duration"])
    except (ValueError, TypeError):
        duration = 0.0

    width = video_stream.get("width") if video_stream else None
    height = video_stream.get("height") if video_stream else None
    size_bytes = int(format_info.get("size", os.path.getsize(file_path)))

    return {
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "has_audio": audio_stream is not None,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "format": format_info.get("format_name", "mp4")
    }

def clean_and_trim_video(
    input_path: str,
    output_path: str,
    trim_end_seconds: float = 3.0
) -> Dict[str, Any]:
    """
    Trims the specified number of seconds from the end of the video
    (e.g., the 3-second Instagram watermark/outro).
    Ensures optimal web/mobile compatibility (+faststart, H.264 + AAC).
    """
    info = get_video_info(input_path)
    original_duration = info["duration"]

    if trim_end_seconds > 0 and original_duration > trim_end_seconds + 0.5:
        target_duration = original_duration - trim_end_seconds
        actually_trimmed = trim_end_seconds
    else:
        # If the video is shorter than the trim or trim is 0, don't trim
        target_duration = original_duration
        actually_trimmed = 0.0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-t", f"{target_duration:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart"
    ]

    if info["has_audio"]:
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    else:
        cmd.extend(["-an"])

    cmd.append(output_path)

    logger.info(f"Procesando video con ffmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Fallo al procesar con ffmpeg: {result.stderr}")
        raise RuntimeError(f"Error procesando el video: {result.stderr}")

    new_info = get_video_info(output_path)

    return {
        "original_duration": original_duration,
        "clean_duration": new_info["duration"],
        "seconds_removed": round(actually_trimmed, 2),
        "output_path": output_path,
        "file_size_mb": new_info["size_mb"],
        "width": new_info["width"],
        "height": new_info["height"]
    }
