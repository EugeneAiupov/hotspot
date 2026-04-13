from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "tunnelspot" / "__init__.py"
VERSION_PATTERN = re.compile(r'__version__ = "(?P<version>\d+\.\d+\.\d+)"')


def read_text() -> str:
    return VERSION_FILE.read_text(encoding="utf-8")


def read_version() -> str:
    match = VERSION_PATTERN.search(read_text())
    if match is None:
        raise RuntimeError(f"Could not find __version__ in {VERSION_FILE}")
    return match.group("version")


def write_version(version: str) -> str:
    current = read_text()
    updated, count = VERSION_PATTERN.subn(f'__version__ = "{version}"', current, count=1)
    if count != 1:
        raise RuntimeError(f"Could not update __version__ in {VERSION_FILE}")
    VERSION_FILE.write_text(updated, encoding="utf-8")
    return version


def bump_version(version: str, part: str) -> str:
    major, minor, patch = [int(item) for item in version.split(".")]
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump part: {part}")


def validate_version(version: str) -> str:
    if VERSION_PATTERN.fullmatch(f'__version__ = "{version}"') is None:
        raise ValueError("Version must follow semantic versioning: MAJOR.MINOR.PATCH")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Show or update TunnelSpot version.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="Print the current version.")

    set_parser = subparsers.add_parser("set", help="Set an explicit version.")
    set_parser.add_argument("version")

    bump_parser = subparsers.add_parser("bump", help="Bump a semantic version part.")
    bump_parser.add_argument("part", choices=("major", "minor", "patch"))

    args = parser.parse_args()

    if args.command == "show":
        print(read_version())
        return 0

    if args.command == "set":
        print(write_version(validate_version(args.version)))
        return 0

    if args.command == "bump":
        next_version = bump_version(read_version(), args.part)
        print(write_version(next_version))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
