import base64
import json
import math
import os
import re
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

try:
    import requests
    from bs4 import BeautifulSoup
    from googlesearch import search
except ImportError:
    print("Please install dependencies: pip install requests beautifulsoup4 google")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / 'outputs'
INTERMEDIATE_DIR = BASE_DIR / 'intermediate_research'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PLACEHOLDER_IMAGE = 'https://example.com/placeholder.jpg'
AWARD_KEYWORDS = [
    'Academy Award',
    'Oscar',
    'Golden Globe',
    'Globo de Oro',
    'BAFTA',
    'Grammy',
    'Emmy',
    'Premio de la Academia',
]
STYLE_SECTION_KEYWORDS = [
    'musical style',
    'style and influence',
    'style',
    'influence',
    'influences',
    'compositions',
    'estilo',
    'estilo musical',
    'influencia',
    'influencias',
]
ANECDOTE_SECTION_KEYWORDS = [
    'personal life',
    'legacy',
    'later life',
    'death',
    'trivia',
    'anecdote',
    'vida personal',
    'legado',
    'muerte',
    'curiosidades',
]
STYLE_HINTS = [
    'style',
    'influence',
    'sound',
    'orchestration',
    'melody',
    'theme',
    'estilo',
    'música',
    'musical',
    'bandas sonoras',
    'orquesta',
]
ANECDOTE_HINTS = [
    'born',
    'died',
    'career',
    'personal',
    'known for',
    'worked',
    'collaborated',
    'nacio',
    'murio',
    'nació',
    'murió',
]
EXTERNAL_DOMAINS = {
    'MundoBSO': 'mundobso.com',
    'Film Score Monthly': 'filmscoremonthly.com',
    'SoundtrackCollector': 'soundtrackcollector.com',
    'WhatSong': 'whatsong.org',
    'Movie Music UK': 'moviemusicuk.us',
    'Film Music Site': 'cinemusic.net',
    'SoundtrackInfo': 'soundtrackinfo.com',
    'SoundtrackFest': 'soundtrackfest.com',
    'BandasSonorasDeCine': 'bandassonorasdecine.com',
    'FMDB': 'fmdb.net',
    'Film Music Review': 'fmrev.com',
    'Cinescores': 'cinescores.dudaone.com',
    'AllMusic': 'allmusic.com',
    'Discogs': 'discogs.com',
    'MusicBrainz': 'musicbrainz.org',
    'Metacritic': 'metacritic.com',
    'Soundtrack.net': 'soundtrack.net',
    'OSTNews': 'ostnews.com',
    'VGMdb': 'vgmdb.net',
}
SOURCE_PACK_QUERIES = [
    '{composer} compositor biografia',
    '{composer} composer biography',
    '{composer} entrevista compositor banda sonora -site:wikipedia.org',
    '{composer} interview film composer -site:wikipedia.org',
    '{composer} metodo de trabajo compositor banda sonora -site:wikipedia.org',
    '{composer} "working method" film composer -site:wikipedia.org',
    '{composer} estilo musical orquestacion tecnica composicion -site:wikipedia.org',
    '{composer} film score technique orchestration -site:wikipedia.org',
    '{composer} "leitmotif" film music -site:wikipedia.org',
    '{composer} "oral history" film music -site:wikipedia.org',
    '{composer} anecdotas compositor banda sonora -site:wikipedia.org',
    '{composer} awards nominations film music',
    '{composer} premios y nominaciones banda sonora',
    '{composer} legacy influence film music -site:wikipedia.org',
]


def log(message: str, level: str = 'INFO') -> None:
    numeric = LOG_LEVELS.get(level, 20)
    threshold = LOG_LEVELS.get(LOG_LEVEL, 20)
    if numeric >= threshold:
        print(f"[{level}] {message}", flush=True)


def perplexity_post(payload: Dict, timeout: int) -> Optional[Dict]:
    if not PPLX_API_KEY:
        return None
    urls_to_try = [f"{PPLX_API}/chat/completions"]
    if PPLX_API.endswith('/v2'):
        urls_to_try.append('https://api.perplexity.ai/chat/completions')
    last_error = None
    for url in urls_to_try:
        try:
            resp = requests.post(
                url,
                headers={
                    'Authorization': f"Bearer {PPLX_API_KEY}",
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=timeout,
            )
            log(f"PPLX POST {url} -> {resp.status_code}", "INFO")
            if resp.status_code in {400, 401, 403, 404}:
                if resp.text:
                    snippet = resp.text[:400].replace('\n', ' ')
                    log(f"PPLX error body: {snippet}", "WARNING")
                last_error = resp.status_code
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = getattr(exc, 'response', None)
            continue
    if last_error:
        log(f"PPLX request failed (status {last_error})", "WARNING")
    else:
        log("PPLX request failed", "WARNING")
    return None


def openai_generate_text(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    if not OPENAI_ENABLED or not OPENAI_API_KEY:
        return ''
    if OPENAI_USE_RESPONSES or OPENAI_MODEL.startswith('gpt-5'):
        payload = {
            'model': OPENAI_MODEL,
            'input': [
                {'role': 'system', 'content': [{'type': 'input_text', 'text': system_prompt}]},
                {'role': 'user', 'content': [{'type': 'input_text', 'text': user_prompt}]},
            ],
            'max_output_tokens': max_tokens,
        }
        if OPENAI_REASONING_EFFORT:
            payload['reasoning'] = {'effort': OPENAI_REASONING_EFFORT}
        try:
            resp = requests.post(
                OPENAI_RESPONSES_API,
                headers={
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=DEEP_RESEARCH_TIMEOUT,
            )
            log(f"OpenAI responses -> {resp.status_code}", "INFO")
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            if isinstance(exc, requests.RequestException) and exc.response is not None:
                snippet = exc.response.text[:400].replace('\n', ' ')
                log(f"OpenAI responses error body: {snippet}", "WARNING")
            log(f"OpenAI responses failed: {exc}", "WARNING")
            return _openai_chat_fallback(system_prompt, user_prompt, max_tokens)
        text_parts: List[str] = []
        for output in data.get('output') or []:
            for part in output.get('content') or []:
                if part.get('type') == 'output_text' and part.get('text'):
                    text_parts.append(part['text'])
        return '\n'.join(text_parts).strip()
    return _openai_chat_fallback(system_prompt, user_prompt, max_tokens)


def _openai_chat_fallback(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    payload = {
        'model': OPENAI_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_tokens': max_tokens,
        'temperature': 0.2,
    }
    try:
        resp = requests.post(
            OPENAI_API,
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=DEEP_RESEARCH_TIMEOUT,
        )
        log(f"OpenAI chat -> {resp.status_code}", "INFO")
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        if isinstance(exc, requests.RequestException) and exc.response is not None:
            snippet = exc.response.text[:400].replace('\n', ' ')
            log(f"OpenAI chat error body: {snippet}", "WARNING")
        log(f"OpenAI chat failed: {exc}", "WARNING")
        return ''
    choices = data.get('choices') or []
    if not choices:
        return ''
    return (choices[0].get('message') or {}).get('content') or ''


def gemini_generate_text(prompt: str, max_tokens: int = 1500) -> str:
    if not GEMINI_API_KEY:
        return ''
    payload = {
        'contents': [
            {'role': 'user', 'parts': [{'text': prompt}]},
        ],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': max_tokens,
        },
    }
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={'key': GEMINI_API_KEY},
            json=payload,
            timeout=DEEP_RESEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        log(f"Gemini generation failed: {exc}", "WARNING")
        return ''
    candidates = data.get('candidates') or []
    if not candidates:
        return ''
    parts = (candidates[0].get('content') or {}).get('parts') or []
    return ''.join(part.get('text', '') for part in parts).strip()
HEADERS = {'User-Agent': 'Soundtracker/1.0'}
REQUEST_TIMEOUT = 10
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40}
DEEP_RESEARCH_TIMEOUT = int(os.getenv('DEEP_RESEARCH_TIMEOUT', '60'))
POSTER_LIMIT = int(os.getenv('POSTER_LIMIT', '0'))
POSTER_SEARCH_RESULTS = 2
POSTER_WEB_FALLBACK = os.getenv('POSTER_WEB_FALLBACK', '1') == '1'
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_API = 'https://api.themoviedb.org/3'
TMDB_IMAGE = 'https://image.tmdb.org/t/p/w500'
PPLX_API_KEY = os.getenv('PPLX_API_KEY') or os.getenv('PERPLEXITY_API_KEY')
PPLX_MODEL = os.getenv('PPLX_MODEL', 'sonar')
PPLX_API = os.getenv('PPLX_API', 'https://api.perplexity.ai')
PPLX_SEARCH_MODE = os.getenv('PPLX_SEARCH_MODE', 'web')
PPLX_DEEP_MODE = os.getenv('PPLX_DEEP_MODE', 'web')
if PPLX_DEEP_MODE == 'deep':
    PPLX_DEEP_MODE = 'academic'
if PPLX_DEEP_MODE not in {'web', 'academic', 'sec'}:
    PPLX_DEEP_MODE = 'web'
PPLX_SEARCH_MAX_TOKENS = int(os.getenv('PPLX_SEARCH_MAX_TOKENS', '64'))
OPENAI_ENABLED = os.getenv('OPENAI_ENABLED', '1') == '1'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.1-codex-mini')
OPENAI_API = os.getenv('OPENAI_API', 'https://api.openai.com/v1/chat/completions')
OPENAI_RESPONSES_API = os.getenv('OPENAI_RESPONSES_API', 'https://api.openai.com/v1/responses')
OPENAI_USE_RESPONSES = os.getenv('OPENAI_USE_RESPONSES', '1') == '1'
OPENAI_REASONING_EFFORT = os.getenv('OPENAI_REASONING_EFFORT', 'medium').lower()
if OPENAI_REASONING_EFFORT not in {'low', 'medium', 'high'}:
    OPENAI_REASONING_EFFORT = 'medium'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
SOURCE_PACK_ENABLED = os.getenv('SOURCE_PACK_ENABLED', '1') == '1'
SOURCE_PACK_REUSE = os.getenv('SOURCE_PACK_REUSE', '1') == '1'
SOURCE_PACK_GOOGLE_FALLBACK = os.getenv('SOURCE_PACK_GOOGLE_FALLBACK', '1') == '1'
SOURCE_PACK_MAX_URLS = int(os.getenv('SOURCE_PACK_MAX_URLS', '24'))
SOURCE_PACK_MAX_PARAGRAPHS = int(os.getenv('SOURCE_PACK_MAX_PARAGRAPHS', '8'))
SOURCE_PACK_MAX_CHARS = int(os.getenv('SOURCE_PACK_MAX_CHARS', '32000'))
DEEP_RESEARCH_ENABLED = os.getenv('DEEP_RESEARCH_ENABLED', '1') == '1'
EXTERNAL_SNIPPET_MAX_CHARS = int(os.getenv('EXTERNAL_SNIPPET_MAX_CHARS', '700'))
EXTERNAL_SNIPPET_SOURCES = int(os.getenv('EXTERNAL_SNIPPET_SOURCES', '12'))
MIN_PARAGRAPH_LEN = int(os.getenv('MIN_PARAGRAPH_LEN', '50'))
MAX_BIO_PARAGRAPHS = int(os.getenv('MAX_BIO_PARAGRAPHS', '6'))
EXTERNAL_DOMAIN_RESULTS = int(os.getenv('EXTERNAL_DOMAIN_RESULTS', '3'))
TOP_MIN_VOTE_COUNT = int(os.getenv('TOP_MIN_VOTE_COUNT', '50'))
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_ENABLED = os.getenv('SPOTIFY_ENABLED', '1') == '1' and SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_ENABLED = os.getenv('YOUTUBE_ENABLED', '1') == '1' and YOUTUBE_API_KEY
STREAMING_CANDIDATE_LIMIT = int(os.getenv('STREAMING_CANDIDATE_LIMIT', '30'))
TOP_FORCE_AWARDS = os.getenv('TOP_FORCE_AWARDS', '1') == '1'
STREAMING_CACHE_PATH = OUTPUT_DIR / 'streaming_cache.json'
NOISE_HINTS = [
    'cookie',
    'privacy',
    'subscribe',
    'newsletter',
    'sign up',
    'terms of use',
    'otras secciones',
    'menu',
]
BLOCKED_DOMAINS = {
    'shutterstock.com',
    'letterboxd.com',
    'remix.berklee.edu',
    'movieposters.com',
    'etsy.com',
    'impawards.com',
}
TMDB_CACHE_PATH = OUTPUT_DIR / 'tmdb_cache.json'
TRANSLATE_ENDPOINT = 'https://translate.googleapis.com/translate_a/single'
TRANSLATE_TARGET = 'es'
DOWNLOAD_POSTERS = os.getenv('DOWNLOAD_POSTERS', '1') == '1'
SEARCH_WEB_ENABLED = os.getenv('SEARCH_WEB_ENABLED', '1') == '1'
FILM_LIMIT = int(os.getenv('FILM_LIMIT', '200'))
POSTER_WORKERS = int(os.getenv('POSTER_WORKERS', '8'))
SPANISH_CHARS = set('áéíóúñü¿¡')
SPANISH_HINTS = [' el ', ' la ', ' de ', ' y ', ' que ', ' en ', ' los ', ' las ', ' un ', ' una ', ' del ']
ENGLISH_HINTS = [
    ' the ',
    ' and ',
    ' was ',
    ' were ',
    ' born ',
    ' composer ',
    ' died ',
    ' in ',
    ' he ',
    ' she ',
    ' award ',
    ' best ',
    ' original ',
    ' score ',
]

BAD_TITLES = {
    'main page', 'contents', 'current events', 'random article', 'about wikipedia',
    'contact us', 'help', 'learn to edit', 'community portal', 'recent changes',
    'donate', 'contribute', 'privacy policy', 'terms of use', 'disclaimers',
}


def slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '_', name.strip().lower())
    return slug.strip('_') or 'composer'


def poster_filename(title: str, year: Optional[int] = None) -> str:
    base = slugify(title or 'poster')
    if base == 'composer':
        base = 'poster'
    if year:
        return f"poster_{base}_{year}.jpg"
    return f"poster_{base}.jpg"


def get_composers_from_file(path: Path) -> List[str]:
    composers: List[str] = []
    if not path.exists():
        print(f"Master list not found at {path}")
        return composers
    with path.open('r', encoding='utf-8') as fh:
        for line in fh:
            if not line.startswith('|'):
                continue
            parts = [col.strip() for col in line.split('|') if col.strip()]
            if not parts:
                continue
            name = parts[0]
            if name in {'Name', 'No.'} or re.fullmatch(r'-+', name):
                continue
            if parts[0].isdigit() and len(parts) >= 2:
                name = parts[1]
            composers.append(name)
    return composers


def get_composers_with_indices(path: Path) -> List[Tuple[Optional[int], str]]:
    composers: List[Tuple[Optional[int], str]] = []
    if not path.exists():
        print(f"Master list not found at {path}")
        return composers
    with path.open('r', encoding='utf-8') as fh:
        for line in fh:
            if not line.startswith('|'):
                continue
            parts = [col.strip() for col in line.split('|') if col.strip()]
            if not parts:
                continue
            if parts[0] in {'Name', 'No.'} or re.fullmatch(r'-+', parts[0]):
                continue
            if parts[0].isdigit() and len(parts) >= 2:
                composers.append((int(parts[0]), parts[1]))
            else:
                composers.append((None, parts[0]))
    return composers


def fetch_url_text(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc in BLOCKED_DOMAINS:
        return ''
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        print(f"    - failed to fetch {url}: {exc}")
        return ''


def clean_text(text: str) -> str:
    cleaned = re.sub(r'\s+', ' ', text).strip()
    cleaned = re.sub(r'\s+([,.;:!?])', r'\1', cleaned)
    return cleaned


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit(' ', 1)[0]
    return trimmed.rstrip() + '...'


def load_tmdb_cache() -> Dict[str, Dict]:
    if not TMDB_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(TMDB_CACHE_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def save_tmdb_cache(cache: Dict[str, Dict]) -> None:
    try:
        TMDB_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        pass


def load_streaming_cache() -> Dict[str, Dict]:
    if not STREAMING_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(STREAMING_CACHE_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def save_streaming_cache(cache: Dict[str, Dict]) -> None:
    try:
        STREAMING_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        pass


def download_image(url: str, path: Path) -> Optional[str]:
    if not url:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(
            url,
            headers={
                'User-Agent': HEADERS['User-Agent'],
                'Referer': 'https://en.wikipedia.org',
            },
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
        resp.raise_for_status()
        with path.open('wb') as fh:
            for chunk in resp.iter_content(8192):
                fh.write(chunk)
        return str(path)
    except requests.RequestException as exc:
        print(f"    - image download error {url}: {exc}")
        if path.exists():
            path.unlink()
        return None


def download_posters_bulk(entries: List[Dict], composer_folder: Path) -> None:
    if not DOWNLOAD_POSTERS:
        return
    tasks = {}
    with ThreadPoolExecutor(max_workers=POSTER_WORKERS) as executor:
        for entry in entries:
            poster_url = entry.get('poster_url')
            if not poster_url:
                continue
            poster_file = Path(entry.get('poster_file') or (composer_folder / 'posters' / poster_filename(
                entry.get('original_title') or entry.get('title') or '',
                entry.get('year'),
            )))
            if poster_file.exists():
                entry['poster_local'] = str(poster_file)
                continue
            entry['poster_file'] = str(poster_file)
            tasks[executor.submit(download_image, poster_url, poster_file)] = entry
        for future in as_completed(tasks):
            entry = tasks[future]
            try:
                saved = future.result()
            except Exception:
                saved = None
            if saved:
                entry['poster_local'] = saved


def search_duckduckgo(query: str, num: int = 5) -> List[str]:
    return []


def search_perplexity(query: str, num: int = 5) -> List[str]:
    if not (SEARCH_WEB_ENABLED and PPLX_API_KEY):
        return []
    log(f"PPLX query: {query}", "INFO")
    payload = {
        'model': PPLX_MODEL,
        'messages': [
            {'role': 'system', 'content': 'Devuelve resultados de busqueda con URLs fiables.'},
            {'role': 'user', 'content': query},
        ],
        'max_tokens': PPLX_SEARCH_MAX_TOKENS,
        'temperature': 0.2,
        'search_mode': PPLX_SEARCH_MODE,
    }
    data = perplexity_post(payload, DEEP_RESEARCH_TIMEOUT)
    if not data:
        log(f"PPLX request failed for query: {query}", "WARNING")
        return []
    urls: List[str] = []
    for item in data.get('search_results') or []:
        url = item.get('url')
        if url and url not in urls:
            urls.append(url)
    if not urls:
        for url in data.get('citations') or []:
            if url and url not in urls:
                urls.append(url)
    if not urls:
        content = ''
        choices = data.get('choices') or []
        if choices:
            content = (choices[0].get('message') or {}).get('content') or ''
        for match in re.findall(r'https?://\\S+', content):
            cleaned = match.strip(').,;]\"\'')
            if cleaned not in urls:
                urls.append(cleaned)
    return urls[:num]


def _safe_json_loads(content: str) -> Optional[Dict]:
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _dedupe_list(items: List[str]) -> List[str]:
    seen = set()
    deduped = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _normalize_citations_text(text: str, citations: List[str]) -> str:
    if not text or not citations:
        return text
    cleaned = re.sub(r"\s*\[\d+\]", "", text)
    blocks = cleaned.split("\n\n")
    total = len(citations)
    cite_index = 0
    normalized_blocks: List[str] = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            normalized_blocks.append(block)
            continue
        if stripped.startswith("#") or stripped.startswith("|"):
            normalized_blocks.append(block)
            continue
        lines = block.splitlines()
        content_lines = [line for line in lines if line.strip()]
        if content_lines and all(line.strip().startswith("- ") for line in content_lines):
            new_lines = []
            for line in lines:
                if not line.strip():
                    new_lines.append(line)
                    continue
                marker = f"[{(cite_index % total) + 1}]"
                cite_index += 1
                new_lines.append(f"{line} {marker}")
            normalized_blocks.append("\n".join(new_lines))
            continue
        marker = f"[{(cite_index % total) + 1}]"
        cite_index += 1
        normalized_blocks.append(f"{block} {marker}")
    return "\n\n".join(normalized_blocks)


def _openai_outline(composer: str) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    system_prompt = (
        'Eres un investigador musical. Devuelve un esquema corto con los '
        'puntos clave que no deben faltar en un informe académico sobre el compositor, '
        'incluyendo hitos, colaboraciones, técnicas, obras clave y contexto histórico. '
        'Responde en viñetas.'
    )
    content = openai_generate_text(system_prompt, f'Compositor: {composer}', max_tokens=450)
    return content.strip() or None


def _gemini_outline(composer: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    prompt = (
        'Genera un esquema conciso en viñetas con los puntos clave que deben '
        'aparecer en un informe académico sobre este compositor: hitos, colaboraciones, '
        'técnicas, obras clave, contexto histórico, legado y datos humanos.\n'
        f'Compositor: {composer}'
    )
    payload = {
        'contents': [
            {'role': 'user', 'parts': [{'text': prompt}]},
        ],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 512,
        },
    }
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={'key': GEMINI_API_KEY},
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None
    candidates = data.get('candidates') or []
    if not candidates:
        return None
    parts = (candidates[0].get('content') or {}).get('parts') or []
    text = ''.join(part.get('text', '') for part in parts)
    return text.strip() or None


def _build_research_outline(composer: str) -> str:
    outlines = []
    openai_outline = _openai_outline(composer)
    if openai_outline:
        outlines.append(f"GPT 5.1 mini:\n{openai_outline}")
    gemini_outline = _gemini_outline(composer)
    if gemini_outline:
        outlines.append(f"Gemini 2.5 flash:\n{gemini_outline}")
    return "\n\n".join(outlines)


def _build_section_prompt(
    composer: str,
    section: str,
    sources_text: str,
    pack_text: str,
    red_tones_note: str,
) -> Tuple[str, str, int]:
    base = (
        'Usa EXCLUSIVAMENTE las fuentes listadas y no inventes. '
        'Texto en español, tono atractivo, pedagógico y ameno (no excesivamente académico). '
        'Cada párrafo debe terminar con citas [1], [2] usando la lista global de fuentes. '
        'Si hay incertidumbre, indícalo. '
    )
    if section == 'biography':
        system_prompt = (
            'Eres un investigador musical y divulgador. '
            + base +
            'Redacta la biografía en 8-14 párrafos o más si hace falta. '
            'Incluye subtítulos Markdown (###) y al menos 2 tablas cuando sea pertinente '
            '(cronología, colaboraciones, obras clave). '
            + red_tones_note
        )
        max_tokens = 2600
    elif section == 'style':
        system_prompt = (
            'Eres un investigador musical y divulgador. '
            + base +
            'Redacta 4-6 párrafos sobre estilo, técnicas de composición, orquestación e influencias. '
            + red_tones_note
        )
        max_tokens = 1400
    else:
        system_prompt = (
            'Eres un investigador musical y divulgador. '
            + base +
            'Redacta 2-4 párrafos narrativos (NO listas) sobre hábitos, método de trabajo, '
            'excentricidades o rasgos humanos que lo hagan memorable. '
            + red_tones_note
        )
        max_tokens = 1200
    user_prompt = (
        f"Compositor: {composer}\n\n"
        f"Fuentes (citas):\n{sources_text}\n\n"
        f"Material:\n{pack_text}\n"
    )
    return system_prompt, user_prompt, max_tokens


def _openai_source_profile(
    composer: str,
    pack_text: str,
    citations: List[str],
    outline: str,
    debug_dir: Optional[Path] = None,
) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        return None
    sources_text = '\n'.join(f"[{idx}] {url}" for idx, url in enumerate(citations, 1))
    red_tones_note = ''
    if 'stothart' in composer.lower():
        red_tones_note = (
            'Incluye, si está documentado con fuentes fiables, la mención a la teoría de los '
            '"tonos rojos" en su forma de pensar la música; si no hay fuentes claras, indícalo explícitamente. '
        )
    else:
        red_tones_note = 'No menciones la teoría de los "tonos rojos" (es específica de Stothart). '
    if outline:
        pack_text = f"{pack_text}\n\nGuía adicional (contraste GPT/Gemini):\n{outline}\n"
    biography_prompt = _build_section_prompt(composer, 'biography', sources_text, pack_text, red_tones_note)
    style_prompt = _build_section_prompt(composer, 'style', sources_text, pack_text, red_tones_note)
    facts_prompt = _build_section_prompt(composer, 'facts', sources_text, pack_text, red_tones_note)
    bio = openai_generate_text(*biography_prompt)
    style = openai_generate_text(*style_prompt)
    facts = openai_generate_text(*facts_prompt)
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        if bio:
            (debug_dir / 'source_pack_openai_biography.txt').write_text(bio, encoding='utf-8')
        if style:
            (debug_dir / 'source_pack_openai_style.txt').write_text(style, encoding='utf-8')
        if facts:
            (debug_dir / 'source_pack_openai_facts.txt').write_text(facts, encoding='utf-8')
    if not (bio or style or facts):
        return None
    return {
        'biography': {'text': bio},
        'style': {'text': style},
        'facts': {'text': facts},
    }


def _gemini_source_profile(
    composer: str,
    pack_text: str,
    citations: List[str],
    outline: str,
    debug_dir: Optional[Path] = None,
) -> Optional[Dict]:
    if not GEMINI_API_KEY:
        return None
    sources_text = '\n'.join(f"[{idx}] {url}" for idx, url in enumerate(citations, 1))
    red_tones_note = ''
    if 'stothart' in composer.lower():
        red_tones_note = (
            'Incluye, si está documentado con fuentes fiables, la mención a la teoría de los '
            '"tonos rojos" en su forma de pensar la música; si no hay fuentes claras, indícalo explícitamente. '
        )
    else:
        red_tones_note = 'No menciones la teoría de los "tonos rojos" (es específica de Stothart). '
    if outline:
        pack_text = f"{pack_text}\n\nGuía adicional (contraste GPT/Gemini):\n{outline}\n"
    biography_prompt = _build_section_prompt(composer, 'biography', sources_text, pack_text, red_tones_note)
    style_prompt = _build_section_prompt(composer, 'style', sources_text, pack_text, red_tones_note)
    facts_prompt = _build_section_prompt(composer, 'facts', sources_text, pack_text, red_tones_note)
    bio = gemini_generate_text(
        f"{biography_prompt[0]}\n\n{biography_prompt[1]}", max_tokens=biography_prompt[2]
    )
    style = gemini_generate_text(
        f"{style_prompt[0]}\n\n{style_prompt[1]}", max_tokens=style_prompt[2]
    )
    facts = gemini_generate_text(
        f"{facts_prompt[0]}\n\n{facts_prompt[1]}", max_tokens=facts_prompt[2]
    )
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        if bio:
            (debug_dir / 'source_pack_gemini_biography.txt').write_text(bio, encoding='utf-8')
        if style:
            (debug_dir / 'source_pack_gemini_style.txt').write_text(style, encoding='utf-8')
        if facts:
            (debug_dir / 'source_pack_gemini_facts.txt').write_text(facts, encoding='utf-8')
    if not (bio or style or facts):
        return None
    return {
        'biography': {'text': bio},
        'style': {'text': style},
        'facts': {'text': facts},
    }


def _merge_section(primary: str, secondary: str) -> str:
    if not primary:
        return secondary
    if not secondary:
        return primary
    if len(secondary) > len(primary) * 1.2:
        return secondary
    if len(primary) > len(secondary) * 1.2:
        return primary
    return primary


def get_source_pack_profile(composer: str) -> Optional[Dict[str, object]]:
    if not (SOURCE_PACK_ENABLED and PPLX_API_KEY):
        return None
    pack = build_source_pack(composer)
    if not pack:
        log(f"Source pack: no pack available for {composer}", "WARNING")
        return None
    pack_text = pack.get('pack_text') or ''
    citations = pack.get('citations') or []
    if not pack_text or not citations:
        log(f"Source pack: empty pack for {composer}", "WARNING")
        return None
    outline = _build_research_outline(composer)
    log(f"Source pack: running synthesis for {composer}", "INFO")
    debug_dir = INTERMEDIATE_DIR / slugify(composer)
    openai_profile = _openai_source_profile(composer, pack_text, citations, outline, debug_dir)
    gemini_profile = _gemini_source_profile(composer, pack_text, citations, outline, debug_dir)

    def extract_text(profile: Optional[Dict], key: str) -> str:
        if not profile:
            return ''
        section = profile.get(key)
        if isinstance(section, dict):
            return section.get('text') or ''
        if isinstance(section, str):
            return section
        return ''

    biography = _merge_section(
        extract_text(openai_profile, 'biography'),
        extract_text(gemini_profile, 'biography'),
    )
    style = _merge_section(
        extract_text(openai_profile, 'style'),
        extract_text(gemini_profile, 'style'),
    )
    facts = _merge_section(
        extract_text(openai_profile, 'facts'),
        extract_text(gemini_profile, 'facts'),
    )
    min_bio = 900
    min_style = 350
    min_facts = 280
    needs_deep = (
        len(biography or '') < min_bio
        or len(style or '') < min_style
        or len(facts or '') < min_facts
    )
    if needs_deep:
        log(f"Source pack: short synthesis, trying deep research for {composer}", "WARNING")
        deep_profile = get_deep_research_profile(composer)
        if deep_profile:
            deep_citations = deep_profile.get('citations') or []
            biography = _merge_section(biography, deep_profile.get('biography') or '')
            style = _merge_section(style, deep_profile.get('style') or '')
            facts = _merge_section(facts, deep_profile.get('facts') or '')
            citations = _dedupe_list(citations + list(deep_citations))

    citations = _dedupe_wikipedia_citations(citations, composer)
    biography = _normalize_citations_text(biography, citations)
    style = _normalize_citations_text(style, citations)
    facts = _normalize_citations_text(facts, citations)
    if not (biography or style or facts):
        return None
    return {
        'biography': biography.strip(),
        'style': style.strip(),
        'facts': facts.strip(),
        'citations': citations,
    }


def get_deep_research_profile(composer: str) -> Optional[Dict[str, object]]:
    if not (DEEP_RESEARCH_ENABLED and PPLX_API_KEY):
        return None
    outline = _build_research_outline(composer)
    red_tones_note = ''
    if 'stothart' in composer.lower():
        red_tones_note = (
            'Incluye, si está documentado con fuentes fiables, la mención a la teoría de los '
            '"tonos rojos" en su forma de pensar la música; si no hay fuentes claras, indícalo explícitamente. '
        )
    else:
        red_tones_note = (
            'No menciones la teoría de los "tonos rojos" (es específica de Stothart). '
        )
    system_prompt = (
        'Eres un investigador musical y divulgador. Responde SOLO con JSON válido. '
        'Estructura: {"biography": {"text": "..."}, '
        '"style": {"text": "..."}, "facts": {"text": "..."}, '
        '"citations": ["url", ...]}. '
        'Texto en español, tono atractivo, pedagógico y ameno (no excesivamente académico). '
        'biography.text: informe largo y detallado (8-14 párrafos o más si hace falta), '
        'con subtítulos Markdown (###) y al menos 2 tablas cuando sea pertinente '
        '(cronología, colaboraciones, obras clave). '
        'style.text: 4-6 párrafos sobre estilo, técnicas de composición, orquestación e influencias. '
        'facts.text: 2-4 párrafos narrativos (NO listas) sobre hábitos, método de trabajo, '
        'excentricidades o rasgos humanos que lo hagan memorable. '
        + red_tones_note +
        'Cada párrafo debe terminar con citas [1], [2] usando la lista global "citations". '
        'Usa fuentes fiables y no inventes. '
        'Si hay incertidumbre, indícalo.'
    )
    user_prompt = f"Compositor: {composer}"
    if outline:
        user_prompt += f"\n\nGuía adicional (contraste GPT/Gemini):\n{outline}"
    payload = {
        'model': PPLX_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_tokens': 2400,
        'temperature': 0.2,
        'search_mode': PPLX_DEEP_MODE,
    }
    def request_profile(payload_data: Dict, allow_mode_fallback: bool) -> Optional[Dict[str, object]]:
        data = perplexity_post(payload_data, DEEP_RESEARCH_TIMEOUT)
        if not data:
            payload_data = dict(payload_data)
            payload_data.pop('search_mode', None)
            data = perplexity_post(payload_data, DEEP_RESEARCH_TIMEOUT)
        if not data:
            return None
        content = ''
        choices = data.get('choices') or []
        if choices:
            content = (choices[0].get('message') or {}).get('content') or ''
        parsed = _safe_json_loads(content)
        if not parsed or not isinstance(parsed, dict):
            return None
        citations = parsed.get('citations') or data.get('citations') or []
        citations = _dedupe_list([c for c in citations if isinstance(c, str)])
        citations = _dedupe_wikipedia_citations(citations, composer)

        def extract_text(section: object) -> str:
            if isinstance(section, dict):
                return section.get('text') or ''
            if isinstance(section, str):
                return section
            return ''

        biography = extract_text(parsed.get('biography'))
        style = extract_text(parsed.get('style'))
        facts = extract_text(parsed.get('facts'))
        min_bio = 900
        min_style = 350
        min_facts = 280
        if allow_mode_fallback and payload_data.get('search_mode') and (
            len(biography or '') < min_bio or len(style or '') < min_style or len(facts or '') < min_facts
        ):
            payload_alt = dict(payload_data)
            payload_alt.pop('search_mode', None)
            alt = request_profile(payload_alt, False)
            if alt:
                biography = _merge_section(biography, alt.get('biography') or '')
                style = _merge_section(style, alt.get('style') or '')
                facts = _merge_section(facts, alt.get('facts') or '')
                citations = _dedupe_list(citations + list(alt.get('citations') or []))
                citations = _dedupe_wikipedia_citations(citations, composer)

        biography = _normalize_citations_text(biography, citations)
        style = _normalize_citations_text(style, citations)
        facts = _normalize_citations_text(facts, citations)
        return {
            'biography': biography.strip(),
            'style': style.strip(),
            'facts': facts.strip(),
            'citations': citations,
        }

    return request_profile(payload, True)


def search_web(query: str, num: int = 3, pause: float = 1.2) -> List[str]:
    if not SEARCH_WEB_ENABLED:
        return []
    if PPLX_API_KEY:
        urls = search_perplexity(query, num=num)
        if urls:
            return urls
    try:
        log(f"Google search fallback: {query}", "INFO")
        time.sleep(pause)
        results = list(search(query, num=num, stop=num, pause=pause))
        deduped = []
        for url in results:
            if url not in deduped:
                deduped.append(url)
        if deduped:
            return deduped
    except Exception:
        pass
    return []


def extract_paragraphs_from_soup(soup: BeautifulSoup, max_paragraphs: int = 4) -> List[str]:
    paragraphs: List[str] = []
    for tag in soup.find_all(['p', 'li']):
        text = clean_text(tag.get_text(' ', strip=True))
        if len(text) < MIN_PARAGRAPH_LEN:
            continue
        lowered = text.lower()
        if any(hint in lowered for hint in NOISE_HINTS):
            continue
        if is_noise_text(text):
            continue
        paragraphs.append(text)
        if len(paragraphs) >= max_paragraphs:
            break
    return paragraphs


def _wiki_key(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if 'wikipedia.org' not in parsed.netloc:
        return None
    if not parsed.path.startswith('/wiki/'):
        return None
    title = unquote(parsed.path[len('/wiki/'):]).split('#')[0]
    return title or None


def _composer_tokens(composer: str) -> List[str]:
    tokens = [token for token in re.split(r'[^a-zA-Z0-9]+', composer.lower()) if token]
    return [token for token in tokens if token not in {'jr', 'sr', 'ii', 'iii', 'iv'}]


def _wiki_title_matches_composer(title: str, composer: str) -> bool:
    if not title:
        return False
    title_clean = title.replace('_', ' ').lower()
    tokens = _composer_tokens(composer)
    if not tokens:
        return False
    full_name = ' '.join(tokens)
    if full_name and full_name in title_clean:
        return True
    surname = tokens[-1]
    return surname in title_clean


def _dedupe_wikipedia_citations(citations: List[str], composer: str) -> List[str]:
    wiki_urls = [url for url in citations if _wiki_key(url)]
    if len(wiki_urls) <= 1:
        return citations
    matching = [
        url for url in wiki_urls
        if _wiki_title_matches_composer(_wiki_key(url) or '', composer)
    ]
    candidates = matching or wiki_urls
    best_url = ''
    best_text = ''
    for url in candidates:
        text = extract_source_text(url)
        if len(text) > len(best_text):
            best_text = text
            best_url = url
    if not best_url:
        return citations
    return [url for url in citations if not _wiki_key(url) or url == best_url]


def _select_best_wikipedia_url(urls: List[str], composer: str) -> Tuple[List[str], Dict[str, str]]:
    selected: List[str] = []
    preloaded: Dict[str, str] = {}
    non_wiki: List[str] = []
    wiki_urls: List[str] = []
    wiki_candidates: List[str] = []

    for url in urls:
        title = _wiki_key(url)
        if title:
            wiki_urls.append(url)
            if _wiki_title_matches_composer(title, composer):
                wiki_candidates.append(url)
        else:
            non_wiki.append(url)

    if wiki_candidates:
        wiki_urls = wiki_candidates

    best_url = ''
    best_text = ''
    for url in wiki_urls:
        text = extract_source_text(url)
        if len(text) > len(best_text):
            best_text = text
            best_url = url
    if best_url:
        selected.append(best_url)
        if best_text:
            preloaded[best_url] = best_text

    return selected + non_wiki, preloaded


def collect_source_urls(composer: str) -> List[str]:
    if not (SOURCE_PACK_ENABLED and PPLX_API_KEY):
        return []
    log(f"Source pack: collecting URLs for {composer}", "INFO")
    urls: List[str] = []
    extra_queries: List[str] = []
    if 'stothart' in composer.lower():
        extra_queries = [
            f'{composer} "red tones" music theory',
            f'{composer} "tonos rojos" musica',
            f'{composer} "red tones" orchestration',
        ]
    for template in extra_queries + SOURCE_PACK_QUERIES:
        query = template.format(composer=composer)
        log(f"Source pack query: {query}", "INFO")
        candidates: List[str] = []
        candidates.extend(search_perplexity(query, num=6))
        if SOURCE_PACK_GOOGLE_FALLBACK and len(candidates) < 6:
            try:
                candidates.extend(list(search(query, num=4, stop=4, pause=1.0)))
            except Exception:
                pass
        for url in candidates:
            if url in urls:
                continue
            netloc = urlparse(url).netloc.lower()
            if netloc in BLOCKED_DOMAINS:
                continue
            if url.lower().endswith(('.pdf', '.ppt', '.pptx', '.doc', '.docx')):
                continue
            urls.append(url)
            if len(urls) >= SOURCE_PACK_MAX_URLS:
                log(f"Source pack: reached max URLs ({SOURCE_PACK_MAX_URLS}) for {composer}", "INFO")
                return urls
    log(f"Source pack: collected {len(urls)} URLs for {composer}", "INFO")
    return urls


def extract_source_text(url: str) -> str:
    html = fetch_url_text(url)
    if not html:
        return ''
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'svg']):
        tag.decompose()
    main = soup.find('article') or soup.find('main') or soup.body or soup
    paragraphs = extract_paragraphs_from_soup(main, max_paragraphs=SOURCE_PACK_MAX_PARAGRAPHS)
    return '\n'.join(paragraphs)


def build_source_pack(composer: str) -> Optional[Dict[str, object]]:
    if not (SOURCE_PACK_ENABLED and PPLX_API_KEY):
        return None
    slug = slugify(composer)
    base_dir = INTERMEDIATE_DIR / slug
    sources_dir = base_dir / 'sources'
    pack_file = base_dir / 'source_pack.txt'
    meta_file = base_dir / 'source_pack.json'

    if SOURCE_PACK_REUSE and pack_file.exists() and meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding='utf-8'))
            citations = meta.get('citations') or []
            pack_text = pack_file.read_text(encoding='utf-8')
            if citations and pack_text:
                return {'pack_text': pack_text, 'citations': citations}
        except (OSError, json.JSONDecodeError):
            pass

    urls = collect_source_urls(composer)
    if not urls:
        log(f"Source pack: no URLs found for {composer}", "WARNING")
        return None
    urls, preloaded = _select_best_wikipedia_url(urls, composer)
    if preloaded:
        log(f"Source pack: selected {len(preloaded)} Wikipedia source(s) for {composer}", "INFO")
    sources_dir.mkdir(parents=True, exist_ok=True)
    pack_parts: List[str] = []
    citations: List[str] = []
    for idx, url in enumerate(urls, 1):
        log(f"Source pack: fetching {url}", "INFO")
        text = preloaded.get(url) or extract_source_text(url)
        if len(text) < 200:
            log(f"Source pack: skipped short source {url}", "WARNING")
            continue
        citations.append(url)
        source_path = sources_dir / f"source_{idx:02}.txt"
        source_path.write_text(f"URL: {url}\n\n{text}\n", encoding='utf-8')
        pack_parts.append(f"[{len(citations)}] {url}\n{text}\n")
        if sum(len(part) for part in pack_parts) >= SOURCE_PACK_MAX_CHARS:
            log(f"Source pack: reached max chars for {composer}", "INFO")
            break
    if not citations:
        log(f"Source pack: no usable sources for {composer}", "WARNING")
        return None
    pack_text = '\n\n'.join(pack_parts).strip()
    base_dir.mkdir(parents=True, exist_ok=True)
    pack_file.write_text(pack_text, encoding='utf-8')
    meta_file.write_text(json.dumps({'citations': citations}, ensure_ascii=False, indent=2), encoding='utf-8')
    log(f"Source pack: wrote {len(citations)} sources for {composer}", "INFO")
    return {'pack_text': pack_text, 'citations': citations}


def should_translate(text: str) -> bool:
    lowered = f" {text.lower()} "
    spanish_char_count = sum(1 for ch in text if ch in SPANISH_CHARS)
    if spanish_char_count > 3:
        return False
    spanish_hits = sum(1 for marker in SPANISH_HINTS if marker in lowered)
    english_hits = sum(1 for marker in ENGLISH_HINTS if marker in lowered)
    return english_hits > spanish_hits + 1


def translate_text(text: str, target: str) -> str:
    if not text:
        return text
    translated, _ = translate_text_detect(text, target)
    return translated


def translate_text_detect(text: str, target: str) -> tuple[str, str]:
    if not text:
        return text, ''
    try:
        resp = requests.get(
            TRANSLATE_ENDPOINT,
            params={'client': 'gtx', 'sl': 'auto', 'tl': target, 'dt': 't', 'q': text},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return text, ''
    translated = []
    for part in data[0]:
        if part and part[0]:
            translated.append(part[0])
    detected = ''
    if len(data) > 2 and isinstance(data[2], str):
        detected = data[2]
    return clean_text(''.join(translated)) or text, detected


def translate_to_spanish(text: str) -> str:
    if not text:
        return text
    translated, detected = translate_text_detect(text, TRANSLATE_TARGET)
    if detected.startswith('es'):
        return text
    return translated


def ensure_spanish(text: str) -> str:
    if not text:
        return text
    translated, detected = translate_text_detect(text, TRANSLATE_TARGET)
    if detected.startswith('es'):
        return text
    return translated


def translate_to_english(text: str) -> str:
    if not text:
        return text
    return translate_text(text, 'en')


def translate_paragraphs(paragraphs: List[str]) -> List[str]:
    return [translate_to_spanish(paragraph) for paragraph in paragraphs if paragraph]


def is_noise_text(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    if letters:
        upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
        if upper_ratio > 0.6 and len(text.split()) > 6:
            return True
    if text == text.upper() and len(text.split()) > 8:
        return True
    if len(text.split()) > 20 and text.count('.') == 0 and text.count(',') == 0:
        return True
    return False


def search_for_text(query: str, required_keywords: List[str]) -> str:
    urls = search_web(query, num=4)
    for url in urls:
        html = fetch_url_text(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        paragraphs = extract_paragraphs_from_soup(soup, max_paragraphs=4)
        for paragraph in paragraphs:
            lowered = paragraph.lower()
            if any(keyword in lowered for keyword in required_keywords):
                return translate_to_spanish(paragraph)
    return ''


def wikipedia_search_title(query: str, lang: str = 'en') -> Optional[str]:
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'format': 'json',
        'utf8': 1,
        'srlimit': 1,
    }
    try:
        resp = requests.get(f'https://{lang}.wikipedia.org/w/api.php', params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    search_results = data.get('query', {}).get('search', [])
    if not search_results:
        return None
    return search_results[0].get('title')


def wikipedia_page_url(title: str, lang: str = 'en') -> str:
    return f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"


def fetch_wikipedia_html(query: str, lang: str = 'en') -> Optional[str]:
    title = wikipedia_search_title(query, lang=lang)
    if not title:
        return None
    return fetch_url_text(wikipedia_page_url(title, lang=lang))


def fetch_wikipedia_extract(query: str, lang: str = 'en') -> str:
    title = wikipedia_search_title(query, lang=lang)
    if not title:
        return ''
    params = {
        'action': 'query',
        'prop': 'extracts',
        'explaintext': 1,
        'exintro': 1,
        'format': 'json',
        'titles': title,
    }
    try:
        resp = requests.get(f'https://{lang}.wikipedia.org/w/api.php', params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return ''
    pages = data.get('query', {}).get('pages', {})
    for page in pages.values():
        extract = page.get('extract')
        if extract:
            return extract.strip()
    return ''


def tmdb_get(path: str, params: Dict) -> Optional[Dict]:
    if not TMDB_API_KEY:
        return None
    base_params = {'api_key': TMDB_API_KEY}
    base_params.update(params)
    try:
        resp = requests.get(f"{TMDB_API}{path}", params=base_params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


TMDB_MOVIE_CACHE = load_tmdb_cache()
STREAMING_CACHE = load_streaming_cache()
SPOTIFY_TOKEN = {'value': None, 'expires_at': 0}


def tmdb_search_movie_details(title: str, year: Optional[int] = None) -> Optional[Dict[str, Optional[str]]]:
    if not TMDB_API_KEY:
        return None
    cache_key = f"{title}|{year or ''}"
    if cache_key in TMDB_MOVIE_CACHE:
        cached = TMDB_MOVIE_CACHE.get(cache_key)
        if cached:
            return cached
    chosen = None
    for lang in ['es-ES', 'en-US']:
        params = {'query': title, 'language': lang, 'include_adult': False}
        if year:
            params['year'] = year
        data = tmdb_get('/search/movie', params)
        if not data:
            continue
        results = data.get('results', [])
        if not results:
            continue
        chosen = results[0]
        if year:
            for result in results:
                release = result.get('release_date') or ''
                if release.startswith(str(year)):
                    chosen = result
                    break
        if chosen:
            break
    if not chosen:
        alt_title = translate_to_english(title)
        if alt_title and alt_title.lower() != title.lower():
            params = {'query': alt_title, 'language': 'en-US', 'include_adult': False}
            if year:
                params['year'] = year
            data = tmdb_get('/search/movie', params)
            if data:
                results = data.get('results', [])
                if results:
                    chosen = results[0]
                    if year:
                        for result in results:
                            release = result.get('release_date') or ''
                            if release.startswith(str(year)):
                                chosen = result
                                break
    if not chosen:
        TMDB_MOVIE_CACHE[cache_key] = {}
        save_tmdb_cache(TMDB_MOVIE_CACHE)
        return None
    movie_id = chosen.get('id')
    es_data = tmdb_get(f'/movie/{movie_id}', {'language': 'es-ES'}) if movie_id else None
    details = {
        'original_title': (es_data or {}).get('original_title') or chosen.get('original_title') or chosen.get('title'),
        'title_es': (es_data or {}).get('title') or chosen.get('title') or chosen.get('original_title'),
        'poster_path': (es_data or {}).get('poster_path') or chosen.get('poster_path'),
        'popularity': chosen.get('popularity'),
        'vote_count': chosen.get('vote_count'),
        'vote_average': chosen.get('vote_average'),
    }
    TMDB_MOVIE_CACHE[cache_key] = details
    save_tmdb_cache(TMDB_MOVIE_CACHE)
    time.sleep(0.25)
    return details


def tmdb_search_person(name: str) -> tuple[Optional[int], List[str]]:
    data = tmdb_get('/search/person', {'query': name})
    if not data:
        return None, []
    results = data.get('results', [])
    if not results:
        return None, []
    person = results[0]
    known_for_titles: List[str] = []
    for item in person.get('known_for', []) or []:
        title = item.get('title') or item.get('original_title')
        if title and title not in known_for_titles:
            known_for_titles.append(title)
    return person.get('id'), known_for_titles


def tmdb_person_movie_credits(person_id: int, language: str = 'es-ES') -> List[Dict[str, Optional[int]]]:
    data = tmdb_get(f'/person/{person_id}/movie_credits', {'language': language})
    if not data:
        return []
    crew = data.get('crew', [])
    cast = data.get('cast', [])
    credits = []
    for item in crew:
        job = (item.get('job') or '').lower()
        dept = (item.get('department') or '').lower()
        if 'music' in dept or 'composer' in job or 'score' in job:
            credits.append(item)
    if len(credits) < 5:
        credits = crew
    credits = credits + cast
    films: List[Dict[str, Optional[int]]] = []
    for item in credits:
        title = item.get('title') or item.get('original_title')
        original_title = item.get('original_title') or title
        if not title:
            continue
        year = None
        release = item.get('release_date')
        if release:
            year = int(release.split('-')[0])
        films.append({
            'title': title,
            'year': year,
            'original_title': original_title,
            'title_es': title if language.startswith('es') else None,
            'poster_path': item.get('poster_path'),
            'popularity': item.get('popularity'),
            'vote_count': item.get('vote_count'),
            'vote_average': item.get('vote_average'),
        })
        if len(films) >= FILM_LIMIT:
            break
    return films


def tmdb_person_profile(person_id: int) -> Optional[str]:
    data = tmdb_get(f'/person/{person_id}', {})
    if not data:
        return None
    profile = data.get('profile_path')
    if not profile:
        return None
    return f"{TMDB_IMAGE}{profile}"


def tmdb_search_movie(title: str, year: Optional[int] = None) -> Optional[str]:
    details = tmdb_search_movie_details(title, year)
    if not details:
        return None
    poster = details.get('poster_path')
    if not poster:
        return None
    return f"{TMDB_IMAGE}{poster}"


def spotify_get_token() -> Optional[str]:
    if not SPOTIFY_ENABLED:
        return None
    now = time.time()
    if SPOTIFY_TOKEN['value'] and SPOTIFY_TOKEN['expires_at'] > now + 60:
        return SPOTIFY_TOKEN['value']
    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode('utf-8')
    basic = base64.b64encode(credentials).decode('utf-8')
    try:
        resp = requests.post(
            'https://accounts.spotify.com/api/token',
            data={'grant_type': 'client_credentials'},
            headers={'Authorization': f"Basic {basic}"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None
    token = data.get('access_token')
    expires_in = data.get('expires_in') or 0
    if token:
        SPOTIFY_TOKEN['value'] = token
        SPOTIFY_TOKEN['expires_at'] = now + int(expires_in)
    return token


def spotify_search_popularity(composer: str, title: str) -> Optional[float]:
    token = spotify_get_token()
    if not token or not title:
        return None
    queries = [
        f'track:"{title}" soundtrack {composer}',
        f'album:"{title}" soundtrack {composer}',
        f'"{title}" "{composer}" soundtrack',
        f'"{title}" soundtrack',
    ]
    headers = {'Authorization': f"Bearer {token}"}
    best = None
    for query in queries:
        try:
            resp = requests.get(
                'https://api.spotify.com/v1/search',
                headers=headers,
                params={'q': query, 'type': 'track', 'limit': 5},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            continue
        for item in data.get('tracks', {}).get('items', []) or []:
            pop = item.get('popularity')
            if pop is None:
                continue
            if best is None or pop > best:
                best = pop
        if best is not None:
            break
    return float(best) if best is not None else None


def youtube_search_views(composer: str, title: str) -> Optional[int]:
    if not (YOUTUBE_ENABLED and title):
        return None
    query = f"{title} soundtrack {composer}".strip()
    try:
        search_resp = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': 5,
                'order': 'viewCount',
                'videoCategoryId': '10',
                'key': YOUTUBE_API_KEY,
            },
            timeout=REQUEST_TIMEOUT,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except (requests.RequestException, ValueError):
        return None
    video_ids = [
        item.get('id', {}).get('videoId')
        for item in search_data.get('items', []) or []
        if item.get('id', {}).get('videoId')
    ]
    if not video_ids:
        return None
    try:
        videos_resp = requests.get(
            'https://www.googleapis.com/youtube/v3/videos',
            params={
                'part': 'statistics',
                'id': ','.join(video_ids),
                'key': YOUTUBE_API_KEY,
            },
            timeout=REQUEST_TIMEOUT,
        )
        videos_resp.raise_for_status()
        videos_data = videos_resp.json()
    except (requests.RequestException, ValueError):
        return None
    max_views = None
    for item in videos_data.get('items', []) or []:
        count = item.get('statistics', {}).get('viewCount')
        if count is None:
            continue
        try:
            views = int(count)
        except (ValueError, TypeError):
            continue
        if max_views is None or views > max_views:
            max_views = views
    return max_views


def streaming_cache_key(composer: str, title: str, year: Optional[int]) -> str:
    return f"{composer}|{title}|{year or ''}"


def get_streaming_signals(composer: str, entry: Dict[str, Optional[str]]) -> None:
    title = (entry.get('original_title') or entry.get('title') or '').strip()
    if not title:
        return
    cache_key = streaming_cache_key(composer, title, entry.get('year'))
    cached = STREAMING_CACHE.get(cache_key)
    if cached:
        entry.update(cached)
        return
    payload: Dict[str, Optional[float]] = {}
    if SPOTIFY_ENABLED:
        payload['spotify_popularity'] = spotify_search_popularity(composer, title)
    if YOUTUBE_ENABLED:
        payload['youtube_views'] = youtube_search_views(composer, title)
    STREAMING_CACHE[cache_key] = payload
    save_streaming_cache(STREAMING_CACHE)
    entry.update(payload)


def normalize_title(text: str) -> Optional[str]:
    cleaned = re.sub(r'^\d+\.?\s*', '', text.strip())
    cleaned = re.sub(r'\s*\(\d{4}\)\s*', '', cleaned).strip(' .-–:;')
    if not cleaned or len(cleaned) < 2 or len(cleaned) > 90:
        return None
    return cleaned


def normalize_title_key(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', title.lower())


def build_title_keys(entry: Dict[str, Optional[str]]) -> List[str]:
    keys: List[str] = []
    for field in ['original_title', 'title', 'title_es']:
        value = entry.get(field)
        if value:
            key = normalize_title_key(value)
            if key and key not in keys:
                keys.append(key)
    return keys


def is_bad_title(title: str) -> bool:
    lowered = title.strip().lower()
    if lowered in BAD_TITLES:
        return True
    if 'wikipedia' in lowered or 'edit' in lowered:
        return True
    if re.fullmatch(r'q\d+', lowered):
        return True
    return False


def extract_titles_from_lists(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    container = soup.select_one('div.mw-parser-output') or soup.select_one('article') or soup.select_one('main') or soup
    titles: List[str] = []
    for li in container.find_all('li'):
        candidate = normalize_title(li.get_text(' ', strip=True))
        if not candidate or is_bad_title(candidate):
            continue
        if candidate not in titles:
            titles.append(candidate)
        if len(titles) >= 15:
            break
    return titles


def find_top_films_from_text(html: str) -> List[str]:
    titles = extract_titles_from_lists(html)
    if titles:
        return titles[:10]
    return []


def get_top_10_films(composer: str) -> Dict[str, int]:
    queries = [
        f"{composer} mejores bandas sonoras lista",
        f"{composer} mejores bandas sonoras",
        f"{composer} best film scores ranked list",
        f"{composer} best film scores",
        f"{composer} best soundtrack",
    ]
    urls: List[str] = []
    for query in queries:
        urls.extend(search_web(query, num=6))
    counts: Dict[str, int] = {}
    for url in urls:
        html = fetch_url_text(url)
        if not html:
            continue
        for title in find_top_films_from_text(html):
            key = normalize_title_key(title)
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
    return counts


def score_film(
    entry: Dict[str, Optional[str]],
    boost_scores: Dict[str, int],
    award_keys: set,
    current_year: int,
) -> float:
    score = 0.0
    popularity = entry.get('popularity')
    vote_count = entry.get('vote_count')
    vote_average = entry.get('vote_average')
    spotify_popularity = entry.get('spotify_popularity')
    youtube_views = entry.get('youtube_views')
    year = entry.get('year')
    if isinstance(popularity, (int, float)):
        score += float(popularity)
    if isinstance(vote_count, (int, float)):
        score += math.log10(float(vote_count) + 1) * 7
    if isinstance(vote_average, (int, float)):
        score += float(vote_average) * 2
    if isinstance(spotify_popularity, (int, float)):
        score += float(spotify_popularity) * 0.6
    if isinstance(youtube_views, (int, float)):
        score += math.log10(float(youtube_views) + 1) * 5
    for key in build_title_keys(entry):
        if key in boost_scores:
            score += 40 + (boost_scores[key] * 10)
            break
    for key in build_title_keys(entry):
        if key in award_keys:
            score += 20
            break
    if year:
        score += (year % 100) * 0.05
        if year > current_year:
            score -= 100
    if isinstance(vote_count, (int, float)) and vote_count < TOP_MIN_VOTE_COUNT:
        score -= 30
    return score


def score_film_base(
    entry: Dict[str, Optional[str]],
    boost_scores: Dict[str, int],
    award_keys: set,
    current_year: int,
) -> float:
    return score_film(
        {
            **entry,
            'spotify_popularity': None,
            'youtube_views': None,
        },
        boost_scores,
        award_keys,
        current_year,
    )


def maybe_add_streaming_signals(
    composer: str,
    entries: List[Dict[str, Optional[str]]],
    boost_scores: Dict[str, int],
    award_keys: set,
) -> None:
    if not (SPOTIFY_ENABLED or YOUTUBE_ENABLED):
        return
    current_year = datetime.utcnow().year
    ranked = sorted(
        entries,
        key=lambda entry: (score_film_base(entry, boost_scores, award_keys, current_year), entry.get('year') or 0),
        reverse=True,
    )
    for entry in ranked[:STREAMING_CANDIDATE_LIMIT]:
        get_streaming_signals(composer, entry)


def select_top_10_films(
    composer: str,
    filmography: List[Dict[str, Optional[str]]],
    awards: List[Dict],
    boost_scores: Dict[str, int],
) -> List[Dict[str, Optional[str]]]:
    if not filmography:
        return []
    award_keys = set()
    for award in awards:
        film = award.get('film')
        if film:
            award_keys.add(normalize_title_key(film))
    current_year = datetime.utcnow().year
    eligible = []
    for entry in filmography:
        year = entry.get('year')
        if year and year > current_year:
            continue
        vote_count = entry.get('vote_count')
        if isinstance(vote_count, (int, float)) and vote_count < TOP_MIN_VOTE_COUNT:
            continue
        eligible.append(entry)
    if len(eligible) < 10:
        eligible = filmography
    maybe_add_streaming_signals(composer, eligible, boost_scores, award_keys)
    def has_signal(entry: Dict[str, Optional[str]]) -> bool:
        for key in build_title_keys(entry):
            if key in boost_scores or key in award_keys:
                return True
        return False
    signaled = [entry for entry in eligible if has_signal(entry)]
    if len(signaled) >= 6:
        eligible = signaled
    ranked = sorted(
        eligible,
        key=lambda entry: (score_film(entry, boost_scores, award_keys, current_year), entry.get('year') or 0),
        reverse=True,
    )
    unique: List[Dict[str, Optional[str]]] = []
    seen_keys = set()
    if TOP_FORCE_AWARDS and award_keys:
        award_entries = [entry for entry in eligible if any(key in award_keys for key in build_title_keys(entry))]
        award_entries = sorted(
            award_entries,
            key=lambda entry: (score_film(entry, boost_scores, award_keys, current_year), entry.get('year') or 0),
            reverse=True,
        )
        for entry in award_entries:
            keys = build_title_keys(entry)
            if any(key in seen_keys for key in keys):
                continue
            for key in keys:
                seen_keys.add(key)
            unique.append(entry)
            if len(unique) >= 10:
                return unique
    for entry in ranked:
        keys = build_title_keys(entry)
        if any(key in seen_keys for key in keys):
            continue
        for key in keys:
            seen_keys.add(key)
        unique.append(entry)
        if len(unique) >= 10:
            break
    return unique


def extract_section(html: str, keywords: List[str]) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    for heading in soup.find_all(['h2', 'h3']):
        title = heading.get_text(' ', strip=True).lower()
        if any(keyword in title for keyword in keywords):
            content: List[str] = []
            for sibling in heading.next_siblings:
                if getattr(sibling, 'name', None) in ['h2', 'h3']:
                    break
                content.append(str(sibling))
            return ''.join(content)
    return ''


def extract_section_text(html: str, keywords: List[str], max_paragraphs: int = 2) -> str:
    section_html = extract_section(html, keywords)
    if not section_html:
        return ''
    soup = BeautifulSoup(section_html, 'html.parser')
    paragraphs = extract_paragraphs_from_soup(soup, max_paragraphs=max_paragraphs)
    return '\n\n'.join(paragraphs)


def extract_films_from_text(text: str) -> List[Dict[str, Optional[int]]]:
    film_pattern = re.compile(r'([A-Z][A-Za-z0-9\-\'"\.\, ]{3,80})\s*\(?((19|20)\d{2})\)?')
    seen = set()
    films = []
    for match in film_pattern.finditer(text):
        title = match.group(1).strip(' .-–')
        year = match.group(2)
        if not title:
            continue
        if (title.lower(), year) in seen:
            continue
        seen.add((title.lower(), year))
        films.append({'title': title, 'year': int(year) if year else None})
        if len(films) >= 200:
            break
    return films


def dedupe_films(films: List[Dict[str, Optional[int]]]) -> List[Dict[str, Optional[int]]]:
    seen = set()
    unique: List[Dict[str, Optional[int]]] = []
    for film in films:
        title = film.get('title', '').strip()
        if not title or is_bad_title(title):
            continue
        key = (title.lower(), film.get('year'))
        if key in seen:
            continue
        seen.add(key)
        unique.append(film)
    return unique


def dedupe_awards(awards: List[Dict]) -> List[Dict]:
    seen = set()
    unique: List[Dict] = []
    for award in awards:
        key = (
            (award.get('award') or '').strip().lower(),
            award.get('year'),
            (award.get('film') or '').strip().lower(),
            (award.get('status') or '').strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(award)
    for award in unique:
        if award.get('award'):
            award['award'] = translate_to_spanish(award['award'])
    unique.sort(key=lambda item: (item.get('year') or 9999, item.get('award') or '', item.get('film') or ''))
    return unique


def merge_films(base: List[Dict[str, Optional[int]]], extra: List[Dict[str, Optional[int]]]) -> List[Dict[str, Optional[int]]]:
    existing = set()
    for film in base:
        title = film.get('original_title') or film.get('title') or ''
        existing.add(normalize_title_key(title))
    for film in extra:
        title = film.get('original_title') or film.get('title') or ''
        key = normalize_title_key(title)
        if key and key not in existing:
            base.append(film)
            existing.add(key)
    return base


def extract_films_from_html(html: str) -> List[Dict[str, Optional[int]]]:
    soup = BeautifulSoup(html, 'html.parser')
    films: List[Dict[str, Optional[int]]] = []
    for li in soup.find_all('li'):
        text = li.get_text(' ', strip=True)
        entry = extract_films_from_text(text)
        for film in entry:
            if film not in films:
                films.append(film)
            if len(films) >= 200:
                return films
    return dedupe_films(films)


def get_wikidata_qid(composer: str) -> Optional[str]:
    params = {
        'action': 'wbsearchentities',
        'search': composer,
        'language': 'en',
        'format': 'json',
        'limit': 1,
    }
    try:
        resp = requests.get('https://www.wikidata.org/w/api.php', params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    results = data.get('search', [])
    if not results:
        return None
    return results[0].get('id')


def fetch_wikidata_filmography(qid: str) -> List[Dict[str, Optional[int]]]:
    query = f"""
    SELECT ?film ?filmLabel ?labelEs ?labelEn ?originalTitle ?year WHERE {{
      ?film wdt:P86 wd:{qid} .
      OPTIONAL {{ ?film wdt:P1476 ?originalTitle . }}
      OPTIONAL {{ ?film rdfs:label ?labelEs FILTER(LANG(?labelEs) = \"es\") }}
      OPTIONAL {{ ?film rdfs:label ?labelEn FILTER(LANG(?labelEn) = \"en\") }}
      OPTIONAL {{ ?film wdt:P577 ?date . BIND(YEAR(?date) as ?year) }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
    }}
    """
    try:
        resp = requests.get(
            'https://query.wikidata.org/sparql',
            params={'format': 'json', 'query': query},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []
    films: List[Dict[str, Optional[int]]] = []
    for item in data.get('results', {}).get('bindings', []):
        label = item.get('filmLabel', {}).get('value')
        label_es = item.get('labelEs', {}).get('value')
        label_en = item.get('labelEn', {}).get('value')
        original_title = item.get('originalTitle', {}).get('value')
        year = item.get('year', {}).get('value')
        title = original_title or label_en or label or label_es
        if title and not re.fullmatch(r'Q\d+', title.strip()):
            films.append({
                'title': title,
                'year': int(year) if year else None,
                'original_title': original_title or label_en or title,
                'title_es': label_es,
            })
        if len(films) >= 200:
            break
    return films


def fetch_wikidata_awards(qid: str) -> List[Dict]:
    query = f"""
    SELECT ?award ?awardLabel ?year ?workLabel ?status WHERE {{
      {{
        wd:{qid} p:P166 ?awardStatement .
        ?awardStatement ps:P166 ?award .
        BIND(\"Win\" as ?status)
        OPTIONAL {{ ?awardStatement pq:P585 ?date . BIND(YEAR(?date) as ?year) }}
        OPTIONAL {{ ?awardStatement pq:P1686 ?work . }}
      }}
      UNION
      {{
        wd:{qid} p:P1411 ?awardStatement .
        ?awardStatement ps:P1411 ?award .
        BIND(\"Nomination\" as ?status)
        OPTIONAL {{ ?awardStatement pq:P585 ?date . BIND(YEAR(?date) as ?year) }}
        OPTIONAL {{ ?awardStatement pq:P1686 ?work . }}
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
    }}
    """
    try:
        resp = requests.get(
            'https://query.wikidata.org/sparql',
            params={'format': 'json', 'query': query},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []
    awards: List[Dict] = []
    for item in data.get('results', {}).get('bindings', []):
        award_name = item.get('awardLabel', {}).get('value')
        year = item.get('year', {}).get('value')
        work = item.get('workLabel', {}).get('value')
        status = item.get('status', {}).get('value') or 'Win'
        if award_name:
            awards.append({
                'award': award_name,
                'year': int(year) if year else None,
                'film': work,
                'status': status,
            })
    return awards


def fetch_wikidata_country(qid: str) -> Optional[str]:
    query = f"""
    SELECT ?countryLabel WHERE {{
      wd:{qid} wdt:P27 ?country .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    LIMIT 1
    """
    try:
        resp = requests.get(
            'https://query.wikidata.org/sparql',
            params={'format': 'json', 'query': query},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    items = data.get('results', {}).get('bindings', [])
    if not items:
        return None
    return items[0].get('countryLabel', {}).get('value')


def get_complete_filmography(composer: str, composer_folder: Path) -> List[Dict]:
    films: List[Dict] = []
    tmdb_films: List[Dict] = []
    if TMDB_API_KEY:
        person_id, _ = tmdb_search_person(composer)
        if person_id:
            tmdb_films = tmdb_person_movie_credits(person_id, language='es-ES')
    if tmdb_films:
        films = tmdb_films
    if len(films) < 8:
        html = fetch_wikipedia_html(f"{composer} composer")
        if html:
            section_html = extract_section(html, ['filmography', 'selected filmography', 'works'])
            if section_html:
                films = merge_films(films, extract_films_from_html(section_html))
        qid = get_wikidata_qid(composer)
        if qid:
            films = merge_films(films, fetch_wikidata_filmography(qid))
        if len(films) < 8:
            urls = search_web(f"{composer} filmography list", num=5)
            for url in urls:
                html = fetch_url_text(url)
                if not html:
                    continue
                films = merge_films(films, extract_films_from_text(html))
                if films:
                    break
    films = dedupe_films(films)
    films.sort(key=lambda item: (item.get('year') or 9999, item.get('title') or ''))
    for idx, entry in enumerate(films):
        entry['original_title'] = entry.get('original_title') or entry.get('title')
        poster_url = None
        if TMDB_API_KEY and not (entry.get('title_es') and entry.get('poster_path')):
            details = tmdb_search_movie_details(entry['original_title'], entry.get('year'))
            if details:
                entry['original_title'] = details.get('original_title') or entry['original_title']
                entry['title_es'] = details.get('title_es') or entry.get('title_es')
                poster_path = details.get('poster_path') or entry.get('poster_path')
                if poster_path:
                    poster_url = f"{TMDB_IMAGE}{poster_path}"
                if details.get('popularity') is not None:
                    entry['popularity'] = details.get('popularity')
                if details.get('vote_count') is not None:
                    entry['vote_count'] = details.get('vote_count')
                if details.get('vote_average') is not None:
                    entry['vote_average'] = details.get('vote_average')
        poster_path = entry.get('poster_path')
        if poster_path and not poster_url:
            poster_url = f"{TMDB_IMAGE}{poster_path}"
        if not entry.get('title_es') and entry.get('original_title'):
            entry['title_es'] = entry['original_title']
        entry['poster_url'] = poster_url
        entry['poster_file'] = str(composer_folder / 'posters' / poster_filename(
            entry.get('original_title') or entry.get('title') or '',
            entry.get('year'),
        ))
        if POSTER_LIMIT and idx >= POSTER_LIMIT:
            entry['poster_local'] = PLACEHOLDER_IMAGE
            continue
        if not DOWNLOAD_POSTERS:
            entry['poster_local'] = poster_url or PLACEHOLDER_IMAGE
            continue
    eligible = [
        entry for idx, entry in enumerate(films)
        if not POSTER_LIMIT or idx < POSTER_LIMIT
    ]
    if DOWNLOAD_POSTERS:
        download_posters_bulk(eligible, composer_folder)
    missing = [entry for entry in eligible if not entry.get('poster_local')]
    if missing:
        with ThreadPoolExecutor(max_workers=POSTER_WORKERS) as executor:
            tasks = {
                executor.submit(
                    get_film_poster,
                    entry.get('original_title') or entry.get('title', ''),
                    composer_folder,
                    entry.get('poster_url'),
                    entry.get('year'),
                    Path(entry['poster_file']) if entry.get('poster_file') else None,
                ): entry
                for entry in missing
            }
            for future in as_completed(tasks):
                entry = tasks[future]
                try:
                    entry['poster_local'] = future.result()
                except Exception:
                    entry['poster_local'] = PLACEHOLDER_IMAGE
    return films


def get_detailed_awards(composer: str) -> List[Dict]:
    qid = get_wikidata_qid(composer)
    if qid:
        awards = fetch_wikidata_awards(qid)
        if awards:
            return dedupe_awards(awards)
    awards: List[Dict] = []
    html = fetch_wikipedia_html(f"{composer} compositor", lang='es') or fetch_wikipedia_html(composer, lang='es')
    if not html:
        html = fetch_wikipedia_html(f"{composer} composer", lang='en')
    if html:
        awards_html = extract_section(html, ['award', 'awards', 'honor', 'honours', 'recognition', 'premios', 'reconocimientos'])
        if awards_html:
            soup = BeautifulSoup(awards_html, 'html.parser')
            lines = [li.get_text(' ', strip=True) for li in soup.find_all('li')]
            for line in lines:
                if any(keyword.lower() in line.lower() for keyword in AWARD_KEYWORDS):
                    year_match = re.search(r'(19|20)\d{2}', line)
                    year = int(year_match.group()) if year_match else None
                    if year and (year < 1900 or year > 2026):
                        continue
                    film_match = re.search(r"for\s+['\"]?([^'\"\n,]+)", line, re.IGNORECASE)
                    status = 'Win' if 'win' in line.lower() or 'winner' in line.lower() else 'Nomination'
                    award_name = next((kw for kw in AWARD_KEYWORDS if kw.lower() in line.lower()), 'Award')
                    award_name = translate_to_spanish(award_name)
                    awards.append({
                        'award': award_name,
                        'year': year,
                        'film': film_match.group(1).strip() if film_match else None,
                        'status': status,
                    })
    if awards:
        return dedupe_awards(awards)
    urls = search_web(f"{composer} awards and nominations", num=5)
    for url in urls:
        html = fetch_url_text(url)
        if not html:
            continue
        text = BeautifulSoup(html, 'html.parser').get_text('\n')
        for line in text.splitlines():
            if any(keyword.lower() in line.lower() for keyword in AWARD_KEYWORDS):
                year_match = re.search(r'(19|20)\d{2}', line)
                year = int(year_match.group()) if year_match else None
                if year and (year < 1900 or year > 2026):
                    continue
                film_match = re.search(r"for\s+['\"]?([^'\"\n,]+)", line, re.IGNORECASE)
                status = 'Win' if 'win' in line.lower() or 'winner' in line.lower() else 'Nomination'
                award_name = next((kw for kw in AWARD_KEYWORDS if kw.lower() in line.lower()), 'Award')
                award_name = translate_to_spanish(award_name)
                awards.append({
                    'award': award_name,
                    'year': year,
                    'film': film_match.group(1).strip() if film_match else None,
                    'status': status,
                })
        if awards:
            break
    return dedupe_awards(awards)


def get_external_sources(composer: str) -> List[Dict[str, str]]:
    info: List[Dict[str, str]] = []
    for name, domain in EXTERNAL_DOMAINS.items():
        results = search_web(f"site:{domain} {composer}", num=EXTERNAL_DOMAIN_RESULTS)
        if not results:
            results = [f"https://{domain}"]
        for idx, url in enumerate(results, start=1):
            if not url:
                continue
            netloc = urlparse(url).netloc.lower()
            if domain not in netloc:
                url = f"https://{domain}"
            label = name if idx == 1 else f"{name} ({idx})"
            info.append({'name': label, 'url': url, 'snippet': f"site:{domain}"})
    return info


def get_general_snippets(composer: str, limit: int, existing_urls: set) -> List[Dict[str, str]]:
    snippets: List[Dict[str, str]] = []
    queries = [
        f"{composer} compositor entrevista banda sonora -site:wikipedia.org",
        f"{composer} compositor estilo musical -site:wikipedia.org",
        f"{composer} compositor trayectoria musical -site:wikipedia.org",
        f"{composer} compositor cine biografia -site:wikipedia.org",
        f"{composer} film music composer biography -site:wikipedia.org",
        f"{composer} soundtrack composer interview -site:wikipedia.org",
        f"{composer} film score composer profile -site:wikipedia.org",
        f"{composer} biographie compositeur -site:wikipedia.org",
        f"{composer} komponist filmmusik biografie -site:wikipedia.org",
        f"{composer} compositor cinema biografia -site:wikipedia.org",
    ]
    for query in queries:
        urls = search_web(query, num=4)
        for url in urls:
            netloc = urlparse(url).netloc.lower()
            if netloc in BLOCKED_DOMAINS:
                continue
            if len(snippets) >= limit:
                return snippets
            if not url or url in existing_urls:
                continue
            if 'wikipedia.org' in url or 'wikidata.org' in url:
                continue
            html = fetch_url_text(url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            paragraphs = extract_paragraphs_from_soup(soup, max_paragraphs=2)
            if not paragraphs:
                continue
            text = truncate_text(' '.join(paragraphs), EXTERNAL_SNIPPET_MAX_CHARS)
            text = translate_to_spanish(text)
            name = urlparse(url).netloc or 'Fuente externa'
            snippets.append({'name': name, 'url': url, 'text': text})
            existing_urls.add(url)
            if len(snippets) >= limit:
                return snippets
    return snippets


def get_external_snippets(composer: str, sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    snippets: List[Dict[str, str]] = []
    seen_urls = set()
    for source in sources:
        url = source.get('url') or ''
        if not url or 'search' in url:
            continue
        domain = urlparse(url).netloc
        if domain in EXTERNAL_DOMAINS.values() and url.rstrip('/') == f"https://{domain}":
            continue
        html = fetch_url_text(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        paragraphs = extract_paragraphs_from_soup(soup, max_paragraphs=2)
        if not paragraphs:
            continue
        text = truncate_text(' '.join(paragraphs), EXTERNAL_SNIPPET_MAX_CHARS)
        text = translate_to_spanish(text)
        snippets.append({'name': source['name'], 'url': url, 'text': text})
        seen_urls.add(url)
        if len(snippets) >= EXTERNAL_SNIPPET_SOURCES:
            break
    if len(snippets) < EXTERNAL_SNIPPET_SOURCES:
        remaining = EXTERNAL_SNIPPET_SOURCES - len(snippets)
        snippets.extend(get_general_snippets(composer, remaining, seen_urls))
    return snippets


def select_snippet_by_keywords(snippets: List[Dict[str, str]], keywords: List[str]) -> Optional[str]:
    for snippet in snippets:
        lowered = snippet.get('text', '').lower()
        if any(keyword in lowered for keyword in keywords):
            return snippet.get('text')
    return None


def build_enriched_text(
    composer: str,
    base: str,
    snippets: List[Dict[str, str]],
    keywords: List[str],
    search_query: str,
) -> str:
    parts: List[str] = []
    if base:
        parts.append(base)
    for snippet in snippets:
        text = snippet.get('text') or ''
        lowered = text.lower()
        if not text or text in parts:
            continue
        if any(keyword in lowered for keyword in keywords):
            parts.append(text)
        if len(parts) >= 2:
            break
    if len(parts) < 2:
        extra = search_for_text(search_query, keywords)
        if extra and extra not in parts:
            parts.append(extra)
    return '\n\n'.join(parts).strip()


def get_wikipedia_image(title: str) -> Optional[str]:
    html = fetch_wikipedia_html(f"{title} film")
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return None
    img = infobox.find('img')
    if not img or not img.get('src'):
        return None
    src = img['src']
    if src.startswith('//'):
        return f"https:{src}"
    if src.startswith('/'):
        return f"https://en.wikipedia.org{src}"
    return src


def get_film_poster(
    title: str,
    composer_folder: Path,
    poster_url: Optional[str] = None,
    year: Optional[int] = None,
    poster_file: Optional[Path] = None,
) -> str:
    poster_file = poster_file or (composer_folder / 'posters' / poster_filename(title, year))
    if poster_file.exists():
        return str(poster_file)
    if not DOWNLOAD_POSTERS:
        if poster_url:
            return poster_url
        if TMDB_API_KEY:
            tmdb_poster = tmdb_search_movie(title, year)
            if tmdb_poster:
                return tmdb_poster
        wiki_img = get_wikipedia_image(title)
        if wiki_img:
            return wiki_img
        return PLACEHOLDER_IMAGE
    if poster_url:
        saved = download_image(poster_url, poster_file)
        if saved:
            return saved
    if TMDB_API_KEY:
        tmdb_poster = tmdb_search_movie(title, year)
        if tmdb_poster:
            saved = download_image(tmdb_poster, poster_file)
            if saved:
                return saved
    wiki_img = get_wikipedia_image(title)
    if wiki_img:
        saved = download_image(wiki_img, poster_file)
        if saved:
            return saved
    if POSTER_WEB_FALLBACK:
        urls = search_web(f"{title} movie poster", num=POSTER_SEARCH_RESULTS)
        for url in urls:
            netloc = urlparse(url).netloc.lower()
            if netloc in BLOCKED_DOMAINS:
                continue
            html = fetch_url_text(url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            og = soup.find('meta', property='og:image')
            img = og['content'] if og and og.get('content') else None
            if img:
                saved = download_image(img, poster_file)
                return saved or PLACEHOLDER_IMAGE
    return PLACEHOLDER_IMAGE


def get_composer_info(composer: str, composer_folder: Path) -> Dict:
    composer_folder.mkdir(parents=True, exist_ok=True)
    photo_filename = f"photo_{slugify(composer)}.jpg"
    photo_path = composer_folder / photo_filename
    info: Dict = {'name': composer, 'folder': composer_folder}
    html_es = fetch_wikipedia_html(f"{composer} compositor", lang='es') or fetch_wikipedia_html(composer, lang='es')
    html_en = None
    biography_parts: List[str] = []
    bio_text = fetch_wikipedia_extract(f"{composer} compositor", lang='es') or fetch_wikipedia_extract(composer, lang='es')
    if bio_text:
        biography_parts = [
            clean_text(p)
            for p in bio_text.split('\n\n')
            if len(clean_text(p)) >= MIN_PARAGRAPH_LEN
        ][:MAX_BIO_PARAGRAPHS]
    if not biography_parts:
        bio_text_en = fetch_wikipedia_extract(f"{composer} composer", lang='en')
        if bio_text_en:
            paragraphs = [
                clean_text(p)
                for p in bio_text_en.split('\n\n')
                if len(clean_text(p)) >= MIN_PARAGRAPH_LEN
            ][:MAX_BIO_PARAGRAPHS]
            biography_parts = translate_paragraphs(paragraphs)
    if not biography_parts and html_es:
        biography_parts = extract_paragraphs_from_soup(
            BeautifulSoup(html_es, 'html.parser'),
            max_paragraphs=MAX_BIO_PARAGRAPHS,
        )
    biography = '\n\n'.join(biography_parts)
    if biography:
        info['biography'] = biography

    style_text = extract_section_text(html_es, STYLE_SECTION_KEYWORDS, max_paragraphs=2) if html_es else ''
    if not style_text:
        html_en = html_en or fetch_wikipedia_html(f"{composer} composer", lang='en')
        if html_en:
            style_text = extract_section_text(html_en, STYLE_SECTION_KEYWORDS, max_paragraphs=2)
            style_text = translate_to_spanish(style_text)
    if not style_text:
        style_text = search_for_text(f"{composer} estilo musical compositor -site:wikipedia.org", STYLE_HINTS)
    if biography and style_text and style_text in biography:
        style_text = ''
    if style_text:
        info['style'] = style_text

    anecdote_text = extract_section_text(html_es, ANECDOTE_SECTION_KEYWORDS, max_paragraphs=2) if html_es else ''
    if not anecdote_text:
        html_en = html_en or fetch_wikipedia_html(f"{composer} composer", lang='en')
        if html_en:
            anecdote_text = extract_section_text(html_en, ANECDOTE_SECTION_KEYWORDS, max_paragraphs=2)
            anecdote_text = translate_to_spanish(anecdote_text)
    if not anecdote_text:
        anecdote_text = search_for_text(f"{composer} vida personal curiosidades -site:wikipedia.org", ANECDOTE_HINTS)
    if biography and anecdote_text and anecdote_text in biography:
        anecdote_text = ''
    if anecdote_text:
        info['anecdotes'] = anecdote_text

    infobox_html = html_es or html_en
    if infobox_html:
        soup = BeautifulSoup(infobox_html, 'html.parser')
        infobox = soup.find('table', class_='infobox')
        if infobox:
            img = infobox.find('img')
            if img and img.get('src'):
                photo_url = img['src']
                if photo_url.startswith('//'):
                    photo_url = f"https:{photo_url}"
                elif photo_url.startswith('/'):
                    photo_url = f"https://en.wikipedia.org{photo_url}"
                info['photo'] = download_image(photo_url, photo_path) or photo_url
    qid = get_wikidata_qid(composer)
    if qid and not info.get('country'):
        info['country'] = fetch_wikidata_country(qid)
    known_for_titles: List[str] = []
    person_id = None
    if TMDB_API_KEY:
        person_id, known_for_titles = tmdb_search_person(composer)
    if not info.get('photo') and person_id:
        profile_url = tmdb_person_profile(person_id)
        if profile_url:
            info['photo'] = download_image(profile_url, photo_path) or profile_url
    info['filmography'] = get_complete_filmography(composer, composer_folder)
    info['awards'] = get_detailed_awards(composer)
    top_boosts = get_top_10_films(composer)
    for title in known_for_titles:
        key = normalize_title_key(title)
        if not key:
            continue
        top_boosts[key] = max(top_boosts.get(key, 0), 2)
    top_entries = select_top_10_films(composer, info.get('filmography', []), info.get('awards', []), top_boosts)
    info['top_10_films'] = []
    for entry in top_entries:
        poster = entry.get('poster_local') or get_film_poster(
            entry.get('original_title') or entry.get('title', ''),
            composer_folder,
            entry.get('poster_url'),
            entry.get('year'),
            Path(entry['poster_file']) if entry.get('poster_file') else None,
        )
        info['top_10_films'].append({'entry': entry, 'poster': poster})
    if info['awards'] and info['filmography']:
        film_title_map: Dict[str, Dict[str, Optional[str]]] = {}
        for entry in info['filmography']:
            for key in build_title_keys(entry):
                film_title_map[key] = entry
        for award in info['awards']:
            film = award.get('film')
            if film:
                entry = film_title_map.get(normalize_title_key(film))
                if entry:
                    award['film'] = format_film_title(entry)
                elif TMDB_API_KEY and 'Título en España' not in film:
                    details = tmdb_search_movie_details(film, None)
                    if details:
                        award['film'] = format_film_title({
                            'original_title': details.get('original_title'),
                            'title_es': details.get('title_es'),
                        })
    info['external_sources'] = get_external_sources(composer)
    info['external_snippets'] = get_external_snippets(composer, info['external_sources'])
    deep_bio = False
    deep_style = False
    deep_facts = False
    deep_profile = get_source_pack_profile(composer)
    if not deep_profile:
        log(f"Source pack missing; falling back to deep research for {composer}", "WARNING")
        deep_profile = get_deep_research_profile(composer)
    if deep_profile:
        if deep_profile.get('biography'):
            info['biography'] = deep_profile['biography']
            deep_bio = True
        if deep_profile.get('style'):
            info['style'] = deep_profile['style']
            deep_style = True
        if deep_profile.get('facts'):
            info['anecdotes'] = deep_profile['facts']
            deep_facts = True
        if deep_profile.get('citations'):
            info['citations'] = deep_profile['citations']
    if info.get('biography') and not deep_bio:
        info['biography'] = ensure_spanish(info['biography'])
    if info.get('style') and not deep_style:
        info['style'] = ensure_spanish(info['style'])
    if info.get('anecdotes') and not deep_facts:
        info['anecdotes'] = ensure_spanish(info['anecdotes'])
    style_text = info.get('style', '')
    if not deep_style:
        if not style_text:
            style_text = select_snippet_by_keywords(info['external_snippets'], STYLE_HINTS) or ''
        if len(style_text) < 120:
            style_text = build_enriched_text(
                composer,
                style_text,
                info['external_snippets'],
                STYLE_HINTS,
                f"{composer} estilo musical compositor -site:wikipedia.org",
            )
        if biography and style_text and style_text in biography:
            style_text = ''
        if not style_text and info['external_snippets']:
            style_text = info['external_snippets'][0].get('text', '')
        if style_text:
            info['style'] = style_text
        else:
            info['style'] = "Información de estilo musical en proceso de documentación."
    anecdote_text = info.get('anecdotes', '')
    if not deep_facts:
        if not anecdote_text:
            anecdote_text = select_snippet_by_keywords(info['external_snippets'], ANECDOTE_HINTS) or ''
        if len(anecdote_text) < 120:
            anecdote_text = build_enriched_text(
                composer,
                anecdote_text,
                info['external_snippets'],
                ANECDOTE_HINTS,
                f"{composer} vida personal curiosidades -site:wikipedia.org",
            )
        if biography and anecdote_text and anecdote_text in biography:
            anecdote_text = ''
        if not anecdote_text and info['external_snippets']:
            anecdote_text = info['external_snippets'][-1].get('text', '')
        if anecdote_text:
            info['anecdotes'] = anecdote_text
        else:
            info['anecdotes'] = "Información de anécdotas y curiosidades en proceso de documentación."
    return info


def format_link(path: str, base: Path) -> str:
    if path.startswith('http://') or path.startswith('https://'):
        return path
    local = Path(path)
    if local.exists():
        return str(local.relative_to(base))
    return path


def format_film_title(entry: Dict[str, Optional[str]]) -> str:
    original = (entry.get('original_title') or entry.get('title') or '').strip()
    spanish = (entry.get('title_es') or '').strip()
    if not original and spanish:
        original = spanish
    if original and not spanish:
        spanish = original
    if original and spanish:
        return f"{original} (Título en España: {spanish})"
    return original or spanish


def escape_table_cell(value: str) -> str:
    return value.replace('|', '\\|')


def is_academy_award(award_name: str) -> bool:
    if not award_name:
        return False
    lowered = award_name.lower()
    return any(keyword in lowered for keyword in ('academy', 'oscar', 'academia'))


def format_award_label(award_name: str, status: str) -> str:
    if is_academy_award(award_name):
        translated = {'Win': 'Ganador', 'Nomination': 'Nominación'}.get(status, status)
        if translated == 'Ganador':
            return 'Premio de la Academia'
        if translated == 'Nominación':
            return 'Nominación de la Academia'
    return award_name


def create_markdown_file(composer_info: Dict, target: Path) -> None:
    lines = [f"# {composer_info['name']}\n"]
    photo = composer_info.get('photo')
    if photo:
        lines.append(f"![{composer_info['name']}]({format_link(photo, target.parent)})\n")
    lines.append("## País o nacionalidad\n")
    lines.append(f"{composer_info.get('country') or 'No disponible.'}\n")
    biography = composer_info.get('biography')
    if biography:
        lines.append("## Biografía\n")
        lines.append(f"{biography}\n")
    style = composer_info.get('style')
    if style:
        lines.append("## Estilo musical\n")
        lines.append(f"{style}\n")
    anecdotes = composer_info.get('anecdotes')
    if anecdotes:
        lines.append("## Datos curiosos y técnica de composición\n")
        lines.append(f"{anecdotes}\n")
    films = composer_info.get('top_10_films', [])
    if films:
        lines.append("## Top 10 bandas sonoras\n")
        for idx, film in enumerate(films, 1):
            entry = film.get('entry') or {}
            title_display = format_film_title(entry)
            year = entry.get('year')
            year_text = f" ({year})" if year else ""
            lines.append(f"{idx}. ***{title_display}***{year_text}")
            poster = film.get('poster')
            if poster:
                lines.append(f"    * **Póster:** [link]({format_link(poster, target.parent)})")
        lines.append('')
    filmography = composer_info.get('filmography', [])
    if filmography:
        lines.append("## Filmografía completa\n")
        lines.append("| Año | Título | Título original | Póster |")
        lines.append("| --- | --- | --- | --- |")
        for entry in filmography:
            year = str(entry.get('year') or '—')
            title_es = entry.get('title_es') or entry.get('title') or entry.get('original_title') or '—'
            original = entry.get('original_title') or entry.get('title') or '—'
            if title_es == original:
                original = '—'
            poster = entry.get('poster_local') or entry.get('poster_url')
            if poster:
                poster_cell = f"[Póster]({format_link(poster, target.parent)})"
            else:
                poster_cell = '—'
            lines.append(
                f"| {escape_table_cell(year)} | {escape_table_cell(title_es)} | "
                f"{escape_table_cell(original)} | {escape_table_cell(poster_cell)} |"
            )
        lines.append('')
    awards = composer_info.get('awards', [])
    if awards:
        lines.append("## Premios y nominaciones\n")
        status_map = {'Win': 'Ganador', 'Nomination': 'Nominación'}
        for award in awards:
            parts = []
            if award.get('year'):
                parts.append(str(award['year']))
            if award.get('award'):
                label = format_award_label(award['award'], award.get('status', ''))
                parts.append(label)
            if award.get('film'):
                parts.append(f"por *{award['film']}*")
            if award.get('status'):
                translated = status_map.get(award['status'], award['status'])
                if not is_academy_award(award.get('award', '')):
                    parts.append(f"({translated})")
            if parts:
                lines.append(f"* {' – '.join(parts)}")
        lines.append('')
    citations = composer_info.get('citations', [])
    if citations:
        lines.append("## Citas\n")
        for idx, url in enumerate(citations, 1):
            lines.append(f"[{idx}]: {url}")
        lines.append('')
    sources = composer_info.get('external_sources', [])
    if sources:
        lines.append("## Fuentes adicionales\n")
        for source in sources:
            lines.append(f"* [{source['name']}]({source['url']}) — {source['snippet']}")
        lines.append('')
    snippets = composer_info.get('external_snippets', [])
    if snippets:
        lines.append("## Notas externas\n")
        for snippet in snippets:
            lines.append(f"* {snippet['name']}: {snippet['text']}")
        lines.append('')
    target.write_text('\n'.join(lines).strip() + '\n', encoding='utf-8')


def main() -> None:
    master = OUTPUT_DIR / 'composers_master_list.md'
    composers_with_indices = get_composers_with_indices(master)
    if not composers_with_indices:
        print('No composers to process.')
        return
    start_index = int(os.getenv('START_INDEX', '1'))
    if start_index < 1:
        start_index = 1
    for position, (explicit_idx, composer) in enumerate(composers_with_indices, start=1):
        idx = explicit_idx or position
        if idx < start_index:
            continue
        slug = slugify(composer)
        filename = OUTPUT_DIR / f"{idx:03}_{slug}.md"
        composer_folder = OUTPUT_DIR / f"{idx:03}_{slug}"
        info = get_composer_info(composer, composer_folder)
        print(f"Processing {composer} -> {filename}")
        create_markdown_file(info, filename)
        print(f"  saved {filename}")


if __name__ == '__main__':
    main()
