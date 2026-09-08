from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insar_monitor.cli import main

result = main(["demo", "--output-dir", str(ROOT / "output" / "demo")])
if result == 0:
    figure_dir = ROOT / "docs" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "output" / "demo" / "deformation_map.svg", figure_dir / "deformation_map.svg")
raise SystemExit(result)
