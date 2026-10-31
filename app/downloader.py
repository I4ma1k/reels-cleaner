import os
import re
import uuid
import logging
import requests
import yt_dlp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Pattern to extract Instagram shortcode or validate link
IG_URL_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.|m\.)?instagram\.com\/(?:reel|p|tv|share\/reel)\/([A-Za-z0-9_-]+)',
    re.IGNORECASE
)

def clean_instagram_url(raw_url: str) -> str:
    """Cleans tracking query params (?igsh=... etc.) and standardizes reel URL."""
    raw_url = raw_url.strip()
    match = IG_URL_REGEX.search(raw_url)
    if match:
        code = match.group(1)
        return f"https://www.instagram.com/reel/{code}/"
    return raw_url

def extract_shortcode(url: str) -> Optional[str]:
    match = IG_URL_REGEX.search(url)
    if match:
        return match.group(1)
    return None

def download_stream_to_file(video_url: str, output_path: str, headers: Optional[dict] = None) -> bool:
    """Streams a direct video URL to disk."""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.instagram.com/'
    }
    if headers:
        default_headers.update(headers)

    with requests.get(video_url, headers=default_headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000

def download_reel(url: str, output_dir: str, cookies_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads an Instagram reel using a resilient multi-strategy approach:
    1. parth-dl (Fast direct scraper without login)
    2. yt-dlp (Robust fallback with DASH merge & cookie support)
    """
    os.makedirs(output_dir, exist_ok=True)
    clean_url = clean_instagram_url(url)
    shortcode = extract_shortcode(clean_url) or str(uuid.uuid4())[:8]
    raw_output_path = os.path.join(output_dir, f"raw_{shortcode}_{uuid.uuid4().hex[:6]}.mp4")

    metadata = {
        "shortcode": shortcode,
        "title": f"Reel {shortcode}",
        "author": "Instagram Creator",
        "thumbnail": None,
        "raw_path": None,
        "method": None
    }

    # Strategy 1: parth-dl direct extractor
    try:
        from parth_dl.extractors import MediaExtractor
        extractor = MediaExtractor(verbose=False)
        info = extractor.extract(clean_url)
        if info and 'entries' in info and len(info['entries']) > 0:
            for entry in info['entries']:
                if entry.get('kind') == 'video' and 'formats' in entry and len(entry['formats']) > 0:
                    video_url = entry['formats'][0].get('url')
                    if video_url:
                        logger.info("Found direct video URL via parth-dl. Downloading stream...")
                        download_stream_to_file(video_url, raw_output_path)
                        if os.path.exists(raw_output_path) and os.path.getsize(raw_output_path) > 1000:
                            metadata["raw_path"] = raw_output_path
                            metadata["title"] = info.get("title") or metadata["title"]
                            metadata["author"] = info.get("uploader") or metadata["author"]
                            metadata["thumbnail"] = info.get("thumbnail")
                            metadata["method"] = "parth-dl"
                            return metadata
    except Exception as e:
        logger.warning(f"Strategy 1 (parth-dl) failed: {e}. Falling back to yt-dlp...")

    # Strategy 2: yt-dlp fallback
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': raw_output_path.replace('.mp4', '') + '.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        if cookies_path and os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            # Find the actual downloaded file (might have had .mp4 added by yt-dlp)
            expected_file = raw_output_path
            if not os.path.exists(expected_file):
                alt_file = raw_output_path.replace('.mp4', '') + '.mp4'
                if os.path.exists(alt_file):
                    expected_file = alt_file

            if os.path.exists(expected_file) and os.path.getsize(expected_file) > 1000:
                metadata["raw_path"] = expected_file
                metadata["title"] = info.get("title") or metadata["title"]
                metadata["author"] = info.get("uploader") or metadata["author"]
                metadata["thumbnail"] = info.get("thumbnail")
                metadata["method"] = "yt-dlp"
                return metadata
    except Exception as e:
        logger.error(f"Strategy 2 (yt-dlp) failed: {e}")
        raise RuntimeError(f"No se pudo descargar el Reel de Instagram: {str(e)}")

    if not metadata["raw_path"] or not os.path.exists(metadata["raw_path"]):
        raise RuntimeError("No se pudo obtener el archivo de video de Instagram.")

    return metadata
