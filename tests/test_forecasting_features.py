"""Tests for feature engineering."""

from forecastiq.forecasting import features


def test_make_supervised_shape_and_columns(synth_series):
    X, target = features.make_supervised(synth_series, lags=(1, 12), roll_windows=(3,), period=12)
    assert list(X.columns) == ["trend", "season_sin", "season_cos", "lag_1", "lag_12", "roll_3"]
    assert len(X) == len(synth_series) - 12  # warmup drops first 12
    assert len(target) == len(X)


def test_feature_row_matches_history(synth_series):
    values = synth_series.to_numpy()
    month = int(synth_series.index[12].month)
    row = features.feature_row(
        values[:12], t=12, period_number=month, lags=(1, 12), roll_windows=(3,), period=12
    )
    # order: trend, sin, cos, lag_1, lag_12, roll_3
    assert row[0] == 12.0
    assert row[3] == values[11]  # lag_1 = previous value
    assert row[4] == values[0]  # lag_12 = value 12 steps back
    assert abs(row[5] - values[9:12].mean()) < 1e-9  # roll_3 = mean of last 3
