"""Unit tests for multi-day smog forecast engine."""

from app.engine.forecast import analyze_forecast


def test_forecast_returns_expected_days():
    # 5 days = 120 hours
    pm25 = [50.0 + (i % 24) * 2 for i in range(120)]
    winds = [2.5] * 120
    days = analyze_forecast(pm25, winds, forecast_days=5)

    assert len(days) == 5
    for day in days:
        assert "avg_pm25" in day
        assert "peak_aqi" in day
        assert "indian_category" in day
        assert "worst_window" in day
        assert "best_window" in day
        assert "safest_airing_hour" in day
        assert 11 <= day["safest_airing_hour"] <= 15
        assert day["is_stagnant"] is False


def test_forecast_detects_severe_stagnation():
    # High PM2.5 and very low wind (< 2.0 m/s)
    pm25 = [350.0] * 48
    winds = [1.1] * 48
    days = analyze_forecast(pm25, winds, forecast_days=2)

    assert len(days) == 2
    assert days[0]["is_severe"] is True
    assert days[0]["category_slug"] == "severe"
    assert days[0]["is_stagnant"] is True
    assert days[0]["avg_wind_speed_mps"] == 1.1


def test_forecast_handles_empty_or_partial_data():
    days = analyze_forecast([], None, forecast_days=5)
    assert days == []

    # Partial day (10 hours)
    days_partial = analyze_forecast([80.0] * 10, None, forecast_days=5)
    assert len(days_partial) == 1
    assert days_partial[0]["avg_pm25"] == 80.0

