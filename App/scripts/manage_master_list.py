#!/usr/bin/env python3
"""Gestor de Master List - Sincronización bidireccional.

Este script gestiona la sincronización entre:
- composers_master_list.md (lista maestra)
- outputs/*.md (archivos de compositor)

Comandos disponibles:
    --sync-check    Verifica estado de sincronización
    --add           Añade un compositor
    --remove        Elimina/archiva un compositor
    --rebuild-index Reconstruye master list desde outputs
    --renumber      Reordena índices por año de nacimiento
    --rename        Renombra un compositor

Uso:
    python scripts/manage_master_list.py --sync-check
    python scripts/manage_master_list.py --add "John Williams" --birth 1932 --country USA
    python scripts/manage_master_list.py --remove 053 --archive
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Rutas base
BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "outputs"
MASTER_LIST_PATH = OUTPUTS_DIR / "composers_master_list.md"
ARCHIVE_DIR = OUTPUTS_DIR / "_archived"


# =============================================================================
# MODELOS DE DATOS
# =============================================================================


@dataclass
class ComposerEntry:
    """Entrada de compositor en la master list."""

    index: int
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    country: str = ""
    slug: str = ""

    def __post_init__(self) -> None:
        """Genera slug si no existe."""
        if not self.slug:
            self.slug = self._generate_slug(self.name)

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Genera slug normalizado desde nombre."""
        slug = name.lower()
        # Reemplazar caracteres especiales
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u",
            "ñ": "n", "ø": "o", "ł": "l", "ś": "s", "ź": "z",
            "ż": "z", "ć": "c", "ę": "e", "ą": "a", "ō": "o",
            "ū": "u", "ā": "a", "ī": "i",
        }
        for old, new in replacements.items():
            slug = slug.replace(old, new)
        # Solo letras, números y espacios
        slug = re.sub(r"[^a-z0-9\s]", "", slug)
        # Espacios a guiones bajos
        slug = re.sub(r"\s+", "_", slug.strip())
        return slug

    @property
    def index_str(self) -> str:
        """Índice como string de 3 dígitos."""
        return f"{self.index:03d}"

    @property
    def filename(self) -> str:
        """Nombre de archivo esperado."""
        return f"{self.index_str}_{self.slug}.md"

    @property
    def folder_name(self) -> str:
        """Nombre de carpeta de assets esperada."""
        return f"{self.index_str}_{self.slug}"

    def to_table_row(self) -> str:
        """Convierte a fila de tabla Markdown."""
        death = str(self.death_year) if self.death_year else ""
        return f"| {self.index_str} | {self.name} | {self.birth_year or ''} | {death} | {self.country} |"


@dataclass
class OutputFile:
    """Archivo de output de compositor."""

    path: Path
    index: int
    slug: str
    name: str = ""
    has_poster_folder: bool = False
    poster_count: int = 0

    @classmethod
    def from_path(cls, path: Path) -> Optional["OutputFile"]:
        """Crea OutputFile desde path."""
        match = re.match(r"(\d{3})_(.+)\.md$", path.name)
        if not match:
            return None

        index = int(match.group(1))
        slug = match.group(2)

        # Extraer nombre del contenido
        name = ""
        try:
            content = path.read_text(encoding="utf-8")
            name_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            if name_match:
                name = name_match.group(1).strip()
        except Exception:
            pass

        # Verificar carpeta de posters
        folder = path.parent / f"{index:03d}_{slug}"
        has_folder = folder.is_dir()
        poster_count = 0
        if has_folder:
            posters_dir = folder / "posters"
            if posters_dir.is_dir():
                poster_count = len(list(posters_dir.glob("*.jpg")))

        return cls(
            path=path,
            index=index,
            slug=slug,
            name=name,
            has_poster_folder=has_folder,
            poster_count=poster_count,
        )


@dataclass
class SyncReport:
    """Reporte de sincronización."""

    in_list_no_file: list[ComposerEntry] = field(default_factory=list)
    in_file_no_list: list[OutputFile] = field(default_factory=list)
    name_mismatches: list[tuple[ComposerEntry, OutputFile]] = field(default_factory=list)
    duplicate_indices: list[int] = field(default_factory=list)
    index_gaps: list[int] = field(default_factory=list)
    total_in_list: int = 0
    total_files: int = 0

    @property
    def is_synced(self) -> bool:
        """Verifica si está sincronizado."""
        return (
            not self.in_list_no_file
            and not self.in_file_no_list
            and not self.name_mismatches
            and not self.duplicate_indices
        )

    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "synced": self.is_synced,
            "total_in_list": self.total_in_list,
            "total_files": self.total_files,
            "in_list_no_file": [e.name for e in self.in_list_no_file],
            "in_file_no_list": [f.slug for f in self.in_file_no_list],
            "name_mismatches": [(e.name, f.name) for e, f in self.name_mismatches],
            "duplicate_indices": self.duplicate_indices,
            "index_gaps": self.index_gaps,
        }

    def print_report(self) -> None:
        """Imprime reporte formateado."""
        print("\n" + "=" * 60)
        print("REPORTE DE SINCRONIZACIÓN")
        print("=" * 60)

        print(f"\nTotal en master list: {self.total_in_list}")
        print(f"Total archivos output: {self.total_files}")

        if self.is_synced:
            print("\n✅ Todo sincronizado correctamente")
        else:
            if self.in_list_no_file:
                print(f"\n❌ En lista SIN archivo ({len(self.in_list_no_file)}):")
                for entry in self.in_list_no_file[:10]:
                    print(f"   - {entry.index_str}: {entry.name}")
                if len(self.in_list_no_file) > 10:
                    print(f"   ... y {len(self.in_list_no_file) - 10} más")

            if self.in_file_no_list:
                print(f"\n❌ Archivo SIN entrada en lista ({len(self.in_file_no_list)}):")
                for f in self.in_file_no_list[:10]:
                    print(f"   - {f.index:03d}: {f.slug}")
                if len(self.in_file_no_list) > 10:
                    print(f"   ... y {len(self.in_file_no_list) - 10} más")

            if self.name_mismatches:
                print(f"\n⚠️ Discrepancias de nombre ({len(self.name_mismatches)}):")
                for entry, output in self.name_mismatches[:10]:
                    print(f"   - {entry.index_str}: lista='{entry.name}' vs archivo='{output.name}'")

            if self.duplicate_indices:
                print(f"\n❌ Índices duplicados: {self.duplicate_indices}")

            if self.index_gaps:
                print(f"\n⚠️ Huecos en índices: {self.index_gaps[:20]}")

        print("\n" + "=" * 60)


# =============================================================================
# MASTER LIST MANAGER
# =============================================================================


class MasterListManager:
    """Gestiona el archivo composers_master_list.md.

    Example:
        manager = MasterListManager()
        manager.load()
        entry = manager.get_by_name("John Williams")
        if entry:
            print(entry.index_str, entry.name)
    """

    def __init__(self, path: Path = MASTER_LIST_PATH) -> None:
        """Inicializa el manager."""
        self.path = path
        self._entries: list[ComposerEntry] = []
        self._header_lines: list[str] = []
        self._loaded = False

    def load(self) -> None:
        """Carga y parsea el archivo master list."""
        if not self.path.exists():
            logger.warning(f"Master list no encontrada: {self.path}")
            self._loaded = True
            return

        content = self.path.read_text(encoding="utf-8")
        lines = content.split("\n")

        self._entries = []
        self._header_lines = []
        in_table = False
        header_done = False

        for line in lines:
            # Detectar inicio de tabla
            if line.startswith("| No."):
                in_table = True
                header_done = True
                self._header_lines.append(line)
                continue

            # Saltar línea de separación de tabla
            if in_table and line.startswith("|---"):
                self._header_lines.append(line)
                continue

            # Parsear filas de datos
            if in_table and line.startswith("|"):
                entry = self._parse_table_row(line)
                if entry:
                    self._entries.append(entry)
            elif not header_done:
                self._header_lines.append(line)

        self._loaded = True
        logger.info(f"Cargados {len(self._entries)} compositores de master list")

    def _parse_table_row(self, line: str) -> Optional[ComposerEntry]:
        """Parsea una fila de la tabla."""
        parts = [p.strip() for p in line.split("|")]
        # Filtrar partes vacías (inicio y fin)
        parts = [p for p in parts if p]

        if len(parts) < 2:
            return None

        try:
            index = int(parts[0])
            name = parts[1]
            birth_year = int(parts[2]) if len(parts) > 2 and parts[2] else None
            death_year = int(parts[3]) if len(parts) > 3 and parts[3] else None
            country = parts[4] if len(parts) > 4 else ""

            return ComposerEntry(
                index=index,
                name=name,
                birth_year=birth_year,
                death_year=death_year,
                country=country,
            )
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parseando fila: {line} - {e}")
            return None

    def save(self, sort_by_index: bool = True) -> None:
        """Guarda el archivo master list."""
        if sort_by_index:
            self._entries.sort(key=lambda e: e.index)

        lines = []

        # Header
        lines.append("# Film Music Composers: A Consolidated and Chronological List")
        lines.append("")
        lines.append(f"## Lista principal ({len(self._entries)} entradas)")
        lines.append("")
        lines.append("| No. | Name | Birth Year | Death Year | Country |")
        lines.append("|---|---|---|---|---|")

        # Datos
        for entry in self._entries:
            lines.append(entry.to_table_row())

        # Escribir
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info(f"Master list guardada: {len(self._entries)} entradas")

    @property
    def entries(self) -> list[ComposerEntry]:
        """Retorna las entradas."""
        if not self._loaded:
            self.load()
        return self._entries

    def get_by_index(self, index: int) -> Optional[ComposerEntry]:
        """Obtiene entrada por índice."""
        for entry in self.entries:
            if entry.index == index:
                return entry
        return None

    def get_by_name(self, name: str) -> Optional[ComposerEntry]:
        """Obtiene entrada por nombre (fuzzy)."""
        name_lower = name.lower()
        for entry in self.entries:
            if entry.name.lower() == name_lower:
                return entry
        return None

    def get_next_index(self) -> int:
        """Obtiene el siguiente índice disponible."""
        if not self.entries:
            return 1
        return max(e.index for e in self.entries) + 1

    def add_entry(self, entry: ComposerEntry) -> None:
        """Añade una entrada."""
        # Verificar duplicados
        if self.get_by_index(entry.index):
            raise ValueError(f"Índice {entry.index} ya existe")
        if self.get_by_name(entry.name):
            raise ValueError(f"Compositor '{entry.name}' ya existe")

        self._entries.append(entry)
        logger.info(f"Añadido: {entry.index_str} - {entry.name}")

    def remove_entry(self, index: int) -> Optional[ComposerEntry]:
        """Elimina una entrada por índice."""
        entry = self.get_by_index(index)
        if entry:
            self._entries.remove(entry)
            logger.info(f"Eliminado de lista: {entry.index_str} - {entry.name}")
        return entry

    def update_entry(self, index: int, **kwargs) -> Optional[ComposerEntry]:
        """Actualiza una entrada."""
        entry = self.get_by_index(index)
        if not entry:
            return None

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        return entry


# =============================================================================
# OUTPUT FILES MANAGER
# =============================================================================


class OutputFilesManager:
    """Gestiona los archivos de output.

    Example:
        outputs = OutputFilesManager()
        outputs.load()
        first = outputs.get_by_index(1)
        if first:
            print(first.path)
    """

    def __init__(self, output_dir: Path = OUTPUTS_DIR) -> None:
        """Inicializa el manager."""
        self.output_dir = output_dir
        self._files: list[OutputFile] = []
        self._loaded = False

    def load(self) -> None:
        """Escanea y carga los archivos de output."""
        self._files = []

        for path in sorted(self.output_dir.glob("*.md")):
            # Ignorar master list y otros archivos especiales
            if path.name.startswith(("composers_", "test_", "deep-", "compass_", "Los ")):
                continue

            output_file = OutputFile.from_path(path)
            if output_file:
                self._files.append(output_file)

        self._loaded = True
        logger.info(f"Encontrados {len(self._files)} archivos de compositor")

    @property
    def files(self) -> list[OutputFile]:
        """Retorna los archivos."""
        if not self._loaded:
            self.load()
        return self._files

    def get_by_index(self, index: int) -> Optional[OutputFile]:
        """Obtiene archivo por índice."""
        for f in self.files:
            if f.index == index:
                return f
        return None

    def get_by_slug(self, slug: str) -> Optional[OutputFile]:
        """Obtiene archivo por slug."""
        for f in self.files:
            if f.slug == slug:
                return f
        return None

    def create_base_file(self, entry: ComposerEntry) -> Path:
        """Crea archivo base para un compositor."""
        path = self.output_dir / entry.filename

        content = f"""# {entry.name}

## Biografía

*Información pendiente de generar.*

## Estilo musical

*Información pendiente de generar.*

## Top 10 bandas sonoras

*Pendiente de generar.*

## Filmografía completa

*Pendiente de generar.*

## Premios y nominaciones

*Pendiente de generar.*

## Fuentes

- Generado automáticamente por SOUNDTRACKER
"""
        path.write_text(content, encoding="utf-8")
        logger.info(f"Creado archivo base: {path.name}")

        # Crear carpeta de assets
        folder = self.output_dir / entry.folder_name / "posters"
        folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Creada carpeta: {entry.folder_name}/posters/")

        return path

    def archive_file(self, index: int, permanent: bool = False) -> Optional[Path]:
        """Archiva o elimina un archivo de compositor."""
        output_file = self.get_by_index(index)
        if not output_file:
            logger.warning(f"No se encontró archivo con índice {index}")
            return None

        if permanent:
            # Eliminar permanentemente
            output_file.path.unlink()
            logger.info(f"Eliminado permanentemente: {output_file.path.name}")

            # Eliminar carpeta si existe
            folder = self.output_dir / f"{index:03d}_{output_file.slug}"
            if folder.is_dir():
                shutil.rmtree(folder)
                logger.info(f"Eliminada carpeta: {folder.name}")

            return output_file.path

        # Archivar
        ARCHIVE_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Mover archivo
        archive_path = ARCHIVE_DIR / f"{timestamp}_{output_file.path.name}"
        shutil.move(str(output_file.path), str(archive_path))
        logger.info(f"Archivado: {output_file.path.name} -> {archive_path.name}")

        # Mover carpeta si existe
        folder = self.output_dir / f"{index:03d}_{output_file.slug}"
        if folder.is_dir():
            archive_folder = ARCHIVE_DIR / f"{timestamp}_{folder.name}"
            shutil.move(str(folder), str(archive_folder))
            logger.info(f"Archivada carpeta: {folder.name}")

        return archive_path

    def rename_file(self, old_index: int, new_index: int, new_slug: str) -> Optional[Path]:
        """Renombra un archivo y su carpeta."""
        output_file = self.get_by_index(old_index)
        if not output_file:
            return None

        # Renombrar archivo
        new_filename = f"{new_index:03d}_{new_slug}.md"
        new_path = self.output_dir / new_filename
        output_file.path.rename(new_path)
        logger.info(f"Renombrado: {output_file.path.name} -> {new_filename}")

        # Renombrar carpeta si existe
        old_folder = self.output_dir / f"{old_index:03d}_{output_file.slug}"
        if old_folder.is_dir():
            new_folder = self.output_dir / f"{new_index:03d}_{new_slug}"
            old_folder.rename(new_folder)
            logger.info(f"Renombrada carpeta: {old_folder.name} -> {new_folder.name}")

            # Actualizar referencias en el archivo Markdown
            content = new_path.read_text(encoding="utf-8")
            content = content.replace(
                f"{old_index:03d}_{output_file.slug}/",
                f"{new_index:03d}_{new_slug}/",
            )
            new_path.write_text(content, encoding="utf-8")

        return new_path


# =============================================================================
# SYNC ENGINE
# =============================================================================


class SyncEngine:
    """Motor de sincronización entre master list y output files.

    Example:
        engine = SyncEngine()
        report = engine.check_sync()
        if not report.is_synced:
            report.print_report()
    """

    def __init__(
        self,
        master_list: Optional[MasterListManager] = None,
        output_files: Optional[OutputFilesManager] = None,
    ) -> None:
        """Inicializa el motor."""
        self.master_list = master_list or MasterListManager()
        self.output_files = output_files or OutputFilesManager()

    def check_sync(self) -> SyncReport:
        """Verifica el estado de sincronización."""
        self.master_list.load()
        self.output_files.load()

        report = SyncReport(
            total_in_list=len(self.master_list.entries),
            total_files=len(self.output_files.files),
        )

        # Crear mapas por índice
        list_by_index = {e.index: e for e in self.master_list.entries}
        files_by_index = {f.index: f for f in self.output_files.files}

        # Detectar duplicados en lista
        seen_indices: set[int] = set()
        for entry in self.master_list.entries:
            if entry.index in seen_indices:
                report.duplicate_indices.append(entry.index)
            seen_indices.add(entry.index)

        # En lista pero sin archivo
        for index, entry in list_by_index.items():
            if index not in files_by_index:
                report.in_list_no_file.append(entry)

        # Archivo sin entrada en lista
        for index, output_file in files_by_index.items():
            if index not in list_by_index:
                report.in_file_no_list.append(output_file)

        # Discrepancias de nombre
        for index in set(list_by_index.keys()) & set(files_by_index.keys()):
            entry = list_by_index[index]
            output_file = files_by_index[index]
            if output_file.name and entry.name.lower() != output_file.name.lower():
                report.name_mismatches.append((entry, output_file))

        # Detectar huecos en índices
        if self.master_list.entries:
            max_index = max(e.index for e in self.master_list.entries)
            all_indices = set(e.index for e in self.master_list.entries)
            for i in range(1, max_index + 1):
                if i not in all_indices:
                    report.index_gaps.append(i)

        return report

    def add_composer(
        self,
        name: str,
        birth_year: Optional[int] = None,
        death_year: Optional[int] = None,
        country: str = "",
        generate: bool = False,
    ) -> ComposerEntry:
        """Añade un nuevo compositor."""
        self.master_list.load()

        # Verificar que no existe
        if self.master_list.get_by_name(name):
            raise ValueError(f"Compositor '{name}' ya existe en la lista")

        # Crear entrada
        index = self.master_list.get_next_index()
        entry = ComposerEntry(
            index=index,
            name=name,
            birth_year=birth_year,
            death_year=death_year,
            country=country,
        )

        # Añadir a lista
        self.master_list.add_entry(entry)
        self.master_list.save()

        # Crear archivo base
        self.output_files.create_base_file(entry)

        if generate:
            logger.info("Opción --generate: ejecutar pipeline para poblar datos")
            # TODO: Integrar con pipeline de generación

        return entry

    def remove_composer(
        self,
        index: int,
        archive: bool = True,
        permanent: bool = False,
    ) -> Optional[ComposerEntry]:
        """Elimina/archiva un compositor."""
        self.master_list.load()

        entry = self.master_list.remove_entry(index)
        if not entry:
            logger.warning(f"No se encontró compositor con índice {index}")
            return None

        self.master_list.save()

        # Archivar/eliminar archivo
        self.output_files.archive_file(index, permanent=permanent and not archive)

        return entry

    def rebuild_from_outputs(self, backup: bool = True) -> int:
        """Reconstruye master list desde archivos de output."""
        self.output_files.load()

        if backup and MASTER_LIST_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = MASTER_LIST_PATH.with_suffix(f".{timestamp}.bak")
            shutil.copy(MASTER_LIST_PATH, backup_path)
            logger.info(f"Backup creado: {backup_path.name}")

        # Crear nuevas entradas desde archivos
        entries = []
        for output_file in self.output_files.files:
            entry = ComposerEntry(
                index=output_file.index,
                name=output_file.name or output_file.slug.replace("_", " ").title(),
                slug=output_file.slug,
            )
            entries.append(entry)

        # Reemplazar entradas
        self.master_list._entries = entries
        self.master_list._loaded = True
        self.master_list.save()

        logger.info(f"Master list reconstruida con {len(entries)} entradas")
        return len(entries)

    def renumber_by_birth_year(self) -> int:
        """Reordena índices por año de nacimiento."""
        self.master_list.load()
        self.output_files.load()

        # Ordenar por año de nacimiento
        sorted_entries = sorted(
            self.master_list.entries,
            key=lambda e: (e.birth_year or 9999, e.name),
        )

        # Crear mapa de cambios
        changes: list[tuple[int, int, ComposerEntry]] = []
        for new_index, entry in enumerate(sorted_entries, start=1):
            if entry.index != new_index:
                changes.append((entry.index, new_index, entry))

        if not changes:
            logger.info("Los índices ya están ordenados por año de nacimiento")
            return 0

        logger.info(f"Se renumerarán {len(changes)} compositores")

        # Primero renombrar a índices temporales (para evitar colisiones)
        temp_offset = 1000
        for old_index, new_index, entry in changes:
            temp_index = old_index + temp_offset
            self.output_files.rename_file(old_index, temp_index, entry.slug)

        # Luego renombrar a índices finales
        for old_index, new_index, entry in changes:
            temp_index = old_index + temp_offset
            self.output_files.rename_file(temp_index, new_index, entry.slug)
            entry.index = new_index

        # Guardar lista actualizada
        self.master_list.save()

        return len(changes)


# =============================================================================
# CLI
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Crea el parser de argumentos."""
    parser = argparse.ArgumentParser(
        description="Gestor de Master List - Sincronización bidireccional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s --sync-check
  %(prog)s --add "John Williams" --birth 1932 --country USA
  %(prog)s --remove 053 --archive
  %(prog)s --rebuild-index
  %(prog)s --renumber
  %(prog)s --rename 053 "John Towner Williams"
        """,
    )

    # Comandos principales (mutuamente excluyentes)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sync-check",
        action="store_true",
        help="Verifica estado de sincronización",
    )
    group.add_argument(
        "--add",
        metavar="NAME",
        help="Añade un compositor con el nombre especificado",
    )
    group.add_argument(
        "--remove",
        metavar="INDEX",
        type=int,
        help="Elimina/archiva compositor por índice",
    )
    group.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Reconstruye master list desde archivos de output",
    )
    group.add_argument(
        "--renumber",
        action="store_true",
        help="Reordena índices por año de nacimiento",
    )
    group.add_argument(
        "--rename",
        nargs=2,
        metavar=("INDEX", "NEW_NAME"),
        help="Renombra un compositor",
    )

    # Opciones para --add
    parser.add_argument("--birth", type=int, help="Año de nacimiento")
    parser.add_argument("--death", type=int, help="Año de fallecimiento")
    parser.add_argument("--country", default="", help="País de origen")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Ejecutar pipeline para generar datos (con --add)",
    )

    # Opciones para --remove
    parser.add_argument(
        "--archive",
        action="store_true",
        default=True,
        help="Archivar en lugar de eliminar (default)",
    )
    parser.add_argument(
        "--permanent",
        action="store_true",
        help="Eliminar permanentemente (requiere confirmación)",
    )

    # Opciones generales
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verbose",
    )

    return parser


def main() -> int:
    """Función principal."""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    engine = SyncEngine()

    try:
        if args.sync_check:
            report = engine.check_sync()
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            else:
                report.print_report()
            return 0 if report.is_synced else 1

        elif args.add:
            entry = engine.add_composer(
                name=args.add,
                birth_year=args.birth,
                death_year=args.death,
                country=args.country,
                generate=args.generate,
            )
            print(f"✅ Añadido: {entry.index_str} - {entry.name}")
            print(f"   Archivo: {entry.filename}")
            return 0

        elif args.remove is not None:
            if args.permanent:
                confirm = input(
                    f"⚠️ ¿Eliminar PERMANENTEMENTE compositor {args.remove}? (y/N): "
                )
                if confirm.lower() != "y":
                    print("Cancelado")
                    return 1

            entry = engine.remove_composer(
                index=args.remove,
                archive=args.archive,
                permanent=args.permanent,
            )
            if entry:
                action = "eliminado" if args.permanent else "archivado"
                print(f"✅ Compositor {action}: {entry.index_str} - {entry.name}")
            else:
                print(f"❌ No se encontró compositor con índice {args.remove}")
                return 1
            return 0

        elif args.rebuild_index:
            count = engine.rebuild_from_outputs()
            print(f"✅ Master list reconstruida con {count} entradas")
            return 0

        elif args.renumber:
            count = engine.renumber_by_birth_year()
            if count:
                print(f"✅ Renumerados {count} compositores")
            else:
                print("✅ Los índices ya están ordenados")
            return 0

        elif args.rename:
            index = int(args.rename[0])
            new_name = args.rename[1]
            engine.master_list.load()
            entry = engine.master_list.update_entry(index, name=new_name)
            if entry:
                # Regenerar slug
                entry.slug = entry._generate_slug(new_name)
                engine.master_list.save()
                # Renombrar archivo
                engine.output_files.rename_file(index, index, entry.slug)
                print(f"✅ Renombrado: {entry.index_str} - {entry.name}")
            else:
                print(f"❌ No se encontró compositor con índice {index}")
                return 1
            return 0

    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
