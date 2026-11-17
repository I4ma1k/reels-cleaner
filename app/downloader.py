import os
import re
import uuid
import random
import logging
import requests
import yt_dlp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.86 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

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
    """Streams a direct video URL to disk with high speed chunks."""
    default_headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': '*/*',
        'Referer': 'https://www.instagram.com/'
    }
    if headers:
        default_headers.update(headers)

    with requests.get(video_url, headers=default_headers, stream=True, timeout=25) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000

def download_reel(url: str, output_dir: str, cookies_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads an Instagram reel using a resilient ultra-fast multi-strategy approach:
    1. parth-dl (Direct CDN link in ~0.5s without login)
    2. yt-dlp (Fast progressive single-file stream fallback with rotating UA)
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

    # Strategy 1: parth-dl direct extractor (fastest, ~0.5s)
    try:
        from parth_dl.extractors import MediaExtractor
        extractor = MediaExtractor(verbose=False)
        info = extractor.extract(clean_url)
        if info and 'entries' in info and len(info['entries']) > 0:
            for entry in info['entries']:
                if entry.get('kind') == 'video' and 'formats' in entry and len(entry['formats']) > 0:
                    video_url = entry['formats'][0].get('url')
                    if video_url:
                        logger.info("Encontrado stream directo vía parth-dl. Descargando...")
                        download_stream_to_file(video_url, raw_output_path)
                        if os.path.exists(raw_output_path) and os.path.getsize(raw_output_path) > 1000:
                            metadata["raw_path"] = raw_output_path
                            metadata["title"] = info.get("title") or metadata["title"]
                            metadata["author"] = info.get("uploader") or metadata["author"]
                            metadata["thumbnail"] = info.get("thumbnail")
                            metadata["method"] = "parth-dl"
                            return metadata
    except Exception as e:
        logger.warning(f"Estrategia 1 (parth-dl) falló: {e}. Probando yt-dlp...")

    # Strategy 2: yt-dlp fallback (single progressive format, rotating user agent)
    try:
        ua = get_random_user_agent()
        ydl_opts = {
            'format': 'b/best[ext=mp4]/best',
            'outtmpl': raw_output_path.replace('.mp4', '') + '.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'retries': 2,
            'extractor_retries': 2,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        
        # Check environment or local file for cookies if provided
        env_cookie_file = os.environ.get("IG_COOKIES_PATH") or cookies_path
        if env_cookie_file and os.path.exists(env_cookie_file):
            ydl_opts['cookiefile'] = env_cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
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
        logger.error(f"Estrategia 2 (yt-dlp) falló: {e}")
        raise RuntimeError(f"No se pudo descargar el Reel de Instagram: {str(e)}")

    if not metadata["raw_path"] or not os.path.exists(metadata["raw_path"]):
        raise RuntimeError("No se pudo obtener el archivo de video de Instagram.")

    return metadata
