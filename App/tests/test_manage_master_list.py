"""Tests for manage_master_list.py script."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from manage_master_list import (
    ComposerEntry,
    MasterListManager,
    OutputFile,
    OutputFilesManager,
    SyncEngine,
    SyncReport,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_composer_entry() -> ComposerEntry:
    """Return a sample composer entry."""
    return ComposerEntry(
        index=53,
        name="John Williams",
        birth_year=1932,
        death_year=None,
        country="USA",
    )


@pytest.fixture
def sample_master_list_content() -> str:
    """Return sample master list content."""
    return """# Film Music Composers: A Consolidated and Chronological List

## Lista principal (3 entradas)

| No. | Name | Birth Year | Death Year | Country |
|---|---|---|---|---|
| 001 | Herbert Stothart | 1885 | 1949 | USA |
| 002 | Max Steiner | 1888 | 1971 | Austria |
| 053 | John Williams | 1932 |  | USA |
"""


@pytest.fixture
def temp_outputs_dir(tmp_path: Path) -> Path:
    """Create a temporary outputs directory with sample files."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()

    # Create sample composer files
    (outputs / "001_herbert_stothart.md").write_text("# Herbert Stothart\n\n## Biografía\n")
    (outputs / "002_max_steiner.md").write_text("# Max Steiner\n\n## Biografía\n")
    (outputs / "053_john_williams.md").write_text("# John Williams\n\n## Biografía\n")

    # Create master list
    master_list = outputs / "composers_master_list.md"
    master_list.write_text("""# Film Music Composers: A Consolidated and Chronological List

## Lista principal (3 entradas)

| No. | Name | Birth Year | Death Year | Country |
|---|---|---|---|---|
| 001 | Herbert Stothart | 1885 | 1949 | USA |
| 002 | Max Steiner | 1888 | 1971 | Austria |
| 053 | John Williams | 1932 |  | USA |
""")

    return outputs


# =============================================================================
# COMPOSER ENTRY TESTS
# =============================================================================


class TestComposerEntry:
    """Tests for ComposerEntry dataclass."""

    def test_create_entry(self, sample_composer_entry: ComposerEntry) -> None:
        """Test creating a composer entry."""
        assert sample_composer_entry.index == 53
        assert sample_composer_entry.name == "John Williams"
        assert sample_composer_entry.birth_year == 1932
        assert sample_composer_entry.death_year is None
        assert sample_composer_entry.country == "USA"

    def test_generate_slug(self, sample_composer_entry: ComposerEntry) -> None:
        """Test slug generation."""
        assert sample_composer_entry.slug == "john_williams"

    def test_generate_slug_special_chars(self) -> None:
        """Test slug generation with special characters."""
        entry = ComposerEntry(index=1, name="Ennio Morricone")
        assert entry.slug == "ennio_morricone"

        entry2 = ComposerEntry(index=2, name="Miklós Rózsa")
        assert entry2.slug == "miklos_rozsa"

        entry3 = ComposerEntry(index=3, name="Tōru Takemitsu")
        assert entry3.slug == "toru_takemitsu"

    def test_index_str(self, sample_composer_entry: ComposerEntry) -> None:
        """Test index string formatting."""
        assert sample_composer_entry.index_str == "053"

    def test_filename(self, sample_composer_entry: ComposerEntry) -> None:
        """Test filename generation."""
        assert sample_composer_entry.filename == "053_john_williams.md"

    def test_folder_name(self, sample_composer_entry: ComposerEntry) -> None:
        """Test folder name generation."""
        assert sample_composer_entry.folder_name == "053_john_williams"

    def test_to_table_row(self, sample_composer_entry: ComposerEntry) -> None:
        """Test conversion to markdown table row."""
        row = sample_composer_entry.to_table_row()
        assert row == "| 053 | John Williams | 1932 |  | USA |"

    def test_to_table_row_with_death_year(self) -> None:
        """Test table row with death year."""
        entry = ComposerEntry(
            index=1,
            name="Herbert Stothart",
            birth_year=1885,
            death_year=1949,
            country="USA",
        )
        row = entry.to_table_row()
        assert row == "| 001 | Herbert Stothart | 1885 | 1949 | USA |"


# =============================================================================
# OUTPUT FILE TESTS
# =============================================================================


class TestOutputFile:
    """Tests for OutputFile dataclass."""

    def test_from_path(self, temp_outputs_dir: Path) -> None:
        """Test creating OutputFile from path."""
        path = temp_outputs_dir / "053_john_williams.md"
        output_file = OutputFile.from_path(path)

        assert output_file is not None
        assert output_file.index == 53
        assert output_file.slug == "john_williams"
        assert output_file.name == "John Williams"

    def test_from_path_invalid(self, tmp_path: Path) -> None:
        """Test OutputFile.from_path with invalid filename."""
        invalid_file = tmp_path / "invalid_file.md"
        invalid_file.write_text("content")

        output_file = OutputFile.from_path(invalid_file)
        assert output_file is None

    def test_from_path_extracts_name(self, tmp_path: Path) -> None:
        """Test that from_path extracts name from markdown header."""
        md_file = tmp_path / "001_test_composer.md"
        md_file.write_text("# Test Composer Name\n\n## Biografía\n")

        output_file = OutputFile.from_path(md_file)
        assert output_file is not None
        assert output_file.name == "Test Composer Name"


# =============================================================================
# MASTER LIST MANAGER TESTS
# =============================================================================


class TestMasterListManager:
    """Tests for MasterListManager class."""

    def test_load(self, temp_outputs_dir: Path) -> None:
        """Test loading master list."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        assert len(manager.entries) == 3
        assert manager.entries[0].name == "Herbert Stothart"
        assert manager.entries[2].name == "John Williams"

    def test_get_by_index(self, temp_outputs_dir: Path) -> None:
        """Test getting entry by index."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        entry = manager.get_by_index(53)
        assert entry is not None
        assert entry.name == "John Williams"

        entry_none = manager.get_by_index(999)
        assert entry_none is None

    def test_get_by_name(self, temp_outputs_dir: Path) -> None:
        """Test getting entry by name."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        entry = manager.get_by_name("John Williams")
        assert entry is not None
        assert entry.index == 53

        # Case insensitive
        entry_lower = manager.get_by_name("john williams")
        assert entry_lower is not None

    def test_get_next_index(self, temp_outputs_dir: Path) -> None:
        """Test getting next available index."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        next_idx = manager.get_next_index()
        assert next_idx == 54  # Max is 53, so next is 54

    def test_add_entry(self, temp_outputs_dir: Path) -> None:
        """Test adding an entry."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        new_entry = ComposerEntry(
            index=54,
            name="Hans Zimmer",
            birth_year=1957,
            country="Germany",
        )
        manager.add_entry(new_entry)

        assert len(manager.entries) == 4
        assert manager.get_by_name("Hans Zimmer") is not None

    def test_add_entry_duplicate_index_raises(self, temp_outputs_dir: Path) -> None:
        """Test that adding duplicate index raises error."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        with pytest.raises(ValueError, match="Índice 53 ya existe"):
            manager.add_entry(ComposerEntry(index=53, name="Duplicate"))

    def test_add_entry_duplicate_name_raises(self, temp_outputs_dir: Path) -> None:
        """Test that adding duplicate name raises error."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        with pytest.raises(ValueError, match="John Williams"):
            manager.add_entry(ComposerEntry(index=100, name="John Williams"))

    def test_remove_entry(self, temp_outputs_dir: Path) -> None:
        """Test removing an entry."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        entry = manager.remove_entry(53)
        assert entry is not None
        assert entry.name == "John Williams"
        assert len(manager.entries) == 2
        assert manager.get_by_index(53) is None

    def test_save(self, temp_outputs_dir: Path) -> None:
        """Test saving master list."""
        manager = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager.load()

        # Add new entry
        manager.add_entry(ComposerEntry(index=54, name="Hans Zimmer", birth_year=1957))
        manager.save()

        # Reload and verify
        manager2 = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        manager2.load()

        assert len(manager2.entries) == 4
        assert manager2.get_by_name("Hans Zimmer") is not None


# =============================================================================
# OUTPUT FILES MANAGER TESTS
# =============================================================================


class TestOutputFilesManager:
    """Tests for OutputFilesManager class."""

    def test_load(self, temp_outputs_dir: Path) -> None:
        """Test loading output files."""
        manager = OutputFilesManager(temp_outputs_dir)
        manager.load()

        assert len(manager.files) == 3

    def test_get_by_index(self, temp_outputs_dir: Path) -> None:
        """Test getting file by index."""
        manager = OutputFilesManager(temp_outputs_dir)
        manager.load()

        output_file = manager.get_by_index(53)
        assert output_file is not None
        assert output_file.slug == "john_williams"

    def test_get_by_slug(self, temp_outputs_dir: Path) -> None:
        """Test getting file by slug."""
        manager = OutputFilesManager(temp_outputs_dir)
        manager.load()

        output_file = manager.get_by_slug("john_williams")
        assert output_file is not None
        assert output_file.index == 53

    def test_create_base_file(self, temp_outputs_dir: Path) -> None:
        """Test creating a base file for a new composer."""
        manager = OutputFilesManager(temp_outputs_dir)

        entry = ComposerEntry(index=54, name="Hans Zimmer")
        path = manager.create_base_file(entry)

        assert path.exists()
        assert path.name == "054_hans_zimmer.md"

        content = path.read_text()
        assert "# Hans Zimmer" in content
        assert "## Biografía" in content

        # Check folder was created
        folder = temp_outputs_dir / "054_hans_zimmer" / "posters"
        assert folder.is_dir()


# =============================================================================
# SYNC ENGINE TESTS
# =============================================================================


class TestSyncEngine:
    """Tests for SyncEngine class."""

    def test_check_sync_all_synced(self, temp_outputs_dir: Path) -> None:
        """Test sync check when everything is synced."""
        master_list = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        output_files = OutputFilesManager(temp_outputs_dir)

        engine = SyncEngine(master_list, output_files)
        report = engine.check_sync()

        assert report.is_synced
        assert report.total_in_list == 3
        assert report.total_files == 3
        assert len(report.in_list_no_file) == 0
        assert len(report.in_file_no_list) == 0

    def test_check_sync_missing_file(self, temp_outputs_dir: Path) -> None:
        """Test sync check when a file is missing."""
        # Remove one file
        (temp_outputs_dir / "053_john_williams.md").unlink()

        master_list = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        output_files = OutputFilesManager(temp_outputs_dir)

        engine = SyncEngine(master_list, output_files)
        report = engine.check_sync()

        assert not report.is_synced
        assert len(report.in_list_no_file) == 1
        assert report.in_list_no_file[0].name == "John Williams"

    def test_check_sync_extra_file(self, temp_outputs_dir: Path) -> None:
        """Test sync check when there's an extra file not in list."""
        # Create extra file
        (temp_outputs_dir / "100_extra_composer.md").write_text("# Extra Composer\n")

        master_list = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        output_files = OutputFilesManager(temp_outputs_dir)

        engine = SyncEngine(master_list, output_files)
        report = engine.check_sync()

        assert not report.is_synced
        assert len(report.in_file_no_list) == 1
        assert report.in_file_no_list[0].slug == "extra_composer"

    def test_add_composer(self, temp_outputs_dir: Path) -> None:
        """Test adding a new composer."""
        master_list = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        output_files = OutputFilesManager(temp_outputs_dir)

        engine = SyncEngine(master_list, output_files)
        entry = engine.add_composer(
            name="Hans Zimmer",
            birth_year=1957,
            country="Germany",
        )

        assert entry.index == 54
        assert entry.name == "Hans Zimmer"

        # Verify file was created
        assert (temp_outputs_dir / "054_hans_zimmer.md").exists()

        # Verify in master list
        master_list.load()
        assert master_list.get_by_name("Hans Zimmer") is not None

    def test_remove_composer(self, temp_outputs_dir: Path) -> None:
        """Test removing a composer."""
        master_list = MasterListManager(temp_outputs_dir / "composers_master_list.md")
        output_files = OutputFilesManager(temp_outputs_dir)

        engine = SyncEngine(master_list, output_files)
        entry = engine.remove_composer(53, archive=True)

        assert entry is not None
        assert entry.name == "John Williams"

        # Verify file was archived (not deleted)
        assert not (temp_outputs_dir / "053_john_williams.md").exists()
        archived_dir = temp_outputs_dir / "_archived"
        assert archived_dir.exists()
        archived_files = list(archived_dir.glob("*john_williams.md"))
        assert len(archived_files) == 1


# =============================================================================
# SYNC REPORT TESTS
# =============================================================================


class TestSyncReport:
    """Tests for SyncReport dataclass."""

    def test_is_synced_true(self) -> None:
        """Test is_synced returns True when no issues."""
        report = SyncReport(total_in_list=3, total_files=3)
        assert report.is_synced

    def test_is_synced_false(self) -> None:
        """Test is_synced returns False when there are issues."""
        report = SyncReport(
            total_in_list=3,
            total_files=2,
            in_list_no_file=[ComposerEntry(1, "Test")],
        )
        assert not report.is_synced

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        report = SyncReport(total_in_list=3, total_files=3)
        d = report.to_dict()

        assert d["synced"] is True
        assert d["total_in_list"] == 3
        assert d["total_files"] == 3
        assert d["in_list_no_file"] == []
