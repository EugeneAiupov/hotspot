from __future__ import annotations

import json
from pathlib import Path
import subprocess

from tunnelspot.models import HotspotStatus, validate_band, validate_password, validate_ssid


class HotspotError(RuntimeError):
    pass


class HotspotService:
    def __init__(self, script_path: Path | None = None) -> None:
        if script_path is None:
            script_path = Path(__file__).with_name("powershell_helper.ps1")
        self._script_path = Path(script_path)

    def status(self) -> HotspotStatus:
        payload = self._run("status")
        return HotspotStatus.from_payload(payload)

    def configure(self, ssid: str, password: str, band: str) -> HotspotStatus:
        payload = self._run(
            "configure",
            ssid=validate_ssid(ssid),
            password=validate_password(password),
            band=validate_band(band),
        )
        return HotspotStatus.from_payload(payload)

    def start(self, ssid: str, password: str, band: str) -> HotspotStatus:
        payload = self._run(
            "start",
            ssid=validate_ssid(ssid),
            password=validate_password(password),
            band=validate_band(band),
        )
        return HotspotStatus.from_payload(payload)

    def stop(self) -> HotspotStatus:
        payload = self._run("stop")
        return HotspotStatus.from_payload(payload)

    def _run(self, action: str, **kwargs: str) -> dict[str, object]:
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._script_path),
            "-Action",
            action,
        ]

        if "ssid" in kwargs:
            command.extend(["-Ssid", kwargs["ssid"]])
        if "password" in kwargs:
            command.extend(["-Passphrase", kwargs["password"]])
        if "band" in kwargs:
            command.extend(["-Band", kwargs["band"]])

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        payload: dict[str, object] = {}

        if stdout:
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise HotspotError(f"Не удалось прочитать ответ PowerShell: {stdout}") from exc

        if completed.returncode != 0:
            message = str(payload.get("error") or stderr or "PowerShell command failed.")
            raise HotspotError(self._translate_error(message))

        if not payload:
            raise HotspotError("PowerShell не вернул данные о состоянии хотспота.")

        if not bool(payload.get("ok")):
            message = str(payload.get("error") or "Hotspot operation failed.")
            raise HotspotError(self._translate_error(message))

        return payload

    def _translate_error(self, message: str) -> str:
        if message == "No active internet connection detected for sharing.":
            return "Windows не нашёл активное интернет-подключение для раздачи."

        if message.startswith("Mobile Hotspot is not available for the current connection: "):
            suffix = message.removeprefix(
                "Mobile Hotspot is not available for the current connection: "
            )
            return (
                "Windows сообщает, что Mobile Hotspot недоступен для текущего подключения: "
                f"{suffix}"
            )

        if message.startswith("Wi-Fi adapter does not support band '"):
            band = message.removeprefix("Wi-Fi adapter does not support band '").removesuffix("'.")
            return f"Wi-Fi адаптер не поддерживает диапазон '{band}'."

        if message.startswith("Failed to start hotspot: "):
            suffix = message.removeprefix("Failed to start hotspot: ")
            return f"Не удалось включить хотспот: {suffix}."

        if message.startswith("Failed to stop hotspot: "):
            suffix = message.removeprefix("Failed to stop hotspot: ")
            return f"Не удалось выключить хотспот: {suffix}."

        if message == "PowerShell command failed.":
            return "Команда PowerShell завершилась с ошибкой."

        if message == "Hotspot operation failed.":
            return "Операция хотспота завершилась ошибкой."

        return message
