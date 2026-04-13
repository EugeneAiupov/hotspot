from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = False
        self._offset = 3.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(66, 36)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        checked = bool(checked)
        if self._checked == checked:
            self._offset = self._target_offset(checked)
            self.update()
            return

        self._checked = checked
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(self._target_offset(checked))
        self._animation.start()
        self.toggled.emit(self._checked)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_color = QColor("#1d8d86") if self._checked else QColor("#d4d7d7")
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 18, 18)

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(self._offset, 3, 30, 30))

    def _target_offset(self, checked: bool) -> float:
        return 33.0 if checked else 3.0

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, value: float) -> None:
        self._offset = float(value)
        self.update()

    offset = Property(float, get_offset, set_offset)
