"""Small engine benchmark script."""

from time import perf_counter

from app.engine.exposure import interpolate_hourly


def main() -> None:
    """Measure interpolation throughput without network dependencies."""
    start = perf_counter()
    for _ in range(1000):
        interpolate_hourly([100.0 if index % 2 else None for index in range(24)])
    elapsed_ms = (perf_counter() - start) * 1000
    print(f"interpolation_1000_runs_ms={elapsed_ms:.2f}")


if __name__ == "__main__":
    main()
