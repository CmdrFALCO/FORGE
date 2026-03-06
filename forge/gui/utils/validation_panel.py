"""Validation panel widget for Streamlit."""

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from forge.engine.geometry.validation import ValidationReport


def render_validation_panel(
    report: "ValidationReport",
    key: str = "validation_panel",
    show_passed: bool = False,
) -> None:
    """Render validation results panel.

    Args:
        report: ValidationReport to display
        key: Unique key for Streamlit widgets
        show_passed: If True, show passed checks (default: only failures)
    """
    from forge.engine.geometry.validation import Severity

    # Summary header with color
    if report.passed and not report.has_warnings:
        st.success(f"{report.summary()}")
    elif report.passed:
        st.warning(f"{report.summary()}")
    else:
        st.error(f"{report.summary()}")

    # Show errors first
    errors = report.get_errors()
    if errors:
        with st.expander(f"Errors ({len(errors)})", expanded=True):
            for result in errors:
                st.markdown(f"**[{result.rule_id}] {result.rule_name}**")
                st.markdown(f"_{result.message}_")
                if result.details:
                    with st.container():
                        cols = st.columns(min(len(result.details), 4))
                        for i, (k, v) in enumerate(result.details.items()):
                            with cols[i % len(cols)]:
                                if isinstance(v, float):
                                    st.metric(k.replace("_", " ").title(), f"{v:.2f}")
                                else:
                                    st.metric(k.replace("_", " ").title(), str(v))
                st.markdown("---")

    # Show warnings
    warnings = [r for r in report.results if r.severity == Severity.WARNING and not r.passed]
    if warnings:
        with st.expander(f"Warnings ({len(warnings)})", expanded=False):
            for result in warnings:
                st.markdown(f"**[{result.rule_id}] {result.rule_name}**")
                st.markdown(f"_{result.message}_")
                st.markdown("---")

    # Show info
    info = [r for r in report.results if r.severity == Severity.INFO and not r.passed]
    if info:
        with st.expander(f"Info ({len(info)})", expanded=False):
            for result in info:
                st.markdown(f"**[{result.rule_id}] {result.rule_name}**")
                st.caption(result.message)

    # Optionally show passed checks
    if show_passed:
        passed = [r for r in report.results if r.passed]
        if passed:
            with st.expander(f"Passed ({len(passed)})", expanded=False):
                for result in passed:
                    st.caption(f"[{result.rule_id}] {result.rule_name}")


def render_validation_summary(
    report: "ValidationReport",
) -> tuple[bool, bool]:
    """Render compact validation summary and return status.

    Args:
        report: ValidationReport to summarize

    Returns:
        Tuple of (can_export, has_warnings)
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if report.passed:
            st.metric("Status", "PASS", delta=None)
        else:
            st.metric("Status", "FAIL", delta=None)

    with col2:
        st.metric(
            "Errors",
            report.error_count,
            delta=None if report.error_count == 0 else f"-{report.error_count}",
            delta_color="inverse",
        )

    with col3:
        st.metric("Warnings", report.warning_count)

    with col4:
        st.metric("Checks", f"{report.pass_count}/{len(report.results)}")

    return report.passed, report.has_warnings

