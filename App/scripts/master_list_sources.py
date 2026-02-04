#!/usr/bin/env python3
"""Utilities for harvesting composer names from web sources."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from soundtracker.clients.search import SearchClient

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

DEFAULT_QUERIES = [
    {"query": "film composers list", "mediums": {"cine"}},
    {"query": "list of film score composers", "mediums": {"cine"}},
    {"query": "best soundtrack composers list", "mediums": {"cine"}},
    {"query": "compositores de bandas sonoras lista", "mediums": {"cine"}},
    {"query": "compositores de musica para cine lista", "mediums": {"cine"}},
    {"query": "television composers list", "mediums": {"serie", "tv"}},
    {"query": "tv soundtrack composers list", "mediums": {"serie", "tv"}},
    {"query": "compositores de series de television lista", "mediums": {"serie", "tv"}},
    {"query": "video game composers list", "mediums": {"videojuego"}},
    {"query": "compositores de musica de videojuegos lista", "mediums": {"videojuego"}},
    {"query": "anime composers list", "mediums": {"serie"}},
]

TOP100_QUERIES = [
    {"query": "top 100 film composers", "mediums": {"cine"}},
    {"query": "greatest film score composers", "mediums": {"cine"}},
    {"query": "best film composers of all time", "mediums": {"cine"}},
    {"query": "best soundtrack composers list", "mediums": {"cine"}},
    {"query": "top video game composers", "mediums": {"videojuego"}},
    {"query": "best video game composers", "mediums": {"videojuego"}},
    {"query": "best television composers", "mediums": {"serie", "tv"}},
    {"query": "top tv composers", "mediums": {"serie", "tv"}},
    {"query": "mejores compositores de bandas sonoras", "mediums": {"cine"}},
]

NAME_RE = re.compile(
    r"\b[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+(?:[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+|[A-Z][a-z]+|de|del|da|dos|van|von|di|la|le|du|st\.?)){1,4}\b"
)

NOISE_TOKENS = {
    "Composer",
    "Compositor",
    "Soundtrack",
    "Banda",
    "Sonora",
    "Music",
    "Score",
    "Film",
    "Series",
    "TV",
    "Video",
    "Game",
    "Games",
    "Lista",
    "List",
    "Top",
    "Best",
    "Greatest",
    "Wikipedia",
    "Navigation",
    "Contents",
    "Donate",
    "Search",
    "Article",
    "Tools",
    "Help",
    "Main",
}


@dataclass
class WebName:
    name: str
    mediums: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)

    def add_source(self, source: str, mediums: Iterable[str]) -> None:
        self.sources.add(source)
        self.mediums.update(mediums)


def normalize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\\s+", " ", name)
    name = re.sub(r"\\s*\\(.*?\\)", "", name).strip()
    return name


def extract_candidate_names(text: str) -> list[str]:
    names: list[str] = []
    for match in NAME_RE.findall(text):
        if not match or len(match.split()) < 2:
            continue
        if any(token in NOISE_TOKENS for token in match.split()):
            continue
        names.append(match.strip())
    return names


def fetch_text(url: str, timeout: int = 15, max_chars: int = 12000) -> str:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Soundtracker/2.0"})
        if not resp.ok:
            return ""
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    chunks: list[str] = []
    for tag in soup.select("li, h2, h3, h4, p, td"):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        if len(text) < 3 or len(text) > 240:
            continue
        chunks.append(text)

    text = " | ".join(chunks)
    return text[:max_chars]


def gemini_filter_names(text: str, candidates: list[str]) -> list[str]:
    if not GEMINI_API_KEY or not candidates:
        return candidates

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Extrae SOLO nombres de compositores de bandas sonoras del texto. "
                            "Devuelve SOLO JSON con un array de nombres. "
                            "No incluyas titulos de peliculas ni instituciones."
                        )
                    },
                    {"text": f"Texto:\n{text[:6000]}"},
                    {"text": f"Candidatos:\n{', '.join(candidates[:200])}"},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
    }

    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Gemini filtering failed: %s", exc)
        return candidates

    candidates_data = data.get("candidates") or []
    if not candidates_data:
        return candidates
    parts = (candidates_data[0].get("content") or {}).get("parts") or []
    content = "".join(part.get("text", "") for part in parts).strip()
    if not content:
        return candidates

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [normalize_name(str(item)) for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        return candidates

    return candidates


def harvest_web_names(
    queries: list[dict],
    max_urls_total: int,
    max_urls_per_query: int,
    use_gemini: bool,
    gemini_max_urls: int = 12,
) -> dict[str, WebName]:
    search_client = SearchClient()
    all_names: dict[str, WebName] = {}
    seen_urls: set[str] = set()

    gemini_used = 0

    for query_def in queries:
        query = query_def["query"]
        mediums = query_def.get("mediums", set())
        urls = search_client.search(query, num=max_urls_per_query)
        for url in urls:
            if len(seen_urls) >= max_urls_total:
                break
            if url in seen_urls:
                continue
            seen_urls.add(url)

            text = fetch_text(url)
            if not text:
                continue
            candidates = extract_candidate_names(text)
            use_gemini_now = use_gemini and gemini_used < gemini_max_urls
            if use_gemini_now:
                candidates = gemini_filter_names(text, candidates)
                gemini_used += 1
            for name in candidates:
                cleaned = normalize_name(name)
                if not cleaned:
                    continue
                key = cleaned.lower()
                if key not in all_names:
                    all_names[key] = WebName(name=cleaned)
                all_names[key].add_source(url, mediums)

        logger.info(
            "Query '%s' -> %d urls, names so far: %d",
            query,
            len(urls),
            len(all_names),
        )

    logger.info("Web harvest completed: %d names, %d urls, gemini=%d", len(all_names), len(seen_urls), gemini_used)
    return all_names
