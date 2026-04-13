from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from tunnelspot.config import SettingsStore
from tunnelspot.models import (
    AppSettings,
    HotspotStatus,
    SUPPORTED_BANDS,
    generate_password,
    validate_password,
    validate_ssid,
)
from tunnelspot.services import HotspotService, PasswordStore
from tunnelspot.theme import PALETTE, build_palette, build_stylesheet
from tunnelspot.widgets import ToggleSwitch


BAND_LABELS = {
    "Auto": "Авто",
    "TwoPointFourGigahertz": "2.4 ГГц",
    "FiveGigahertz": "5 ГГц",
}


def color_with_alpha(value: str, alpha: int) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class CallableWorker(QRunnable):
    def __init__(self, func: Callable[[], object]) -> None:
        super().__init__()
        self._func = func
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self._func()
        except Exception as exc:
            self.signals.error.emit(str(exc))
        else:
            self.signals.finished.emit(result)


class BackgroundWidget(QWidget):
    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(PALETTE["bg_top"]))
        gradient.setColorAt(1.0, QColor(PALETTE["bg_bottom"]))
        painter.fillRect(self.rect(), gradient)

        painter.setPen(Qt.NoPen)
        painter.setBrush(color_with_alpha("#ffffff", 96))
        painter.drawEllipse(-80, -20, 380, 300)

        painter.setBrush(color_with_alpha(PALETTE["accent"], 38))
        painter.drawEllipse(self.width() - 260, 50, 320, 320)

        painter.setBrush(color_with_alpha("#5f98ad", 28))
        painter.drawEllipse(self.width() - 460, self.height() - 220, 340, 240)


class InfoBlock(QWidget):
    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 16px; color: #102226;")
        value_label.setWordWrap(True)

        self.value_label = value_label
        layout.addWidget(title_label)
        layout.addWidget(value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings_store = SettingsStore()
        self.password_store = PasswordStore()
        self.hotspot_service = HotspotService()
        self.thread_pool = QThreadPool.globalInstance()
        self._workers: list[CallableWorker] = []
        self._is_busy = False
        self._status_loading = False
        self._suspend_toggle_signal = False

        self.settings = self.settings_store.load()
        saved_password = self.password_store.get_password() or generate_password()

        self.setWindowTitle("TunnelSpot")
        self.resize(980, 680)
        self.setMinimumSize(900, 640)

        root = BackgroundWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(36, 28, 36, 28)

        shell = QFrame()
        shell.setObjectName("card")
        shell_shadow = QGraphicsDropShadowEffect(self)
        shell_shadow.setBlurRadius(42)
        shell_shadow.setOffset(0, 18)
        shell_shadow.setColor(color_with_alpha("#1c2a2c", 30))
        shell.setGraphicsEffect(shell_shadow)
        main_layout.addWidget(shell)

        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(34, 34, 34, 34)
        shell_layout.setSpacing(26)

        hero_layout = QVBoxLayout()
        hero_layout.setSpacing(12)
        hero_layout.addWidget(self._make_label("VPN HOTSPOT", "eyebrow"))
        hero_layout.addWidget(self._make_label("Раздавай VPN с ПК одним движением.", "title"))
        hero_layout.addWidget(
            self._make_label(
                "TunnelSpot включает Wi-Fi точку на Windows, сохраняет пароль в системном "
                "хранилище и использует текущее интернет-подключение, включая активный VPN.",
                "subtitle",
            )
        )
        hero_layout.addSpacing(20)

        self.status_chip = self._make_label("Статус загружается", "statusChip")
        hero_layout.addWidget(self.status_chip, 0, Qt.AlignLeft)

        self.upstream_label = InfoBlock("Внешнее подключение", "Определяется...")
        self.clients_label = InfoBlock("Клиенты", "0 / 0")
        hero_layout.addWidget(self.upstream_label)
        hero_layout.addWidget(self.clients_label)
        hero_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        security_note = self._make_label(
            "Пароль не лежит в открытом виде в файле: он хранится через Windows Credential Manager.",
            "bodyMuted",
        )
        hero_layout.addWidget(security_note)

        panel = QFrame()
        panel.setObjectName("card")
        panel_shadow = QGraphicsDropShadowEffect(self)
        panel_shadow.setBlurRadius(26)
        panel_shadow.setOffset(0, 14)
        panel_shadow.setColor(color_with_alpha("#1c2a2c", 18))
        panel.setGraphicsEffect(panel_shadow)
        panel.setMaximumWidth(420)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(18)

        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(14)
        self.toggle = ToggleSwitch()
        self.toggle.toggled.connect(self._on_toggle_requested)
        toggle_row.addWidget(self.toggle, 0, Qt.AlignLeft | Qt.AlignVCenter)

        self.toggle_caption = QLabel("Хотспот выключен")
        self.toggle_caption.setStyleSheet("font-size: 20px; font-weight: 700;")
        toggle_row.addWidget(self.toggle_caption, 1)
        panel_layout.addLayout(toggle_row)

        body_copy = self._make_label(
            "Минимум настроек: имя сети, пароль и диапазон. Всё остальное Windows возьмёт "
            "из текущего интернет-подключения.",
            "bodyMuted",
        )
        panel_layout.addWidget(body_copy)

        panel_layout.addWidget(self._make_label("Настройки сети", "sectionTitle"))

        fields = QFormLayout()
        fields.setSpacing(12)
        fields.setLabelAlignment(Qt.AlignLeft)

        self.ssid_input = QLineEdit(self.settings.ssid)
        self.ssid_input.setPlaceholderText("Имя Wi-Fi сети")
        fields.addRow("SSID", self.ssid_input)

        password_row = QHBoxLayout()
        password_row.setSpacing(10)
        self.password_input = QLineEdit(saved_password)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Пароль точки доступа")
        password_row.addWidget(self.password_input, 1)

        self.show_password_button = QPushButton("Показать")
        self.show_password_button.clicked.connect(self._toggle_password_visibility)
        password_row.addWidget(self.show_password_button)
        fields.addRow("Пароль", self._wrap_layout(password_row))

        self.band_combo = QComboBox()
        self._set_available_bands(SUPPORTED_BANDS, self.settings.band)
        fields.addRow("Диапазон", self.band_combo)
        panel_layout.addLayout(fields)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.generate_button = QPushButton("Сгенерировать")
        self.generate_button.clicked.connect(self._generate_password)
        action_row.addWidget(self.generate_button)

        self.save_button = QPushButton("Сохранить")
        self.save_button.setObjectName("accentButton")
        self.save_button.clicked.connect(self._save_settings)
        action_row.addWidget(self.save_button)

        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setObjectName("ghostButton")
        self.refresh_button.clicked.connect(self.refresh_status)
        action_row.addWidget(self.refresh_button)
        panel_layout.addLayout(action_row)

        self.message_label = self._make_label("", "bodyMuted")
        self.message_label.hide()
        panel_layout.addWidget(self.message_label)

        note = self._make_label(
            "Для включения используется Mobile Hotspot Windows. Если VPN активен как текущее "
            "подключение, трафик клиентов пойдёт через него.",
            "bodyMuted",
        )
        panel_layout.addWidget(note)
        panel_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        shell_layout.addLayout(hero_layout, 1)
        shell_layout.addWidget(panel, 0)

        self.refresh_status()

    def _make_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setWordWrap(True)
        return label

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        container = QWidget()
        container.setLayout(layout)
        return container

    def _set_available_bands(self, bands: tuple[str, ...], selected: str) -> None:
        selected = selected if selected in bands else bands[0]
        self.band_combo.clear()
        for band in bands:
            self.band_combo.addItem(BAND_LABELS.get(band, band), userData=band)
        self.band_combo.setCurrentIndex(self.band_combo.findData(selected))

    def _toggle_password_visibility(self) -> None:
        hidden = self.password_input.echoMode() == QLineEdit.Password
        self.password_input.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self.show_password_button.setText("Скрыть" if hidden else "Показать")

    def _generate_password(self) -> None:
        self.password_input.setText(generate_password())
        self._show_message("Сгенерирован новый пароль.", danger=False)

    def _save_settings(self) -> None:
        try:
            settings, password = self._collect_inputs()
        except ValueError as exc:
            self._show_message(str(exc), danger=True)
            return

        saved_settings = self.settings_store.save(settings)
        self.password_store.set_password(password)
        self.settings = saved_settings
        self._show_message("Настройки сохранены. Пароль записан в Windows Credential Manager.", danger=False)

    def _collect_inputs(self) -> tuple[AppSettings, str]:
        settings = AppSettings(
            ssid=validate_ssid(self.ssid_input.text()),
            band=str(self.band_combo.currentData()),
        )
        password = validate_password(self.password_input.text())
        return settings, password

    def _set_busy(self, busy: bool, text: str | None = None) -> None:
        self._is_busy = busy
        for widget in (
            self.toggle,
            self.ssid_input,
            self.password_input,
            self.band_combo,
            self.generate_button,
            self.save_button,
            self.refresh_button,
            self.show_password_button,
        ):
            widget.setEnabled(not busy)

        if busy and text:
            self._show_message(text, danger=False)

    def _show_message(self, text: str, danger: bool) -> None:
        self.message_label.setText(text)
        self.message_label.setStyleSheet(
            f"color: {PALETTE['danger'] if danger else PALETTE['accent']}; font-size: 13px;"
        )
        self.message_label.show()

    def _run_worker(
        self,
        action: Callable[[], object],
        on_success: Callable[[object], None],
        *,
        lock_ui: bool,
        busy_text: str | None = None,
        reset_toggle_on_error: bool = False,
    ) -> None:
        if lock_ui and self._is_busy:
            return
        if not lock_ui and (self._status_loading or self._is_busy):
            return

        if lock_ui:
            self._set_busy(True, busy_text)
        else:
            self._status_loading = True

        worker = CallableWorker(action)
        self._workers.append(worker)
        worker.signals.finished.connect(
            lambda result, current=worker: self._handle_worker_success(lock_ui, on_success, result, current)
        )
        worker.signals.error.connect(
            lambda message, current=worker: self._handle_worker_error(
                lock_ui,
                message,
                reset_toggle_on_error,
                current,
            )
        )
        self.thread_pool.start(worker)

    def _handle_worker_success(
        self,
        lock_ui: bool,
        on_success: Callable[[object], None],
        result: object,
        worker: CallableWorker,
    ) -> None:
        self._discard_worker(worker)
        if lock_ui:
            self._set_busy(False)
        else:
            self._status_loading = False
        on_success(result)

    def _handle_worker_error(
        self,
        lock_ui: bool,
        message: str,
        reset_toggle_on_error: bool,
        worker: CallableWorker,
    ) -> None:
        self._discard_worker(worker)
        if lock_ui:
            self._set_busy(False)
        else:
            self._status_loading = False
        self._show_message(message, danger=True)
        if reset_toggle_on_error:
            self._set_toggle_checked(False)

    def _discard_worker(self, worker: CallableWorker) -> None:
        try:
            self._workers.remove(worker)
        except ValueError:
            pass

    def refresh_status(self) -> None:
        self._run_worker(self.hotspot_service.status, self._apply_status, lock_ui=False)

    def _apply_status(self, result: object) -> None:
        if not isinstance(result, HotspotStatus):
            return
        self._update_status_ui(result)

    def _update_status_ui(self, status: HotspotStatus) -> None:
        self._set_toggle_checked(status.is_running)
        self.toggle_caption.setText("Хотспот включён" if status.is_running else "Хотспот выключен")
        self.status_chip.setText(f"{'ON' if status.is_running else 'OFF'} · {status.capability}")
        self.status_chip.setProperty("danger", status.capability != "Enabled")
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)

        self.upstream_label.set_value(status.upstream_profile)
        self.clients_label.set_value(f"{status.client_count} / {status.max_client_count}")

        available_bands = status.supported_bands or SUPPORTED_BANDS
        current_band = str(self.band_combo.currentData() or self.settings.band)
        self._set_available_bands(available_bands, current_band)

    def _set_toggle_checked(self, checked: bool) -> None:
        self._suspend_toggle_signal = True
        self.toggle.setChecked(checked)
        self._suspend_toggle_signal = False

    def _on_toggle_requested(self, checked: bool) -> None:
        if self._suspend_toggle_signal:
            return

        if checked:
            try:
                settings, password = self._collect_inputs()
            except ValueError as exc:
                self._show_message(str(exc), danger=True)
                self._set_toggle_checked(False)
                return

            self._run_worker(
                lambda: self.hotspot_service.start(settings.ssid, password, settings.band),
                self._apply_operation_result,
                lock_ui=True,
                busy_text="Включаю хотспот и применяю настройки...",
                reset_toggle_on_error=True,
            )
        else:
            self._run_worker(
                self.hotspot_service.stop,
                self._apply_operation_result,
                lock_ui=True,
                busy_text="Выключаю хотспот...",
            )

    def _apply_operation_result(self, result: object) -> None:
        if not isinstance(result, HotspotStatus):
            return
        self._update_status_ui(result)
        if result.is_running:
            self._show_message("Хотспот включён.", danger=False)
        else:
            self._show_message("Хотспот выключен.", danger=False)


def configure_fonts(app: QApplication) -> None:
    families = set(QFontDatabase.families())
    family = "Segoe UI Variable Text" if "Segoe UI Variable Text" in families else "Segoe UI"
    app.setFont(QFont(family, 10))


def run() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(build_palette())
    app.setStyleSheet(build_stylesheet())
    configure_fonts(app)

    window = MainWindow()
    window.show()
    return app.exec()
