from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analysis import (
    cross_fault_profile,
    filter_coherence,
    read_observations,
    summarise,
    write_profile,
    write_summary,
)
from .demo import generate_synthetic_dataset
from .render import render_svg
from .science import coherence_uncertainty_cm, robust_outlier_filter, weighted_mean_displacement


def run_analysis(input_path: Path, output_dir: Path, threshold_cm: float, minimum_coherence: float, provenance: str, looks: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = read_observations(input_path)
    coherent = filter_coherence(raw, minimum_coherence)
    observations = robust_outlier_filter(coherent)
    summary = summarise(observations, threshold_cm, provenance)
    summary["input_observation_count"] = len(raw)
    summary["coherence_filtered_count"] = len(coherent)
    summary["robust_outlier_filtered_count"] = len(observations)
    summary["coherence_weighted_mean_cm"] = round(weighted_mean_displacement(observations), 3)
    summary["mean_phase_noise_precision_cm"] = round(
        sum(coherence_uncertainty_cm(item.coherence, looks=looks) for item in observations) / len(observations), 4
    )
    summary["uncertainty_scope"] = "phase-noise precision only; excludes atmosphere, orbit, DEM, reference-frame and unwrapping errors"
    profile = cross_fault_profile(observations)
    write_summary(summary, output_dir / "summary.json")
    write_profile(profile, output_dir / "cross_fault_profile.csv")
    render_svg(observations, output_dir / "deformation_map.svg", "Sentinel-1 DInSAR LOS Deformation Monitoring")
    print(f"Analysed {len(observations)} observations")
    print(f"Maximum LOS displacement: {summary['maximum_los_displacement_cm']} cm")
    print(f"Minimum LOS displacement: {summary['minimum_los_displacement_cm']} cm")
    print(f"Results: {output_dir.resolve()}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Analyse geocoded DInSAR LOS displacement points")
    sub = root.add_subparsers(dest="command", required=True)
    analyse = sub.add_parser("analyse", help="Analyse a CSV point export")
    analyse.add_argument("input", type=Path)
    analyse.add_argument("--output-dir", type=Path, default=Path("output/analysis"))
    analyse.add_argument("--threshold-cm", type=float, default=10.0)
    analyse.add_argument("--minimum-coherence", type=float, default=0.35)
    analyse.add_argument("--provenance", default="user-supplied")
    analyse.add_argument("--looks", type=float, default=1.0, help="Effective independent looks for phase-noise precision")
    demo = sub.add_parser("demo", help="Generate and analyse a synthetic demonstration field")
    demo.add_argument("--output-dir", type=Path, default=Path("output/demo"))
    demo.add_argument("--threshold-cm", type=float, default=10.0)
    demo.add_argument("--minimum-coherence", type=float, default=0.35)
    demo.add_argument("--looks", type=float, default=4.0)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "demo":
            source = generate_synthetic_dataset(args.output_dir / "synthetic_los_displacement.csv")
            run_analysis(source, args.output_dir, args.threshold_cm, args.minimum_coherence, "synthetic", args.looks)
        else:
            run_analysis(args.input, args.output_dir, args.threshold_cm, args.minimum_coherence, args.provenance, args.looks)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
