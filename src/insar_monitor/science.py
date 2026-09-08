from __future__ import annotations

import math
import random
import statistics
from collections.abc import Iterable

from .analysis import Observation


def phase_to_los_cm(phase_radians: float, wavelength_m: float = 0.055465, sign: int = -1) -> float:
    """Convert unwrapped interferometric phase to LOS displacement in centimetres.

    The default sign convention follows d_LOS = -lambda * phase / (4*pi). A project
    must document whether positive displacement is towards or away from the sensor.
    """
    if wavelength_m <= 0:
        raise ValueError("Radar wavelength must be positive")
    if sign not in {-1, 1}:
        raise ValueError("Sign must be either -1 or 1")
    if not math.isfinite(phase_radians):
        raise ValueError("Phase must be finite")
    return sign * wavelength_m * phase_radians * 100.0 / (4.0 * math.pi)


def coherence_uncertainty_cm(coherence: float, looks: float = 1.0, wavelength_m: float = 0.055465) -> float:
    """Estimate one-sigma LOS uncertainty from coherence under a simple phase-noise model.

    This is a statistical precision proxy, not total geophysical uncertainty. It excludes
    atmosphere, orbit, DEM, reference-frame and unwrapping errors.
    """
    if not 0 < coherence <= 1:
        raise ValueError("Coherence must be greater than 0 and at most 1")
    if looks <= 0:
        raise ValueError("Number of looks must be positive")
    phase_sigma = math.sqrt((1.0 - coherence**2) / (2.0 * looks * coherence**2))
    return abs(phase_to_los_cm(phase_sigma, wavelength_m=wavelength_m))


def weighted_mean_displacement(items: Iterable[Observation]) -> float:
    values = list(items)
    if not values:
        raise ValueError("At least one observation is required")
    weights = [item.coherence**2 for item in values]
    return sum(item.los_displacement_cm * weight for item, weight in zip(values, weights)) / sum(weights)


def median_absolute_deviation(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("At least one value is required")
    centre = statistics.median(values)
    return statistics.median(abs(value - centre) for value in values)


def robust_outlier_filter(items: Iterable[Observation], threshold: float = 4.5) -> list[Observation]:
    """Filter displacement outliers using a scaled median absolute deviation rule."""
    values = list(items)
    if threshold <= 0:
        raise ValueError("Outlier threshold must be positive")
    if len(values) < 3:
        return values
    displacement = [item.los_displacement_cm for item in values]
    centre = statistics.median(displacement)
    mad = median_absolute_deviation(displacement)
    if mad == 0:
        return values
    return [item for item in values if abs(0.67448975 * (item.los_displacement_cm - centre) / mad) <= threshold]


def bootstrap_mean_interval(values: Iterable[float], repetitions: int = 1000, seed: int = 42) -> tuple[float, float]:
    """Return a deterministic percentile bootstrap interval for the arithmetic mean."""
    sample = list(values)
    if not sample:
        raise ValueError("At least one value is required")
    if repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions")
    rng = random.Random(seed)
    n = len(sample)
    estimates = sorted(statistics.fmean(sample[rng.randrange(n)] for _ in range(n)) for _ in range(repetitions))
    low = estimates[math.floor(0.025 * (repetitions - 1))]
    high = estimates[math.ceil(0.975 * (repetitions - 1))]
    return low, high


def solve_3x3(matrix: list[list[float]], vector: list[float]) -> tuple[float, float, float]:
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Reference points do not constrain a planar ramp")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[column])]
    return augmented[0][3], augmented[1][3], augmented[2][3]


def estimate_planar_ramp(reference_items: Iterable[Observation]) -> tuple[float, float, float, float, float]:
    """Fit z = intercept + x_slope*(lon-lon0) + y_slope*(lat-lat0) by weighted least squares."""
    items = list(reference_items)
    if len(items) < 3:
        raise ValueError("At least three reference observations are required")
    lon0 = statistics.fmean(item.longitude for item in items)
    lat0 = statistics.fmean(item.latitude for item in items)
    design = [
        ((1.0, item.longitude - lon0, item.latitude - lat0), item.coherence**2, item.los_displacement_cm)
        for item in items
    ]
    normal = [
        [sum(weight * row[i] * row[j] for row, weight, _ in design) for j in range(3)]
        for i in range(3)
    ]
    rhs = [sum(weight * row[i] * displacement for row, weight, displacement in design) for i in range(3)]
    intercept, x_slope, y_slope = solve_3x3(normal, rhs)
    return intercept, x_slope, y_slope, lon0, lat0


def remove_planar_ramp(items: Iterable[Observation], model: tuple[float, float, float, float, float]) -> list[Observation]:
    intercept, x_slope, y_slope, lon0, lat0 = model
    return [
        Observation(
            longitude=item.longitude,
            latitude=item.latitude,
            los_displacement_cm=item.los_displacement_cm - intercept - x_slope * (item.longitude - lon0) - y_slope * (item.latitude - lat0),
            coherence=item.coherence,
            distance_to_fault_km=item.distance_to_fault_km,
        )
        for item in items
    ]
