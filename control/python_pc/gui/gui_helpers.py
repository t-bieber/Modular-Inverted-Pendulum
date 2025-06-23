"""Helper widgets and GUI utilities."""

from PyQt5.QtWidgets import QDoubleSpinBox


def create_spinbox(
    minimum: float, maximum: float, step: float, value: float
) -> QDoubleSpinBox:
    """Return a ``QDoubleSpinBox`` configured with the given parameters."""
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setSingleStep(step)
    spin.setDecimals(3)
    spin.setValue(value)
    return spin


__all__ = ["create_spinbox"]
