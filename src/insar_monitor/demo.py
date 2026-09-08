from __future__ import annotations

import csv
import math
import random
from pathlib import Path


def generate_synthetic_dataset(path: str | Path, seed: int = 42) -> Path:
    """Create a deterministic fault-like LOS field for software demonstration only."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    for row in range(18):
        latitude = 36.95 + row * 0.055
        for column in range(24):
            longitude = 36.05 + column * 0.065
            fault_longitude = 36.86 + (latitude - 37.4) * 0.32
            distance_km = (longitude - fault_longitude) * 88.0
            positive_lobe = 48 * math.exp(-((distance_km - 10) / 24) ** 2)
            negative_lobe = -28 * math.exp(-((distance_km + 15) / 20) ** 2)
            along_strike = 1 + 0.30 * math.cos((latitude - 37.42) * 4.5)
            displacement = (positive_lobe + negative_lobe) * along_strike + rng.gauss(0, 1.1)
            coherence = max(0.28, min(0.94, 0.82 - 0.18 * math.exp(-(distance_km / 10) ** 2) + rng.gauss(0, 0.035)))
            records.append(
                {
                    "longitude": f"{longitude:.5f}",
                    "latitude": f"{latitude:.5f}",
                    "los_displacement_cm": f"{displacement:.3f}",
                    "coherence": f"{coherence:.3f}",
                    "distance_to_fault_km": f"{distance_km:.3f}",
                }
            )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return path

