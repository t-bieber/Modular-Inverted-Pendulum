"""
serial_backend.py

Serial communication backend with control signal sending.
"""

import logging
import math
import multiprocessing
import struct
from math import degrees

import serial
from utils.settings_manager import SettingsManager #-> get this passed from main?

# MAX_ANGLE_DEG = settings.get_max_angle_deg()
# MAX_XPOS_MM = settings.get_max_xpos_mm()
# SERIAL_BAUDRATE = settings.get_serial_baudrate()
# SERIAL_PORT = settings.get_serial_port()

logger = logging.getLogger(__name__)


def find_last_valid_packet(buffer) -> tuple[int, int] | None:
    for i in range(len(buffer) - 5, -1, -1):
        if buffer[i] == 0xAA:
            packet = buffer[i + 1 : i + 5]
            if len(packet) == 4:
                x_pos: int
                raw_angle: int
                x_pos, raw_angle = struct.unpack("<HH", packet)
                return x_pos, raw_angle
    return None


def raw_angle_to_rad(raw_angle) -> float:
    return raw_angle * 2 * math.pi / 1200.0


def scale_control_output(
    raw_output: float,
    max_input: float = 100.0,
    threshold: int = 20,
    max_output: int = 255,
) -> int:
    """
    Scale a control signal to motor output range, compensating for static friction.
    """
    if raw_output == 0:
        return 0

    clipped_input = max(-max_input, min(max_input, raw_output))
    norm = clipped_input / max_input
    scaled = int(norm * (max_output - threshold))

    if scaled > 0:
        scaled += threshold
    elif scaled < 0:
        scaled -= threshold

    return scaled


def send_control_signal(ser, control_value) -> None:
    """
    Sends a signed 16-bit control signal to Teensy.
    Format: [0x55][int16 low byte][int16 high byte]
    """
    control_value = int(max(-255, min(255, control_value)))
    packet = struct.pack("<bh", 0x55, control_value)
    ser.write(packet)


def hardwareUpdateLoop(shared_vars, settings) -> None: #TODO: Refactor your hardwareUpdateLoop() so it takes a settings_dict as argument instead of accessing a full SettingsManager inside.
    try:
        ser = serial.Serial(settings["serial_port"], settings["baudrate"], timeout=0)
        logger.info("Connected to %s at %d baud.", settings["serial_port"], settings["baudrate"])
    except serial.SerialException as e:
        logger.error("Failed to open serial port: %s", e)
        return

    last_sent_control = 0

    while True:
        data = ser.read_all()
        if data is not None and len(data) >= 5:
            result: tuple[int, int] | None = find_last_valid_packet(data)
            if result:
                x_position: int # ENCODER COUNT VALUE
                raw_angle: int  # ENCODER COUNT VALUE
                x_position, raw_angle = result

                # convert values from encoder counts to radians, millimeters
                shared_vars["angle"].value = raw_angle_to_rad(raw_angle)
                shared_vars["position"].value = (x_position - 16220 / 2) / 27  # mm approx TODO actual math?! no way

                # scale controller output to motor range
                current_control = scale_control_output(shared_vars["control_signal"])

                if current_control != last_sent_control: #TODO implement limit switches
                    if (
                        abs(degrees(shared_vars["angle"].value)) <= 180 + settings["max_angle_deg"]
                        and abs(degrees(shared_vars["angle"].value)) >= 180 - settings["max_angle_deg"]
                        and abs(shared_vars["position"].value) <= settings["max_xpos_mm"]
                    ):
                        send_control_signal(
                            ser, -current_control
                        )  # negative because of wiring
                    else:
                        # Out of bounds: stop motor
                        send_control_signal(ser, 0)
                        last_sent_control = 0
                    last_sent_control: int = current_control