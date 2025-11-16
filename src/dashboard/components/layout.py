from contextlib import contextmanager
from typing import Iterator, Optional

import streamlit as st


def page_header(title: str, subtitle: Optional[str] = None) -> None:
    """Render a consistent dashboard page header."""
    st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f"<div class='page-subtitle'>{subtitle}</div>", unsafe_allow_html=True
        )


@contextmanager
def section(
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    *,
    spacing: bool = True,
) -> Iterator[None]:
    """Container wrapper that standardizes section headings."""
    container = st.container()
    with container:
        if title:
            st.markdown(
                f"<div class='section-title'>{title}</div>", unsafe_allow_html=True
            )
        if subtitle:
            st.markdown(
                f"<div class='section-subtitle'>{subtitle}</div>",
                unsafe_allow_html=True,
            )
        yield
        if spacing:
            st.markdown("")


def two_columns_ratio(left_ratio: float = 1, right_ratio: float = 1):
    return st.columns([left_ratio, right_ratio])


def three_columns():
    return st.columns(3)
