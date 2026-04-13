from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_path

from tunnelspot.models import AppSettings


class SettingsStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = user_config_path("TunnelSpot", "TunnelSpot")
        self._base_dir = Path(base_dir)
        self._path = self._base_dir / "settings.json"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppSettings:
        if not self._path.exists():
            return AppSettings()

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        settings = AppSettings(
            ssid=str(payload.get("ssid", "TunnelSpot")),
            band=str(payload.get("band", "Auto")),
        )
        return settings.normalized()

    def save(self, settings: AppSettings) -> AppSettings:
        normalized = settings.normalized()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return normalized
