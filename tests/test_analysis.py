import csv
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insar_monitor.analysis import filter_coherence, read_observations, summarise
from insar_monitor.demo import generate_synthetic_dataset
from insar_monitor.science import (
    coherence_uncertainty_cm,
    estimate_planar_ramp,
    phase_to_los_cm,
    remove_planar_ramp,
    robust_outlier_filter,
)
from insar_monitor.analysis import Observation


class AnalysisTests(unittest.TestCase):
    def test_demo_is_deterministic_and_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = generate_synthetic_dataset(Path(folder) / "demo.csv")
            items = read_observations(path)
            self.assertEqual(len(items), 432)
            self.assertTrue(all(0 <= item.coherence <= 1 for item in items))
            result = summarise(items, threshold_cm=10, provenance="synthetic")
            self.assertEqual(result["provenance"], "synthetic")
            self.assertGreater(result["maximum_los_displacement_cm"], 20)
            self.assertLess(result["minimum_los_displacement_cm"], -10)

    def test_coherence_filter(self):
        with tempfile.TemporaryDirectory() as folder:
            items = read_observations(generate_synthetic_dataset(Path(folder) / "demo.csv"))
            filtered = filter_coherence(items, 0.8)
            self.assertLess(len(filtered), len(items))
            self.assertTrue(all(item.coherence >= 0.8 for item in filtered))

    def test_missing_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["longitude", "latitude"])
                writer.writerow([1, 2])
            with self.assertRaisesRegex(ValueError, "Missing required columns"):
                read_observations(path)

    def test_phase_to_displacement_conversion(self):
        half_cycle = phase_to_los_cm(2 * 3.141592653589793)
        self.assertAlmostEqual(half_cycle, -2.77325, places=4)
        self.assertGreater(coherence_uncertainty_cm(0.5, looks=4), 0)

    def test_planar_ramp_estimation_and_removal(self):
        items = []
        for lon, lat in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1)]:
            items.append(Observation(lon, lat, 2 + 3 * lon - 4 * lat, 0.9, lon))
        model = estimate_planar_ramp(items)
        corrected = remove_planar_ramp(items, model)
        self.assertTrue(all(abs(item.los_displacement_cm) < 1e-9 for item in corrected))

    def test_robust_filter_removes_extreme_outlier(self):
        items = [Observation(0, 0, value, 0.8, 0) for value in [1, 1.1, 0.9, 1.2, 500]]
        self.assertEqual(len(robust_outlier_filter(items)), 4)


if __name__ == "__main__":
    unittest.main()
