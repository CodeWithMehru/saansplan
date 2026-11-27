"""Benchmark script for SaansPlan engine throughput, latency, and static bundle size."""

import gzip
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.engine.cleaner_day import generate_cleaner_day
from app.engine.emissions import calculate_emissions_and_cost
from app.engine.exposure import interpolate_hourly, simulate_exposure
from app.engine.forecast import analyze_forecast
from app.engine.inhaled import inhaled_micrograms, uncertainty_band
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.routine import HomeSetup, Routine


def _bench_interpolation() -> float:
    """Measure elapsed milliseconds for 1000 hourly interpolation passes."""
    start = perf_counter()
    for _ in range(1000):
        interpolate_hourly([100.0 if index % 2 else None for index in range(24)])
    return (perf_counter() - start) * 1000


def _bench_inhaled_dose() -> float:
    """Measure elapsed milliseconds for 1000 inhaled dose calculations."""
    start = perf_counter()
    for _ in range(1000):
        ug = inhaled_micrograms(150.0, 60, "rest", "child")
        uncertainty_band(ug)
    return (perf_counter() - start) * 1000


def _bench_family_plan() -> float:
    """Measure elapsed milliseconds for full 6-member family calculation."""
    family = [
        FamilyMember(name="Parent 1", age_group=AgeGroup.adult, sensitive=False),
        FamilyMember(name="Parent 2", age_group=AgeGroup.adult, sensitive=False),
        FamilyMember(name="Elderly Grandparent", age_group=AgeGroup.elderly, sensitive=True),
        FamilyMember(name="Child 1", age_group=AgeGroup.child, sensitive=True),
        FamilyMember(name="Child 2", age_group=AgeGroup.child, sensitive=False),
        FamilyMember(name="Child 3", age_group=AgeGroup.child, sensitive=True),
    ]
    pm25_series = [120.0 + (i % 6) * 15 for i in range(24)]
    routine = Routine(
        activities=[],
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=True,
        ),
    )

    start = perf_counter()
    for _ in range(100):
        simulate_exposure(pm25_series, pm25_series, family, routine)
        analyze_forecast(
            pm25_hourly=[120.0] * 120,
            wind_speed_hourly=[1.5] * 120,
            forecast_days=5,
        )
        generate_cleaner_day(
            pm25_hourly=pm25_series,
            aqi_hourly=pm25_series,
            members=family,
            routine=routine,
        )
        calculate_emissions_and_cost(
            commute_mode="car",
            cooking_fuel="lpg",
            heating_fuel="none",
        )
        for member in family:
            ug = inhaled_micrograms(120.0, 60, "light", member.age_group.value)
            uncertainty_band(ug)
    return ((perf_counter() - start) / 100) * 1000


def benchmark_engine() -> None:
    """Benchmark engine performance for interpolation and full 6-member family calculation."""
    print(f"interpolation_1000_runs_ms={_bench_interpolation():.2f}")
    print(f"inhaled_dose_1000_runs_ms={_bench_inhaled_dose():.2f}")
    print(f"full_6member_plan_calc_ms={_bench_family_plan():.2f}")


GZIP_BUDGET_KB = 60.0


def benchmark_bundle() -> None:
    """Measure total static assets size uncompressed and gzipped against the 60 KB budget."""
    static_dir = Path("app/static")
    files = (
        list(static_dir.rglob("*.html"))
        + list(static_dir.rglob("*.css"))
        + list(static_dir.rglob("*.js"))
    )
    # Exclude test files
    files = [f for f in files if "tests" not in f.parts]

    raw_bytes = 0
    gzip_bytes = 0

    for f in files:
        content = f.read_bytes()
        raw_bytes += len(content)
        gzip_bytes += len(gzip.compress(content))

    raw_kb = raw_bytes / 1024
    gzip_kb = gzip_bytes / 1024

    print(f"static_bundle_raw_kb={raw_kb:.2f}")
    print(f"static_bundle_gzipped_kb={gzip_kb:.2f}")
    print(f"static_bundle_budget_met={'PASS' if gzip_kb < GZIP_BUDGET_KB else 'FAIL'}")


def main() -> None:
    print("=== SaansPlan Performance Benchmarks ===")
    benchmark_engine()
    print("\n=== Static Bundle Budget (< 60 KB gzipped) ===")
    benchmark_bundle()


if __name__ == "__main__":
    main()
