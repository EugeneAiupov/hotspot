from __future__ import annotations

from pathlib import Path


def load_script_namespace() -> dict[str, object]:
    path = Path(__file__).resolve().parents[1] / "scripts" / "version.py"
    source = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {"__name__": "__test__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), namespace)
    return namespace


def test_bump_version():
    namespace = load_script_namespace()
    bump_version = namespace["bump_version"]

    assert bump_version("0.1.0", "patch") == "0.1.1"
    assert bump_version("0.1.0", "minor") == "0.2.0"
    assert bump_version("0.1.0", "major") == "1.0.0"


def test_validate_version():
    namespace = load_script_namespace()
    validate_version = namespace["validate_version"]

    assert validate_version("1.2.3") == "1.2.3"
