"""Check local documentation links, registry coverage and release metadata."""

import json
from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from urllib.parse import unquote
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    failures = []
    for path in root.rglob("*.md"):
        if any(p in (".git", "build", "dist", ".venv") for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.strip().split(' "')[0].strip("<>").split("#")[0]
            if not target or re.match(r"[a-zA-Z][\w+.-]*:", target):
                continue
            if not (path.parent / unquote(target)).exists():
                failures.append(f"{path.relative_to(root)}: missing {target}")
    registry = json.loads((root / "speech_eval/metrics.json").read_text(encoding="utf-8"))
    catalog = (root / "docs/METRICS.md").read_text(encoding="utf-8")
    for spec in registry:
        if f"## `{spec['id']}`" not in catalog:
            failures.append(f"Missing metric card: {spec['id']}")
    counts = (len(registry), sum(not m.get("alias_of") for m in registry))
    if counts != (69, 64):
        failures.append(f"Update documented counts: {counts}")
    ET.parse(root / "assets/banner.svg")
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    if config["project"]["name"] != "speechmetrichub":
        failures.append("Distribution name mismatch")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Documentation links, {counts[0]} metric cards, SVG and package metadata passed.")


if __name__ == "__main__":
    main()
