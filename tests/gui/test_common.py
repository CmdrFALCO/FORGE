"""Tests for forge.gui.utils.common module."""

import sys
from unittest.mock import MagicMock

import pytest

pytest.importorskip("streamlit")


# Mock streamlit before importing forge.gui.utils
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock streamlit module for all tests."""
    mock_st = MagicMock()
    mock_st.session_state = {}
    sys.modules["streamlit"] = mock_st
    yield mock_st
    # Cleanup
    if "forge.gui.utils.common" in sys.modules:
        del sys.modules["forge.gui.utils.common"]
    if "forge.gui.utils.cad_availability" in sys.modules:
        del sys.modules["forge.gui.utils.cad_availability"]
    if "forge.gui.utils" in sys.modules:
        del sys.modules["forge.gui.utils"]


class TestFormatFileSize:
    """Tests for format_file_size function."""

    def test_bytes(self, mock_streamlit):
        """Test formatting bytes."""
        from forge.gui.utils.common import format_file_size

        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_kilobytes(self, mock_streamlit):
        """Test formatting kilobytes."""
        from forge.gui.utils.common import format_file_size

        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(10240) == "10.0 KB"

    def test_megabytes(self, mock_streamlit):
        """Test formatting megabytes."""
        from forge.gui.utils.common import format_file_size

        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 2) == "2.00 MB"
        assert format_file_size(1024 * 1024 * 10) == "10.00 MB"


class TestGetOutputDir:
    """Tests for get_output_dir function."""

    def test_creates_directory(self, tmp_path, monkeypatch, mock_streamlit):
        """Test that output directory is created."""
        from forge.gui.utils import common

        # Monkeypatch Path to use temp directory
        monkeypatch.chdir(tmp_path)

        output_dir = common.get_output_dir()

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert output_dir.name == "outputs"

    def test_returns_existing_directory(self, tmp_path, monkeypatch, mock_streamlit):
        """Test that existing directory is returned."""
        from forge.gui.utils import common

        monkeypatch.chdir(tmp_path)
        (tmp_path / "outputs").mkdir()

        output_dir = common.get_output_dir()

        assert output_dir.exists()
        assert output_dir.name == "outputs"


class TestInitSessionState:
    """Tests for init_session_state function."""

    def test_initializes_defaults(self, mock_streamlit):
        """Test that defaults are set."""
        from forge.gui.utils.common import init_session_state

        mock_streamlit.session_state = {}

        init_session_state({"key1": "value1", "key2": 42})

        assert mock_streamlit.session_state["key1"] == "value1"
        assert mock_streamlit.session_state["key2"] == 42

    def test_does_not_overwrite_existing(self, mock_streamlit):
        """Test that existing values are preserved."""
        from forge.gui.utils.common import init_session_state

        mock_streamlit.session_state = {"key1": "existing"}

        init_session_state({"key1": "new_value", "key2": "new"})

        assert mock_streamlit.session_state["key1"] == "existing"
        assert mock_streamlit.session_state["key2"] == "new"


