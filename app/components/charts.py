"""Styled Plotly chart builders. Each returns a figure; call ``show`` to render."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.theme import ACCENT, PRIMARY, style_fig


def show(fig) -> None:
    st.plotly_chart(fig, width="stretch")


def line(df: pd.DataFrame, x: str, y, title: str = "", color: str | None = None,
         labels: dict | None = None):
    fig = px.line(df, x=x, y=y, title=title, color=color, labels=labels, markers=False)
    fig.update_traces(line=dict(width=2.4))
    return style_fig(fig)


def bar(df: pd.DataFrame, x: str, y: str, title: str = "", color: str | None = None,
        orientation: str = "v", labels: dict | None = None, text=None):
    fig = px.bar(df, x=x, y=y, title=title, color=color, orientation=orientation,
                 labels=labels, text=text)
    fig.update_traces(marker_line_width=0)
    return style_fig(fig)


def donut(df: pd.DataFrame, names: str, values: str, title: str = ""):
    fig = px.pie(df, names=names, values=values, title=title, hole=0.55)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_fig(fig)


def forecast_chart(history: pd.DataFrame, forecast: pd.DataFrame, title: str = "",
                   value_col: str = "value"):
    """History line + forecast line with a shaded 95% prediction interval."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(forecast["period_start"]), y=forecast["yhat_upper"],
        mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(forecast["period_start"]), y=forecast["yhat_lower"],
        mode="lines", line=dict(width=0), fill="tonexty",
        fillcolor="rgba(245,158,11,0.18)", name="95% interval"))
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(history["period_start"]), y=history[value_col],
        mode="lines", line=dict(color=PRIMARY, width=2.4), name="Actual"))
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(forecast["period_start"]), y=forecast["yhat"],
        mode="lines+markers", line=dict(color=ACCENT, width=2.4, dash="dash"),
        marker=dict(size=5), name="Forecast"))
    fig.update_layout(title=title)
    return style_fig(fig)
