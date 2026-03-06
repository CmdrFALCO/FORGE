"""Tests for CAD availability checking."""

import pytest

from forge.engine.cad.availability import BUILD123D_AVAILABLE, get_cad_status, require_build123d


class TestAvailability:
    """Tests for availability module."""

    def test_get_cad_status_returns_dict(self) -> None:
        """Should return status dict with expected keys."""
        status = get_cad_status()

        assert isinstance(status, dict)
        assert "build123d_available" in status
        assert "build123d_version" in status

    def test_build123d_available_is_bool(self) -> None:
        """BUILD123D_AVAILABLE should be a boolean."""
        assert isinstance(BUILD123D_AVAILABLE, bool)

    def test_require_build123d_when_available(self) -> None:
        """Should not raise if build123d is available."""
        if not BUILD123D_AVAILABLE:
            pytest.skip("build123d not installed")

        # Should not raise
        require_build123d()

    def test_require_build123d_error_message(self) -> None:
        """Error message should be helpful when build123d not available."""
        if BUILD123D_AVAILABLE:
            pytest.skip("build123d is installed")

        with pytest.raises(ImportError) as excinfo:
            require_build123d()

        assert "build123d" in str(excinfo.value).lower()
        assert "pip install" in str(excinfo.value).lower()


class TestOptionalImport:
    """Tests for optional import behavior."""

    def test_core_imports_without_build123d(self) -> None:
        """Core CAD module should import without build123d."""
        # These should always work
        from forge.engine.cad import (
            BUILD123D_AVAILABLE,
            CADAssembly,
            CADBody,
            MaterialGroup,
        )

        assert BUILD123D_AVAILABLE is not None
        assert MaterialGroup is not None
        assert CADBody is not None
        assert CADAssembly is not None

    def test_generator_import_conditional(self) -> None:
        """Generator should only be importable when build123d available."""
        from forge.engine.cad import BUILD123D_AVAILABLE

        if BUILD123D_AVAILABLE:
            from forge.engine.cad import Build123dGenerator

            assert Build123dGenerator is not None
        else:
            with pytest.raises(ImportError):
                from forge.engine.cad import Build123dGenerator  # noqa: F401
