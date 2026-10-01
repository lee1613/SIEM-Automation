#!/usr/bin/env python3
"""Derive the README status badges (released / in progress / next) from the docs folders.

- released: the highest version that has a result doc in docs/scoreboard_result/v0/,
  with its score from datasets/evaluation/versions.json when that file has a row for it.
- in progress / next: the architecture docs in docs/version_architecture/v0/ newer than
  released, oldest first (the repo's own definition of "in progress": designed or changed
  after its predecessor's full run, with no result doc yet).

    python3 scripts/update_status.py --write   # rewrite the three shield lines in README.md
    python3 scripts/update_status.py --check   # exit 1 if README.md is stale (CI)
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
DOC_RE = re.compile(r"v(\d+(?:\.\d+)*)\.md")
COLORS = {"released": "2ea44f", "progress": "d29922", "next": "6e7781"}


def _versions(folder: Path) -> list[str]:
    """Version names ('v0.4.5') of the docs in a folder, oldest first, compared numerically."""
    found = [(tuple(int(p) for p in m.group(1).split(".")), f"v{m.group(1)}")
             for f in folder.glob("v*.md") if (m := DOC_RE.fullmatch(f.name))]
    return [name for _, name in sorted(found)]


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.removeprefix("v").split("."))


def derive(root: Path = REPO) -> dict:
    results = _versions(root / "docs" / "scoreboard_result" / "v0")
    if not results:
        sys.exit("No result docs under docs/scoreboard_result/v0/.")
    released = results[-1]
    rows = json.loads((root / "datasets" / "evaluation" / "versions.json").read_text(encoding="utf-8"))["versions"]
    row = next((r for r in rows if r["version"] == released), None)
    score = f"{row['correct']}/{row['questions']}" if row else None
    newer = [v for v in _versions(root / "docs" / "version_architecture" / "v0") if _key(v) > _key(released)]
    return {"released": (released, score),
            "in_progress": newer[0] if newer else None,
            "next": newer[1] if len(newer) > 1 else None}


def _badge(label: str, message: str, color: str) -> str:
    return (f"https://img.shields.io/badge/{quote(label, safe='')}-{quote(message, safe='')}"
            f"-{color}?style=for-the-badge")


def shield_lines(status: dict) -> dict[str, str]:
    version, score = status["released"]
    released = f"{version} · {score}" if score else version
    return {
        "released-shield": _badge("released", released, COLORS["released"]),
        "progress-shield": _badge("in progress", status["in_progress"] or "none", COLORS["progress"]),
        "next-shield": _badge("next", status["next"] or "none", COLORS["next"]),
    }


def apply(readme: str, status: dict) -> str:
    for name, url in shield_lines(status).items():
        pattern = re.compile(rf"^\[{re.escape(name)}\]: .*$", re.MULTILINE)
        if not pattern.search(readme):
            sys.exit(f"README.md has no '[{name}]: ...' line to update.")
        readme = pattern.sub(lambda _: f"[{name}]: {url}", readme)
    return readme


def main(argv: list[str] | None = None, root: Path = REPO) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite the shield lines in README.md")
    mode.add_argument("--check", action="store_true", help="Exit 1 if README.md is stale")
    args = parser.parse_args(argv)

    readme_path = root / "README.md"
    current = readme_path.read_text(encoding="utf-8")
    updated = apply(current, derive(root))
    if args.check:
        if updated != current:
            print("README status badges are stale. Run: python3 scripts/update_status.py --write",
                  file=sys.stderr)
            return 1
        print("README status badges are in sync.")
        return 0
    readme_path.write_text(updated, encoding="utf-8", newline="")
    print("Refreshed the README status badges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
