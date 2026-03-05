"""Common utilities for Streamlit pages."""

from pathlib import Path

import streamlit as st


def init_session_state(defaults: dict) -> None:
    """Initialize session state with defaults if not already set."""
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_output_dir() -> Path:
    """Get or create the outputs directory."""
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def show_export_success(filepath: Path, file_type: str) -> None:
    """Display success message with file info."""
    st.success(f"{file_type} exported successfully!")
    st.code(str(filepath), language=None)
    st.caption(f"Size: {format_file_size(filepath.stat().st_size)}")


def create_download_link(filepath: Path, label: str) -> None:
    """Create a download button for a file."""
    with open(filepath, "rb") as f:
        st.download_button(
            label=label,
            data=f.read(),
            file_name=filepath.name,
            mime="application/octet-stream",
        )

