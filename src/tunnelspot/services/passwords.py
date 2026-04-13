from __future__ import annotations

import keyring


class PasswordStore:
    SERVICE_NAME = "TunnelSpot"
    ENTRY_NAME = "wifi-hotspot-password"

    def get_password(self) -> str | None:
        return keyring.get_password(self.SERVICE_NAME, self.ENTRY_NAME)

    def set_password(self, password: str) -> None:
        keyring.set_password(self.SERVICE_NAME, self.ENTRY_NAME, password)
