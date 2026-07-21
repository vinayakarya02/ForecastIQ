"""Forecasting engine: build series -> engineer features -> fit models -> backtest -> select -> persist.

Modules:
    data          build monthly/quarterly series for total/category/region/market/product
    features      trend, seasonality, lag and rolling/moving-average features
    models        Naive, MovingAverage, LinearRegression, ARIMA, SARIMA (+ optional Prophet)
    evaluator     RMSE / MAE / MAPE / R2 and best-model selection
    trainer       rolling-origin backtesting
    predictor     refit the winner, forecast with intervals, persist to the warehouse
    visualizations actual-vs-forecast, residuals, model & forecast comparison

All models share a common ``fit(y)`` / ``forecast(horizon)`` contract, so new models are drop-in.
Orchestrated by ``pipelines/run_forecast.py``.
"""
