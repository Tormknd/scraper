# scraper.py – extraction HTML → JSON via OpenAI + téléchargement d’images.
#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, logging, pathlib
from typing import Dict, List
from urllib.parse import urljoin, urlsplit, urlunsplit, quote

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
from openai import OpenAI

# ───────────────────────────── CONFIG ──────────────────────────────
load_dotenv()
MODEL       = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY     = os.getenv("OPENAI_API_KEY")    # export OPENAI_API_KEY=…
TIMEOUT     = 10                             # sec
RETRIES     = 3
PAUSE_IMG   = 0.4                            # sec entre deux téléchargements d’image
MAX_TOKENS  = 11_000                        # ≈ 12 k, sécurité GPT-4o-mini

IMG_DIR     = pathlib.Path(__file__).with_name("images")
IMG_DIR.mkdir(exist_ok=True)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_items",
        "description": "Extract products with title, optional price and absolute image URL",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "price": {"type": "string"},
                            "img":   {"type": "string"}
                        },
                        "required": ["title", "img"]
                    }
                }
            },
            "required": ["items"]
        }
    }
}

# ─────────────────────────── HTTP session ──────────────────────────
_session = requests.Session()
_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (compatible; scraper-llm/1.1)"}
)
retry_cfg = Retry(
    total=RETRIES,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
_session.mount("http://", HTTPAdapter(max_retries=retry_cfg))
_session.mount("https://", HTTPAdapter(max_retries=retry_cfg))

# ───────────────────────── token counter ───────────────────────────
try:
    import tiktoken
    _enc = tiktoken.encoding_for_model(MODEL)
    _tok = lambda s: len(_enc.encode(s))
except Exception:
    _enc = None
    _tok = lambda s: len(s) // 4

client = OpenAI(api_key=API_KEY)

class ScraperError(RuntimeError):
    ...

# ───────────────────────── helpers ─────────────────────────────────
def _fetch(url: str) -> str:
    try:
        r = _session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as exc:
        raise ScraperError(f"HTTP error on {url}: {exc}") from exc

def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return str(soup)

def _truncate_tokens(text: str) -> str:
    if not _enc:
        return text
    tokens = _enc.encode(text)
    return _enc.decode(tokens[:MAX_TOKENS])

def _llm_extract(html: str) -> Dict:
    prompt = (
        "Voici du HTML d'une page web. "
        "Rends les éléments pertinents (titre, prix, image) au format JSON défini.\n\n"
        + html
    )
    prompt = _truncate_tokens(prompt)

    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        tools=[SCHEMA],
        tool_choice="auto",
        messages=[{"role": "user", "content": prompt}],
    )
    args = resp.choices[0].message.tool_calls[0].function.arguments
    data = json.loads(args)
    if "items" not in data:
        raise ScraperError("LLM did not return 'items'")
    return data

def _sanitize_url(url: str) -> str:
    """Encode les caractères non sûrs (espaces, etc.)."""
    p = urlsplit(url)
    return urlunsplit((
        p.scheme,
        p.netloc,
        quote(p.path),
        quote(p.query, safe="=&"),
        p.fragment,
    ))

def _download_image(url: str) -> str:
    safe = _sanitize_url(url)
    # Détermine nom de base et extension d'origine
    orig_name = pathlib.Path(urlsplit(safe).path).name
    stem = pathlib.Path(orig_name).stem
    suffix = pathlib.Path(orig_name).suffix.lower()

    try:
        resp = _session.get(safe, stream=True, timeout=TIMEOUT)
        resp.raise_for_status()
        # Choix de l'extension basée sur Content-Type
        ctype = resp.headers.get("Content-Type", "").split(";")[0]
        ext_map = {
            "image/webp": ".webp",
            "image/avif": ".avif",
            "image/jpeg": ".jpg",
            "image/png":  ".png",
            "image/gif":  ".gif",
        }
        ext = ext_map.get(ctype, suffix or "")
        filename = stem + ext
        dest = IMG_DIR / filename

        if not dest.exists():
            with dest.open("wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            time.sleep(PAUSE_IMG)

        return f"/images/{dest.name}"

    except Exception as exc:
        logging.warning("Image download failed %s : %s", safe, exc)
        return url  # fallback : URL distante

def _dedup(items: List[Dict]) -> List[Dict]:
    seen, uniq = set(), []
    for it in items:
        key = it.get("img")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    return uniq

# ───────────────────────── public API ──────────────────────────────
def scrape(url: str) -> Dict[str, List[Dict[str, str]]]:
    html    = _fetch(url)
    data    = _llm_extract(_clean_html(html))

    for it in data["items"]:
        it["img"]       = urljoin(url, it["img"])
        it["img_local"] = _download_image(it["img"])

    data["items"] = _dedup(data["items"])
    return data
