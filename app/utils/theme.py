"""Central color palette, typography, and CSS for a consistent, commercial look."""
from __future__ import annotations

import streamlit as st

# ---- Brand palette ----
PRIMARY = "#2563eb"     # blue   - primary series / accents
ACCENT = "#f59e0b"      # amber  - forecast / secondary
GREEN = "#16a34a"       # positive
RED = "#dc2626"         # negative / loss
SLATE = "#475569"
MUTED = "#94a3b8"

# Categorical palette for multi-series charts (colour-blind friendly-ish, one family per hue).
PALETTE = ["#2563eb", "#f59e0b", "#16a34a", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#65a30d"]

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#1e293b"),
    margin=dict(l=10, r=10, t=48, b=10),
    hoverlabel=dict(font_size=12),
    colorway=PALETTE,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)

_CSS = """
<style>
  .block-container { padding-top: 2.2rem; padding-bottom: 2rem; max-width: 1250px; }
  h1, h2, h3 { font-family: 'Inter','Segoe UI',sans-serif; letter-spacing:-0.01em; }
  /* KPI card */
  .kpi-card {
      background: linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);
      border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 18px;
      box-shadow: 0 1px 2px rgba(15,23,42,.04); height: 100%;
  }
  .kpi-label { color:#64748b; font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
  .kpi-value { color:#0f172a; font-size:1.55rem; font-weight:700; margin-top:2px; line-height:1.1; }
  .kpi-delta-pos { color:#16a34a; font-size:.8rem; font-weight:600; }
  .kpi-delta-neg { color:#dc2626; font-size:.8rem; font-weight:600; }
  .kpi-sub { color:#94a3b8; font-size:.74rem; margin-top:2px; }
  /* Insight card */
  .insight-card { border-left:4px solid var(--acc,#2563eb); background:#f8fafc;
      border-radius:8px; padding:12px 16px; margin-bottom:12px; }
  .insight-title { font-weight:700; color:#0f172a; font-size:.98rem; }
  .insight-detail { color:#475569; font-size:.88rem; margin-top:3px; }
  .insight-tag { display:inline-block; font-size:.68rem; font-weight:700; text-transform:uppercase;
      letter-spacing:.05em; color:#fff; background:#2563eb; border-radius:6px; padding:2px 8px; margin-bottom:6px; }
  .hero { background:linear-gradient(120deg,#1e3a8a 0%,#2563eb 55%,#3b82f6 100%); color:#fff;
      border-radius:16px; padding:28px 32px; margin-bottom:8px; }
  .hero h1 { color:#fff; margin:0 0 6px 0; font-size:2.0rem; }
  .hero p { color:#dbeafe; margin:0; font-size:1.02rem; }
  .nav-card { border:1px solid #e2e8f0; border-radius:12px; padding:16px 18px; height:100%;
      background:#fff; transition:border-color .15s; }
  .nav-card:hover { border-color:#2563eb; }
  .nav-card .t { font-weight:700; color:#0f172a; }
  .nav-card .d { color:#64748b; font-size:.85rem; margin-top:4px; }
</style>
"""


def apply_theme() -> None:
    """Inject the global CSS. Call once per page (cheap, idempotent)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def style_fig(fig):
    """Apply the shared Plotly layout to a figure and return it."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig
