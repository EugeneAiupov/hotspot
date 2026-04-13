from __future__ import annotations

from dataclasses import asdict, dataclass
import secrets
import string


SUPPORTED_BANDS = ("Auto", "TwoPointFourGigahertz", "FiveGigahertz")
PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*-_=+?"


def is_printable_ascii(value: str) -> bool:
    return all(32 <= ord(char) <= 126 for char in value)


def validate_ssid(value: str) -> str:
    ssid = value.strip()
    if not ssid:
        raise ValueError("Имя сети не может быть пустым.")
    if len(ssid.encode("ascii", "ignore")) != len(ssid) or not is_printable_ascii(ssid):
        raise ValueError("SSID должен содержать только печатные ASCII-символы.")
    if len(ssid.encode("ascii")) > 32:
        raise ValueError("SSID должен быть не длиннее 32 символов.")
    return ssid


def validate_password(value: str) -> str:
    password = value.strip()
    if not password:
        raise ValueError("Пароль не может быть пустым.")
    if not is_printable_ascii(password):
        raise ValueError("Пароль должен содержать только печатные ASCII-символы.")
    if not 8 <= len(password) <= 63:
        raise ValueError("Пароль должен быть длиной от 8 до 63 символов.")
    return password


def validate_band(value: str) -> str:
    if value not in SUPPORTED_BANDS:
        raise ValueError("Выбран неподдерживаемый диапазон Wi-Fi.")
    return value


def generate_password(length: int = 16) -> str:
    if length < 8:
        raise ValueError("Минимальная длина пароля: 8 символов.")
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


@dataclass(slots=True)
class AppSettings:
    ssid: str = "TunnelSpot"
    band: str = "Auto"

    def normalized(self) -> "AppSettings":
        return AppSettings(
            ssid=validate_ssid(self.ssid),
            band=validate_band(self.band),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self.normalized())


@dataclass(slots=True)
class HotspotStatus:
    upstream_profile: str
    capability: str
    state: str
    ssid: str
    band: str
    supported_bands: tuple[str, ...]
    client_count: int
    max_client_count: int
    operation_status: str | None = None
    message: str | None = None

    @property
    def is_running(self) -> bool:
        return self.state.lower() == "on"

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "HotspotStatus":
        return cls(
            upstream_profile=str(payload.get("profile_name") or "Unknown"),
            capability=str(payload.get("capability") or "Unknown"),
            state=str(payload.get("state") or "Unknown"),
            ssid=str(payload.get("ssid") or ""),
            band=str(payload.get("band") or "Auto"),
            supported_bands=tuple(str(item) for item in payload.get("supported_bands", ())),
            client_count=int(payload.get("client_count") or 0),
            max_client_count=int(payload.get("max_client_count") or 0),
            operation_status=(
                str(payload["operation_status"])
                if payload.get("operation_status") is not None
                else None
            ),
            message=str(payload["message"]) if payload.get("message") is not None else None,
        )
