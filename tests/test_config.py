from __future__ import annotations

import json

from tunnelspot.config import SettingsStore
from tunnelspot.models import AppSettings, generate_password, validate_password, validate_ssid


def test_settings_store_roundtrip(tmp_path):
    store = SettingsStore(base_dir=tmp_path)
    saved = store.save(AppSettings(ssid="TunnelSpot-Home", band="FiveGigahertz"))
    loaded = store.load()

    assert saved == loaded
    assert json.loads(store.path.read_text(encoding="utf-8")) == {
        "ssid": "TunnelSpot-Home",
        "band": "FiveGigahertz",
    }


def test_generated_password_is_valid():
    password = generate_password(20)
    assert len(password) == 20
    assert validate_password(password) == password


def test_ssid_validation_rejects_non_ascii():
    try:
        validate_ssid("Точка")
    except ValueError as exc:
        assert "ASCII" in str(exc)
    else:
        raise AssertionError("Non-ASCII SSID should be rejected")
