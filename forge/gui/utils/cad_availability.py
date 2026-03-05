"""CAD dependency availability checking."""

import streamlit as st


def check_cad_available() -> dict:
    """Check availability of CAD export dependencies."""
    status = {
        "build123d": False,
        "build123d_version": None,
        "step_export": False,
        "stl_export": False,
        "freecad_script": True,  # Always available (no deps)
    }

    try:
        from forge.engine.cad import BUILD123D_AVAILABLE, BUILD123D_VERSION

        status["build123d"] = BUILD123D_AVAILABLE
        status["build123d_version"] = BUILD123D_VERSION
        status["step_export"] = BUILD123D_AVAILABLE
        status["stl_export"] = BUILD123D_AVAILABLE
    except ImportError:
        pass

    return status


def show_cad_status() -> None:
    """Display CAD dependency status in sidebar."""
    status = check_cad_available()

    st.markdown("#### CAD Export Status")

    col1, col2 = st.columns(2)

    with col1:
        if status["build123d"]:
            st.markdown("build123d")
        else:
            st.markdown("build123d")

    with col2:
        if status["freecad_script"]:
            st.markdown("FreeCAD")

    if not status["build123d"]:
        st.caption("Install for STEP/STL:")
        st.code("pip install cellcad[cad]", language="bash")

