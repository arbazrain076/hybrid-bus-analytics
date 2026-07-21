"""Regenerates the report infographics under outputs/report/assets/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from reporting.diagrams import build_all  # noqa: E402


def main() -> None:
    for name in build_all():
        print(name)


if __name__ == "__main__":
    main()
