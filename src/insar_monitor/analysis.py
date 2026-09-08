from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = {
    "longitude",
    "latitude",
    "los_displacement_cm",
    "coherence",
    "distance_to_fault_km",
}


@dataclass(frozen=True)
class Observation:
    longitude: float
    latitude: float
    los_displacement_cm: float
    coherence: float
    distance_to_fault_km: float


def read_observations(path: str | Path) -> list[Observation]:
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        rows = []
        for line_number, row in enumerate(reader, start=2):
            try:
                item = Observation(**{name: float(row[name]) for name in REQUIRED_COLUMNS})
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value on CSV line {line_number}") from exc
            validate_observation(item, line_number)
            rows.append(item)
    if not rows:
        raise ValueError("The input file contains no observations")
    return rows


def validate_observation(item: Observation, line_number: int | None = None) -> None:
    suffix = f" on CSV line {line_number}" if line_number else ""
    values = asdict(item)
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError(f"Non-finite value{suffix}")
    if not -180 <= item.longitude <= 180 or not -90 <= item.latitude <= 90:
        raise ValueError(f"Coordinate outside WGS84 bounds{suffix}")
    if not 0 <= item.coherence <= 1:
        raise ValueError(f"Coherence outside 0-1{suffix}")


def filter_coherence(items: Iterable[Observation], minimum: float) -> list[Observation]:
    if not 0 <= minimum <= 1:
        raise ValueError("Minimum coherence must be between 0 and 1")
    return [item for item in items if item.coherence >= minimum]


def summarise(items: list[Observation], threshold_cm: float, provenance: str) -> dict:
    if not items:
        raise ValueError("No observations remain after filtering")
    values = [item.los_displacement_cm for item in items]
    strongest = max(items, key=lambda item: abs(item.los_displacement_cm))
    above = [value for value in values if abs(value) >= threshold_cm]
    return {
        "provenance": provenance,
        "observation_count": len(items),
        "minimum_los_displacement_cm": round(min(values), 3),
        "maximum_los_displacement_cm": round(max(values), 3),
        "mean_los_displacement_cm": round(statistics.fmean(values), 3),
        "median_los_displacement_cm": round(statistics.median(values), 3),
        "standard_deviation_cm": round(statistics.pstdev(values), 3),
        "mean_coherence": round(statistics.fmean(item.coherence for item in items), 3),
        "alert_threshold_cm": threshold_cm,
        "observations_above_threshold": len(above),
        "fraction_above_threshold": round(len(above) / len(items), 4),
        "strongest_absolute_displacement": {
            "longitude": strongest.longitude,
            "latitude": strongest.latitude,
            "los_displacement_cm": strongest.los_displacement_cm,
        },
    }


def cross_fault_profile(items: list[Observation], bin_width_km: float = 5.0) -> list[dict]:
    if bin_width_km <= 0:
        raise ValueError("Profile bin width must be positive")
    bins: dict[int, list[Observation]] = {}
    for item in items:
        key = math.floor(item.distance_to_fault_km / bin_width_km)
        bins.setdefault(key, []).append(item)
    from .science import bootstrap_mean_interval

    profile = []
    for key in sorted(bins):
        group = bins[key]
        low, high = bootstrap_mean_interval(
            [item.los_displacement_cm for item in group], repetitions=500, seed=42 + key
        )
        profile.append(
            {
                "bin_centre_km": round((key + 0.5) * bin_width_km, 3),
                "mean_los_displacement_cm": round(
                    statistics.fmean(item.los_displacement_cm for item in group), 3
                ),
                "mean_coherence": round(statistics.fmean(item.coherence for item in group), 3),
                "mean_los_95ci_low_cm": round(low, 3),
                "mean_los_95ci_high_cm": round(high, 3),
                "observation_count": len(group),
            }
        )
    return profile


def write_summary(summary: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_profile(profile: list[dict], path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(profile[0]))
        writer.writeheader()
        writer.writerows(profile)
