from app.engine.exposure import interpolate_hourly, simulate_exposure


def test_interpolation_between_known_values():
    values = interpolate_hourly([100.0, None, 300.0])
    assert values[0] == [100.0, 200.0, 300.0]
    assert values[1] == [False, True, False]


def test_missing_all_hours_uses_zero_and_flags():
    values, flags = interpolate_hourly([None, None])
    assert values == [0.0, 0.0]
    assert flags == [True, True]


def test_edge_cases_aqi_zero_and_extreme_pm25(members, routine):
    result = simulate_exposure([0.0] * 24, [0.0] * 24, members, routine)
    assert result["peak_aqi"] == 0
    extreme = simulate_exposure([10000.0] * 24, [500.0] * 24, members, routine)
    assert extreme["total_before"] >= 0
