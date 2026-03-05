"""Tests for forge.gui.utils.cad_availability module."""

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
    # Cleanup - remove cached modules to ensure fresh imports
    modules_to_remove = [k for k in sys.modules if k.startswith("forge.gui.utils")]
    for mod in modules_to_remove:
        del sys.modules[mod]


class TestCheckCadAvailable:
    """Tests for check_cad_available function."""

    def test_build123d_available(self, mock_streamlit):
        """Test when build123d is available."""
        # Create mock for forge.engine.cad module
        mock_cad_module = MagicMock()
        mock_cad_module.BUILD123D_AVAILABLE = True
        mock_cad_module.BUILD123D_VERSION = "0.7.0"
        sys.modules["forge.engine.cad"] = mock_cad_module

        from forge.gui.utils.cad_availability import check_cad_available

        status = check_cad_available()

        assert status["build123d"] is True
        assert status["build123d_version"] == "0.7.0"
        assert status["step_export"] is True
        assert status["stl_export"] is True
        assert status["freecad_script"] is True

    def test_build123d_not_available(self, mock_streamlit):
        """Test when build123d is not available."""
        mock_cad_module = MagicMock()
        mock_cad_module.BUILD123D_AVAILABLE = False
        mock_cad_module.BUILD123D_VERSION = None
        sys.modules["forge.engine.cad"] = mock_cad_module

        from forge.gui.utils.cad_availability import check_cad_available

        status = check_cad_available()

        assert status["build123d"] is False
        assert status["build123d_version"] is None
        assert status["step_export"] is False
        assert status["stl_export"] is False
        assert status["freecad_script"] is True  # Always available

    def test_freecad_always_available(self, mock_streamlit):
        """Test that FreeCAD script generation is always available."""
        # Even without forge.engine.cad, freecad_script should be True
        from forge.gui.utils.cad_availability import check_cad_available

        status = check_cad_available()

        # FreeCAD script generation has no dependencies
        assert status["freecad_script"] is True


class TestShowCadStatus:
    """Tests for show_cad_status function."""

    def test_shows_available_status(self, mock_streamlit):
        """Test display when build123d is available."""
        mock_cad_module = MagicMock()
        mock_cad_module.BUILD123D_AVAILABLE = True
        mock_cad_module.BUILD123D_VERSION = "0.7.0"
        sys.modules["forge.engine.cad"] = mock_cad_module

        # Mock columns context manager
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_streamlit.columns.return_value = [mock_col, mock_col]

        from forge.gui.utils.cad_availability import show_cad_status

        show_cad_status()

        mock_streamlit.markdown.assert_called()

    def test_shows_unavailable_status(self, mock_streamlit):
        """Test display when build123d is not available."""
        mock_cad_module = MagicMock()
        mock_cad_module.BUILD123D_AVAILABLE = False
        mock_cad_module.BUILD123D_VERSION = None
        sys.modules["forge.engine.cad"] = mock_cad_module

        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_streamlit.columns.return_value = [mock_col, mock_col]

        from forge.gui.utils.cad_availability import show_cad_status

        show_cad_status()

        # Should show install instructions
        mock_streamlit.caption.assert_called()
        mock_streamlit.code.assert_called()


