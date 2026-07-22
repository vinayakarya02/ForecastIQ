"""Cached data-access layer.

Thin wrappers that call the existing ``forecastiq.analytics`` / ``forecastiq.forecasting``
modules against the (optionally filtered) engine and cache the results per scope. No
metric or model logic lives here — it only reuses and caches.
"""
from __future__ import annotations

import warnings

import pandas as pd
import streamlit as st
from sqlalchemy import text

from forecastiq.analytics import insights, kpis, products, regional, returns, segmentation, trends
from forecastiq.forecasting import data as fdata
from forecastiq.forecasting import models as fmodels
from forecastiq.forecasting import predictor

from .scope import FactScope
from .warehouse import _config, base_engine, engine_for

# ---------------------------------------------------------------- executive / trends
@st.cache_data(show_spinner=False)
def executive_kpis(scope: FactScope) -> dict:
    return kpis.executive_kpis(engine_for(scope))


@st.cache_data(show_spinner=False)
def monthly_revenue(scope: FactScope) -> pd.DataFrame:
    return trends.monthly_revenue(engine_for(scope))


@st.cache_data(show_spinner=False)
def quarterly_revenue(scope: FactScope) -> pd.DataFrame:
    return trends.quarterly_revenue(engine_for(scope))


@st.cache_data(show_spinner=False)
def yearly_revenue(scope: FactScope) -> pd.DataFrame:
    return trends.yearly_revenue(engine_for(scope))


@st.cache_data(show_spinner=False)
def mom_growth(scope: FactScope) -> pd.DataFrame:
    return trends.mom_growth(engine_for(scope))


@st.cache_data(show_spinner=False)
def revenue_trend(scope: FactScope, window: int = 3) -> pd.DataFrame:
    return trends.revenue_trend(engine_for(scope), window)


# ---------------------------------------------------------------- customers
@st.cache_data(show_spinner=False)
def rfm_segments(scope: FactScope) -> pd.DataFrame:
    return segmentation.rfm_segment_summary(engine_for(scope))


@st.cache_data(show_spinner=False)
def customer_lifetime_value(scope: FactScope) -> pd.DataFrame:
    return segmentation.customer_lifetime_value(engine_for(scope))


@st.cache_data(show_spinner=False)
def repeat_customers(scope: FactScope) -> dict:
    return segmentation.repeat_customers(engine_for(scope))


@st.cache_data(show_spinner=False)
def top_customers(scope: FactScope, n: int = 15) -> pd.DataFrame:
    return segmentation.top_customers(engine_for(scope), n)


# ---------------------------------------------------------------- products
@st.cache_data(show_spinner=False)
def category_performance(scope: FactScope) -> pd.DataFrame:
    return products.category_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def subcategory_performance(scope: FactScope) -> pd.DataFrame:
    return products.subcategory_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def top_products(scope: FactScope, n: int = 15) -> pd.DataFrame:
    return products.top_products(engine_for(scope), n)


@st.cache_data(show_spinner=False)
def low_performing_products(scope: FactScope, n: int = 15) -> pd.DataFrame:
    return products.low_performing_products(engine_for(scope), n)


# ---------------------------------------------------------------- regional
@st.cache_data(show_spinner=False)
def market_performance(scope: FactScope) -> pd.DataFrame:
    return regional.market_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def region_performance(scope: FactScope) -> pd.DataFrame:
    return regional.region_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def country_performance(scope: FactScope) -> pd.DataFrame:
    return regional.country_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def state_performance(scope: FactScope) -> pd.DataFrame:
    return regional.state_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def city_performance(scope: FactScope) -> pd.DataFrame:
    return regional.city_performance(engine_for(scope))


@st.cache_data(show_spinner=False)
def region_manager_performance(scope: FactScope) -> pd.DataFrame:
    return regional.region_manager_performance(engine_for(scope))


# ---------------------------------------------------------------- returns
@st.cache_data(show_spinner=False)
def return_rate_by_region(scope: FactScope) -> pd.DataFrame:
    return returns.return_rate_by_region(engine_for(scope))


@st.cache_data(show_spinner=False)
def return_rate_by_category(scope: FactScope) -> pd.DataFrame:
    return returns.return_rate_by_category(engine_for(scope))


@st.cache_data(show_spinner=False)
def return_rate_by_product(scope: FactScope, min_orders: int = 20, n: int = 20) -> pd.DataFrame:
    return returns.return_rate_by_product(engine_for(scope), min_orders, n)


@st.cache_data(show_spinner=False)
def returned_totals(scope: FactScope) -> dict:
    return returns.returned_totals(engine_for(scope))


@st.cache_data(show_spinner=False)
def returns_trend(scope: FactScope) -> pd.DataFrame:
    """Monthly returned revenue and return rate (presentation-only aggregation)."""
    return pd.read_sql(
        text(
            """
            SELECT printf('%04d-%02d-01', d.year, d.month) AS period_start,
                   ROUND(SUM(CASE WHEN f.is_returned = 1 THEN f.sales ELSE 0 END), 2) AS returned_revenue,
                   ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.is_returned = 1 THEN f.order_id END)
                         / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS return_rate_pct
            FROM fact_sales f
            JOIN dim_date d ON f.order_date_key = d.date_key
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month
            """
        ),
        engine_for(scope),
    )


# ---------------------------------------------------------------- insights
@st.cache_data(show_spinner=False)
def business_insights(scope: FactScope) -> pd.DataFrame:
    generated = insights.generate_insights(engine_for(scope))
    return insights.insights_to_frame(generated)


# ---------------------------------------------------------------- forecasting
@st.cache_data(show_spinner=False)
def forecast_levels() -> dict[str, list[str]]:
    """Available keys per forecast level (for the Forecasting page selectors)."""
    e = base_engine()
    return {level: fdata.list_keys(e, level) for level in ("category", "market", "region", "product")}


@st.cache_data(show_spinner=False)
def persisted_model_metrics() -> pd.DataFrame:
    """Model metrics from the most recent persisted forecast run (Model Performance page)."""
    return pd.read_sql(
        text(
            "SELECT series_id, model_name, rmse, mae, mape, r2, is_best FROM model_metrics "
            "WHERE run_id = (SELECT run_id FROM model_metrics ORDER BY created_at DESC LIMIT 1) "
            "ORDER BY series_id, mape"
        ),
        base_engine(),
    )


@st.cache_data(show_spinner=True)
def run_forecast(level: str, key: str | None, horizon: int, granularity: str = "monthly") -> dict:
    """Run the forecasting engine for one series and return a picklable result bundle."""
    cfg = _config()
    fcfg = cfg["forecasting"]
    period = 4 if granularity == "quarterly" else fcfg.get("seasonal_period", 12)
    factories = fmodels.build_model_factories(fcfg["models"], period)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y = fdata.build_series(base_engine(), fcfg["target"], granularity, level, key)
        sf = predictor.forecast_series(
            y, factories, horizon=horizon, n_folds=fcfg["backtest_folds"],
            selection_metric=fcfg["selection_metric"],
            series_id=fdata.series_id(level, key), granularity=granularity)

    fc = sf.forecast
    return {
        "series_id": sf.series_id,
        "best_model": sf.best_model,
        "selection_metric": fcfg["selection_metric"],
        "history": pd.DataFrame({"period_start": y.index, "value": y.to_numpy()}),
        "forecast": pd.DataFrame({"period_start": fc.index, "yhat": fc.yhat,
                                  "yhat_lower": fc.yhat_lower, "yhat_upper": fc.yhat_upper}),
        "metrics": pd.DataFrame([{"model": m, **vals} for m, vals in sf.metrics.items()]),
        "backtest": sf.backtest,
        "failures": sf.failures,
    }
