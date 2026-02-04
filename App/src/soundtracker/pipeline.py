"""Main pipeline for generating composer profiles.

This module orchestrates all services to generate complete
composer profile Markdown files with filmographies, awards,
and poster downloads.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from soundtracker.clients import TMDBClient, WikidataClient
from soundtracker.config import settings
from soundtracker.generators import MarkdownGenerator
from soundtracker.logging_config import log_progress, setup_logging
from soundtracker.models import ComposerInfo, ExternalSource, Film
from soundtracker.services import (
    AwardsService,
    BiographyService,
    FilmographyService,
    PosterService,
    ResearchService,
    Top10Service,
)
from soundtracker.utils.text import slugify

logger = logging.getLogger(__name__)


class CitationManager:
    """Assign numeric markers to citation URLs."""

    def __init__(self) -> None:
        self._mapping: dict[str, int] = {}

    def annotate(self, text: str, citations: list[str]) -> str:
        """Append citation markers to text."""
        if not text or not citations:
            return text

        markers = [self._marker(url) for url in citations]
        return f"{text} {' '.join(markers)}"

    def export(self) -> list[tuple[str, str]]:
        """Export list of (marker, url) sorted by marker number."""
        items = [(self._marker(url), url) for url in self._mapping]
        return sorted(items, key=lambda item: self._marker_number(item[0]))

    def _marker(self, url: str) -> str:
        if url not in self._mapping:
            self._mapping[url] = len(self._mapping) + 1
        return f"[^{self._mapping[url]}]"

    @staticmethod
    def _marker_number(marker: str) -> int:
        match = re.search(r"(\\d+)", marker)
        return int(match.group(1)) if match else 0


class ComposerPipeline:
    """Pipeline for generating complete composer profiles.

    Orchestrates data collection from multiple sources and
    generates formatted Markdown output files.

    Example:
        pipeline = ComposerPipeline()
        pipeline.process_composer("John Williams", index=1)
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        download_posters: bool = True,
    ) -> None:
        """Initialize the pipeline.

        Args:
            output_dir: Output directory for files.
            download_posters: Whether to download posters.
        """
        self.output_dir = output_dir or settings.output_dir
        self.download_posters = download_posters

        # Initialize clients
        self.tmdb = TMDBClient()
        self.wikidata = WikidataClient()

        # Initialize services
        self.biography_service = BiographyService()
        self.filmography_service = FilmographyService()
        self.awards_service = AwardsService()
        self.top10_service = Top10Service()
        self.poster_service = PosterService()
        self.research_service = ResearchService()

        # Initialize generator
        self.markdown_generator = MarkdownGenerator()

    def process_composer(
        self,
        name: str,
        index: Optional[int] = None,
    ) -> ComposerInfo:
        """Process a single composer and generate output.

        Args:
            name: Composer name.
            index: Optional index for filename.

        Returns:
            ComposerInfo with all collected data.
        """
        logger.info("Processing composer: %s", name)

        # Create folder structure
        slug = slugify(name)
        folder_name = f"{index:03d}_{slug}" if index else slug
        composer_folder = self.output_dir / folder_name
        composer_folder.mkdir(parents=True, exist_ok=True)

        # Initialize composer info
        info = ComposerInfo(name=name, index=index)

        # Get biography and related info
        self._collect_biography(info)

        # Get filmography
        self._collect_filmography(info, composer_folder)

        # Get awards
        self._collect_awards(info)

        # Select top 10
        self._select_top10(info)

        # Download posters
        if self.download_posters:
            self._download_posters(info, composer_folder)

        # Get external sources
        self._collect_external_sources(info)

        # Generate Markdown file
        filename = f"{index:03d}_{slug}.md" if index else f"{slug}.md"
        output_path = self.output_dir / filename
        self.markdown_generator.generate(info, output_path)

        logger.info("Completed: %s -> %s", name, output_path)
        return info

    def _apply_deep_research(self, info: ComposerInfo) -> None:
        """Enrich biography/style/facts using deep research.

        Args:
            info: ComposerInfo to update.
        """
        if not self.research_service.is_enabled:
            return

        research = self.research_service.get_profile(info.name)
        if not research:
            return

        citation_manager = CitationManager()

        if research.biography.text:
            info.biography = citation_manager.annotate(
                research.biography.text,
                research.biography.citations,
            )
        if research.style.text:
            info.style = citation_manager.annotate(
                research.style.text,
                research.style.citations,
            )
        if research.facts.text:
            info.anecdotes = citation_manager.annotate(
                research.facts.text,
                research.facts.citations,
            )

        for marker, url in citation_manager.export():
            info.external_sources.append(
                ExternalSource(
                    name=marker,
                    url=url,
                    snippet="Cita",
                    domain="citation",
                )
            )

    def _collect_biography(self, info: ComposerInfo) -> None:
        """Collect biography, style, and anecdotes.

        Args:
            info: ComposerInfo to populate.
        """
        logger.debug("Collecting biography for %s", info.name)

        bio_data = self.biography_service.get_biography(info.name)
        if isinstance(bio_data, dict):
            info.biography = bio_data.get("biography")
            info.style = bio_data.get("style")
            info.anecdotes = bio_data.get("anecdotes")
            info.image_url = bio_data.get("image_url")
        else:
            info.biography = bio_data
            info.style = self.biography_service.get_musical_style(info.name)
            info.anecdotes = self.biography_service.get_anecdotes(info.name)
            if not info.anecdotes:
                info.anecdotes = self.biography_service.derive_fun_facts(
                    info.biography or "",
                    info.style or "",
                )

        # Get TMDB profile image if available
        if not info.image_url and settings.is_tmdb_available:
            person_id, _ = self.tmdb.search_person(info.name)
            if person_id:
                info.tmdb_id = person_id
                info.image_url = self.tmdb.get_person_profile_url(person_id)

        # Get Wikidata QID
        qid = self.wikidata.get_qid(info.name)
        if qid:
            info.wikidata_qid = qid
            birth, death = self.wikidata.get_birth_death_years(qid)
            info.birth_year = birth
            info.death_year = death
            info.country = self.wikidata.get_country(qid)

        # Deep research enrichment (Perplexity)
        self._apply_deep_research(info)

    def _collect_filmography(
        self,
        info: ComposerInfo,
        composer_folder: Path,
    ) -> None:
        """Collect complete filmography.

        Args:
            info: ComposerInfo to populate.
            composer_folder: Folder for assets.
        """
        logger.debug("Collecting filmography for %s", info.name)

        films = self.filmography_service.get_complete_filmography(
            info.name,
            composer_folder=composer_folder,
            tmdb_id=info.tmdb_id,
            wikidata_qid=info.wikidata_qid,
        )
        info.filmography = films
        info.tv_credits = self.filmography_service.get_tv_credits(info.name)
        info.video_games = self.filmography_service.get_video_game_credits(info.name)

    def _collect_awards(self, info: ComposerInfo) -> None:
        """Collect awards and nominations.

        Args:
            info: ComposerInfo to populate.
        """
        logger.debug("Collecting awards for %s", info.name)
        info.awards = self.awards_service.get_awards(info.name)

    def _select_top10(self, info: ComposerInfo) -> None:
        """Select top 10 soundtracks.

        Args:
            info: ComposerInfo to populate.
        """
        logger.debug("Selecting top 10 for %s", info.name)

        # Get web rankings for boost scores
        boost_scores = {}
        if settings.use_web_toplists:
            boost_scores = self.top10_service.get_web_rankings(info.name)

        # Select top 10
        info.top_10 = self.top10_service.select_top_10(
            info.name,
            info.filmography,
            info.awards,
            boost_scores,
        )

    def _download_posters(
        self,
        info: ComposerInfo,
        composer_folder: Path,
    ) -> None:
        """Download posters for films.

        Args:
            info: ComposerInfo with films.
            composer_folder: Folder for assets.
        """
        logger.debug("Downloading posters for %s", info.name)

        # Download for top 10 first
        self.poster_service.download_posters(
            info.top_10,
            composer_folder,
        )

        # Download for full filmography if configured
        if settings.poster_limit == 0 or settings.poster_limit > 10:
            self.poster_service.download_posters(
                info.filmography,
                composer_folder,
                limit=settings.poster_limit or None,
            )

        # Download composer photo
        if info.image_url and not info.image_local:
            photo_path = composer_folder / f"photo_{slugify(info.name)}.jpg"
            result = self.poster_service._download_image(info.image_url, photo_path)
            if result:
                info.image_local = result

    def _collect_external_sources(self, info: ComposerInfo) -> None:
        """Collect external sources and snippets.

        Args:
            info: ComposerInfo to populate.
        """
        logger.debug("Collecting external sources for %s", info.name)

        # External domains to search
        external_domains = {
            "MundoBSO": "mundobso.com",
            "Film Score Monthly": "filmscoremonthly.com",
            "SoundtrackCollector": "soundtrackcollector.com",
            "WhatSong": "whatsong.org",
        }

        sources = []
        for name, domain in external_domains.items():
            sources.append(ExternalSource(
                name=name,
                url=f"https://{domain}",
                snippet=f"site:{domain}",
                domain=domain,
            ))

        info.external_sources.extend(sources)


def process_composers_from_list(
    master_list_path: Path,
    output_dir: Optional[Path] = None,
    start_index: int = 1,
    end_index: Optional[int] = None,
) -> list[ComposerInfo]:
    """Process multiple composers from a master list file.

    Args:
        master_list_path: Path to master list Markdown file.
        output_dir: Output directory.
        start_index: Start from this index.
        end_index: Stop at this index (inclusive).

    Returns:
        List of processed ComposerInfo objects.
    """
    setup_logging()

    # Parse master list
    composers = _parse_master_list(master_list_path)
    if not composers:
        logger.warning("No composers found in %s", master_list_path)
        return []

    # Filter by index range
    filtered = [
        (idx, name) for idx, name in composers
        if idx >= start_index and (end_index is None or idx <= end_index)
    ]

    logger.info("Processing %d composers (index %d-%s)",
                len(filtered), start_index, end_index or "end")

    # Process each composer
    pipeline = ComposerPipeline(output_dir=output_dir)
    results = []

    for i, (idx, name) in enumerate(filtered, 1):
        log_progress(i, len(filtered), f"Processing {name}")
        try:
            info = pipeline.process_composer(name, index=idx)
            results.append(info)
        except Exception as e:
            logger.error("Failed to process %s: %s", name, e)

    logger.info("Completed processing %d composers", len(results))
    return results


def _parse_master_list(path: Path) -> list[tuple[int, str]]:
    """Parse master list Markdown file.

    Args:
        path: Path to master list file.

    Returns:
        List of (index, name) tuples.
    """
    import re

    if not path.exists():
        logger.error("Master list not found: %s", path)
        return []

    composers = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                continue

            parts = [col.strip() for col in line.split("|") if col.strip()]
            if not parts:
                continue

            # Skip header rows
            if parts[0] in {"Name", "No.", "#"} or re.fullmatch(r"-+", parts[0]):
                continue

            # Parse index and name
            if parts[0].isdigit() and len(parts) >= 2:
                composers.append((int(parts[0]), parts[1]))

    return composers


# Convenience function for CLI
def main() -> None:
    """Main entry point for CLI."""
    setup_logging()

    master_list = settings.output_dir / "composers_master_list.md"
    if not master_list.exists():
        logger.error("Master list not found: %s", master_list)
        return

    process_composers_from_list(
        master_list,
        start_index=settings.start_index,
        end_index=settings.end_index,
    )


if __name__ == "__main__":
    main()
