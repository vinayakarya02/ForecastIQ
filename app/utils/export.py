"""CSV export helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def download_csv(
    df: pd.DataFrame, filename: str, label: str = "Download CSV", key: str | None = None
) -> None:
    """Render a download button for a DataFrame as CSV."""
    st.download_button(
        label=f"⬇️  {label}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
        width="content",
    )
