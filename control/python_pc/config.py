"""Shared configuration constants for the control application."""

SERIAL_PORT = "COM5"
SERIAL_BAUDRATE = 115200

# Angle limits used by the hardware backend (degrees)
MAX_ANGLE_DEG = 15
# Maximum cart travel range accepted by hardware backend (mm)
MAX_XPOS_MM = 220

__all__ = [
    "SERIAL_PORT",
    "SERIAL_BAUDRATE",
    "MAX_ANGLE_DEG",
    "MAX_XPOS_MM",
]
