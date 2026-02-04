#!/usr/bin/env python3
"""Build top lists for film and video game soundtrack composers.

Process (A+B then D):
1) Use structured sources (IMDb + Wikidata + Wikipedia if needed) to gather
   credits, birth/death dates, country, awards and nominations.
2) Seed with the old master list and Spanish composer lists to avoid starting
   from scratch and ensure full Spanish coverage.
3) Optionally crawl the web using SearchClient (Perplexity/Google) with the
   curated domain list to collect external sources (no ranking changes).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from soundtracker.clients import SearchClient, WikidataClient  # noqa: E402
from soundtracker.config import settings  # noqa: E402


FILM_TITLE_TYPES = ("movie", "short")
GAME_TITLE_TYPES = ("videoGame",)

FILM_LIST_QUERIES = [
    "top film composers",
    "best film score composers",
    "film score composers list",
    "greatest film music composers",
]

GAME_LIST_QUERIES = [
    "top video game composers",
    "best video game music composers",
    "video game soundtrack composers list",
]


@dataclass
class ImdbComposer:
    nconst: str
    name: str
    birth_year: Optional[int]
    death_year: Optional[int]
    credits: int


@dataclass
class ComposerRecord:
    name: str
    birth: str
    death: str
    country: str
    credits: int
    nominations: int
    awards: int
    is_spanish: bool


def normalize_name(name: str) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^A-Za-z\s\-']", " ", ascii_name)
    ascii_name = re.sub(r"\s+", " ", ascii_name)
    return ascii_name.strip().lower()


def is_person_name(name: str) -> bool:
    if not name:
        return False
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    if len(tokens) < 2:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    if "(" in name or ")" in name:
        return False
    return True


def clean_person_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r"\s*\(.*?\)", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def parse_master_list_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        if not parts or parts[0].lower() in {"no.", "name", "#"} or parts[0].startswith("---"):
            continue
        if len(parts) < 2:
            continue
        name = clean_person_name(parts[1].strip())
        if is_person_name(name):
            names.append(name)
    return names


def is_name_candidate(name: str) -> bool:
    if not name:
        return False
    if "(" in name or ")" in name:
        return False
    if "," in name or ";" in name:
        return False
    if len(name) > 60:
        return False
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    if len(tokens) < 2 or len(tokens) > 5:
        return False
    allowed_lower = {"de", "del", "la", "las", "los", "da", "dos", "van", "von"}
    for token in tokens:
        if token.lower() in allowed_lower:
            continue
        if not re.match(r"^[A-ZÁÉÍÓÚÜÑ]", token):
            return False
    return True


def extract_bold_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    names = []
    for match in re.findall(r"\\*\\*([^*]+)\\*\\*", text):
        name = match.strip()
        if is_name_candidate(name):
            names.append(name)
    return names


def load_spanish_names(paths: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in paths:
        for raw_name in extract_bold_names(path):
            cleaned = clean_person_name(raw_name)
            if cleaned:
                names.add(cleaned)
    return names


def load_external_domains(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"EXTERNAL_DOMAINS\s*=\s*\{(.*?)\}\s*", text, re.S)
    if not match:
        return []
    block = match.group(1)
    domains = []
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entry = re.search(r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]", line)
        if not entry:
            continue
        domains.append(entry.group(2))
    return domains


def query_imdb_composers(db_path: Path, title_types: tuple[str, ...]) -> list[ImdbComposer]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_credit_cache(conn)
    if title_types == FILM_TITLE_TYPES:
        credit_col = "film_credits"
    else:
        credit_col = "game_credits"
    query = f"""
        SELECT c.nconst,
               p.primaryName AS name,
               p.birthYear AS birthYear,
               p.deathYear AS deathYear,
               c.{credit_col} AS credit_count
        FROM composer_credit_counts c
        JOIN people p ON p.nconst = c.nconst
        WHERE c.{credit_col} > 0
    """
    rows: list[ImdbComposer] = []
    for row in conn.execute(query):
        name = row["name"]
        if not is_person_name(name):
            continue
        rows.append(
            ImdbComposer(
                nconst=row["nconst"],
                name=name,
                birth_year=row["birthYear"],
                death_year=row["deathYear"],
                credits=int(row["credit_count"] or 0),
            )
        )
    conn.close()
    return rows


def ensure_credit_cache(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='composer_credit_counts'"
    ).fetchone()
    if row:
        return
    print("Building composer_credit_counts cache (first run, this may take a few minutes)...")
    conn.execute(
        """
        CREATE TABLE composer_credit_counts AS
        SELECT c.nconst AS nconst,
               SUM(CASE WHEN t.titleType IN ('movie','short') THEN 1 ELSE 0 END) AS film_credits,
               SUM(CASE WHEN t.titleType IN ('videoGame') THEN 1 ELSE 0 END) AS game_credits
        FROM composer_credits c
        JOIN titles t ON t.tconst = c.tconst
        GROUP BY c.nconst
        """
    )
    conn.execute("CREATE INDEX idx_credit_counts_nconst ON composer_credit_counts (nconst)")
    conn.execute("CREATE INDEX idx_credit_counts_film ON composer_credit_counts (film_credits)")
    conn.execute("CREATE INDEX idx_credit_counts_game ON composer_credit_counts (game_credits)")
    conn.commit()
    print("composer_credit_counts cache built.")


def build_imdb_name_map(rows: list[ImdbComposer]) -> dict[str, ImdbComposer]:
    best: dict[str, ImdbComposer] = {}
    for row in rows:
        key = normalize_name(row.name)
        if not key:
            continue
        if key not in best or row.credits > best[key].credits:
            best[key] = row
    return best


def build_candidates(
    imdb_rows: list[ImdbComposer],
    mandatory_names: set[str],
    spanish_names: set[str],
    top_n: int,
) -> list[ImdbComposer]:
    imdb_map = build_imdb_name_map(imdb_rows)
    candidates: list[ImdbComposer] = []
    seen: set[str] = set()
    non_imdb_spanish = 0

    for raw_name in sorted(mandatory_names):
        name = clean_person_name(raw_name)
        if not name:
            continue
        key = normalize_name(name)
        row = imdb_map.get(key)
        if row:
            if row.nconst in seen:
                continue
            candidates.append(row)
            seen.add(row.nconst)
        else:
            if name in spanish_names:
                non_imdb_spanish += 1
                candidates.append(
                    ImdbComposer(
                        nconst="",
                        name=name,
                        birth_year=None,
                        death_year=None,
                        credits=0,
                    )
                )

    remaining = sorted(imdb_rows, key=lambda r: r.credits, reverse=True)
    target_count = top_n + non_imdb_spanish
    for row in remaining:
        if row.nconst in seen:
            continue
        candidates.append(row)
        seen.add(row.nconst)
        if len(candidates) >= target_count:
            break

    return candidates


def collect_wikidata_info(
    wikidata: WikidataClient,
    name: str,
    spanish_names: set[str],
    fallback_birth: Optional[int],
    fallback_death: Optional[int],
) -> tuple[str, str, str, int, int]:
    qid = wikidata.get_qid(name)
    birth = str(fallback_birth) if fallback_birth else ""
    death = str(fallback_death) if fallback_death else ""
    country = ""
    wins = 0
    nominations = 0

    if not qid:
        return birth, death, country, wins, nominations

    summary = wikidata.get_person_summary(qid)
    birth_date = summary.get("birth")
    death_date = summary.get("death")
    if birth_date:
        birth = birth_date.split("T")[0]
    if death_date:
        death = death_date.split("T")[0]

    if not country:
        country = summary.get("country") or ""

    wins_val = summary.get("wins")
    noms_val = summary.get("nominations")
    if wins_val:
        try:
            wins = int(float(wins_val))
        except ValueError:
            wins = 0
    if noms_val:
        try:
            nominations = int(float(noms_val))
        except ValueError:
            nominations = 0

    return birth, death, country, wins, nominations


def crawl_list_sources(
    search: SearchClient,
    queries: list[str],
    max_per_domain: int,
    output_path: Path,
    domains: list[str],
    max_domains: int,
) -> None:
    results: dict[str, list[str]] = {}
    if not domains:
        output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        return

    domain_list = domains[:max_domains] if max_domains else domains
    for query in queries:
        urls: list[str] = []
        for domain in domain_list:
            base = domain
            if base.startswith("http"):
                parsed = urlparse(base)
                domain = parsed.netloc
            full_query = f"site:{domain} {query}"
            hits = search.search(full_query, num=max_per_domain)
            for url in hits:
                if url not in urls:
                    urls.append(url)
            if len(urls) >= max_per_domain * 5:
                break
            time.sleep(0.2)
        results[query] = urls

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(path: Path, title: str, records: list[ComposerRecord]) -> None:
    records_sorted = sorted(records, key=lambda r: normalize_name(r.name))
    lines = []
    lines.append(title)
    lines.append("")
    lines.append(f"## Lista principal ({len(records_sorted)} entradas)")
    lines.append("")
    lines.append("| No. | Name | Birth | Death | Country | Soundtracks | Nominations | Awards |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for idx, record in enumerate(records_sorted, 1):
        lines.append(
            f"| {idx:03d} | {record.name} | {record.birth} | {record.death} | "
            f"{record.country} | {record.credits} | {record.nominations} | {record.awards} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_list(
    imdb_rows: list[ImdbComposer],
    mandatory_names: set[str],
    spanish_names: set[str],
    top_n: int,
    crawl: bool,
    crawl_output: Path,
    crawl_domains: list[str],
    crawl_max_domains: int,
    crawl_queries: list[str],
    cache: dict[str, dict[str, str]],
    cache_path: Path,
    log_every: int,
    limit: Optional[int],
    wikidata_delay: float,
    refresh_missing: bool,
    title: str,
    output_path: Path,
) -> None:
    wikidata = WikidataClient()
    candidates = build_candidates(imdb_rows, mandatory_names, spanish_names, top_n)

    if limit:
        candidates = candidates[:limit]

    records: list[ComposerRecord] = []
    for idx, row in enumerate(candidates, 1):
        cached = cache.get(row.name)
        needs_refresh = False
        if cached and refresh_missing:
            needs_refresh = not cached.get("birth") or not cached.get("country")

        if cached and not needs_refresh:
            birth = cached.get("birth", "")
            death = cached.get("death", "")
            country = cached.get("country", "")
            wins = int(cached.get("wins", 0))
            nominations = int(cached.get("nominations", 0))
        else:
            birth, death, country, wins, nominations = collect_wikidata_info(
                wikidata,
                row.name,
                spanish_names,
                row.birth_year,
                row.death_year,
            )
            if not country and row.nconst and row.name in spanish_names:
                country = "España"
            cache[row.name] = {
                "birth": birth,
                "death": death,
                "country": country,
                "wins": str(wins),
                "nominations": str(nominations),
            }
        if log_every and idx % log_every == 0:
            print(f"Processed {idx}/{len(candidates)}")
            if cache_path:
                cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        if row.nconst == "" and not birth and not country and wins == 0 and nominations == 0:
            continue

        records.append(
            ComposerRecord(
                name=row.name,
                birth=birth,
                death=death,
                country=country,
                credits=row.credits,
                nominations=nominations,
                awards=wins,
                is_spanish=row.name in spanish_names,
            )
        )
        if len(records) >= top_n:
            break
        time.sleep(wikidata_delay)

    if cache_path:
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    if crawl:
        crawl_list_sources(
            SearchClient(),
            crawl_queries,
            max_per_domain=1,
            output_path=crawl_output,
            domains=crawl_domains,
            max_domains=crawl_max_domains,
        )

    write_markdown(output_path, title, records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build top lists for film and video game composers.")
    parser.add_argument("--imdb-db", type=Path, default=settings.imdb_db_path)
    parser.add_argument(
        "--old-master",
        type=Path,
        default=settings.output_dir / "OLD" / "composers_master_list.md",
    )
    parser.add_argument(
        "--spanish-md",
        type=Path,
        nargs="*",
        default=[
            BASE_DIR / "intermediate_research" / "Compositores de Bandas Sonoras Españolas.md",
            BASE_DIR / "intermediate_research" / "Cronología de Compositores de Cine Español.md",
        ],
    )
    parser.add_argument("--top-film", type=int, default=300)
    parser.add_argument("--top-games", type=int, default=100)
    parser.add_argument("--film-output", type=Path, default=settings.output_dir / "top_300_cine.md")
    parser.add_argument("--games-output", type=Path, default=settings.output_dir / "top_100_videojuegos.md")
    parser.add_argument("--crawl", action="store_true")
    parser.add_argument("--crawl-output", type=Path, default=settings.output_dir / "top_lists_sources.json")
    parser.add_argument("--crawl-max-domains", type=int, default=8)
    parser.add_argument("--cache", type=Path, default=settings.output_dir / "top_lists_cache.json")
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--wikidata-delay", type=float, default=0.5)
    parser.add_argument("--refresh-missing", action="store_true")
    parser.add_argument("--only-film", action="store_true")
    parser.add_argument("--only-games", action="store_true")
    parser.add_argument(
        "--external-domains-file",
        type=Path,
        default=BASE_DIR / "scripts" / "create_composer_files.py",
    )

    args = parser.parse_args()

    old_names = set(parse_master_list_names(args.old_master))
    spanish_names = load_spanish_names(args.spanish_md)
    mandatory = old_names | spanish_names
    crawl_domains = load_external_domains(args.external_domains_file)
    cache = {}
    if args.cache and args.cache.exists():
        try:
            cache = json.loads(args.cache.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}

    if not args.only_games:
        film_rows = query_imdb_composers(args.imdb_db, FILM_TITLE_TYPES)
        build_list(
            film_rows,
            mandatory,
            spanish_names,
            args.top_film,
            args.crawl,
            args.crawl_output,
            crawl_domains,
            args.crawl_max_domains,
            FILM_LIST_QUERIES,
            cache,
            args.cache,
            args.log_every,
            args.limit,
            args.wikidata_delay,
            args.refresh_missing,
            "# Top 300 Compositores de Bandas Sonoras (Cine)",
            args.film_output,
        )

    if not args.only_film:
        game_rows = query_imdb_composers(args.imdb_db, GAME_TITLE_TYPES)
        build_list(
            game_rows,
            set(),
            set(),
            args.top_games,
            args.crawl,
            args.crawl_output,
            crawl_domains,
            args.crawl_max_domains,
            GAME_LIST_QUERIES,
            cache,
            args.cache,
            args.log_every,
            args.limit,
            args.wikidata_delay,
            args.refresh_missing,
            "# Top 100 Compositores de Bandas Sonoras (Videojuegos)",
            args.games_output,
        )


if __name__ == "__main__":
    main()
