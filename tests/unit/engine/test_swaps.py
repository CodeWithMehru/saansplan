from app.engine.swaps import generate_swaps, reduce_fraction


def test_reduction_calculation():
    assert reduce_fraction(100.0, 58.0) == 42.0
    assert reduce_fraction(0.0, 10.0) == 0.0


def test_swaps_ranked_and_limited(members, routine):
    swaps = generate_swaps([100.0] * 24, [150.0] * 24, members, routine)
    assert len(swaps) <= 3
    assert all(s["percent_reduction"] > 0 for s in swaps)
    assert swaps == sorted(swaps, key=lambda s: s["percent_reduction"], reverse=True)
