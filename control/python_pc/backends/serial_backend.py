"""Serial communication backend with control signal sending."""

import logging
import math
import multiprocessing
import struct
from math import degrees

import serial

from config import (
    MAX_ANGLE_DEG,
    MAX_XPOS_MM,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
)

logger = logging.getLogger(__name__)


def find_last_valid_packet(buffer):
    for i in range(len(buffer) - 5, -1, -1):
        if buffer[i] == 0xAA:
            packet = buffer[i + 1 : i + 5]
            if len(packet) == 4:
                x_pos, raw_angle = struct.unpack("<HH", packet)
                return x_pos, raw_angle
    return None


def raw_angle_to_rad(raw_angle):
    return raw_angle * 2 * math.pi / 1200.0


def scale_control_output(
    raw_output: float,
    max_input: float = 100.0,
    threshold: int = 10,
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


def send_control_signal(ser, control_value):
    """
    Sends a signed 16-bit control signal to Teensy.
    Format: [0x55][int16 low byte][int16 high byte]
    """
    control_value = int(max(-255, min(255, control_value)))
    packet = struct.pack("<bh", 0x55, control_value)
    ser.write(packet)


def hardwareUpdateLoop(position, angle, control_signal):
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0)
        logger.info("Connected to %s at %d baud.", SERIAL_PORT, SERIAL_BAUDRATE)
    except serial.SerialException as e:
        logger.error("Failed to open serial port: %s", e)
        return

    last_sent_control = None

    try:
        while True:
            data = ser.read_all()
            if data is not None and len(data) >= 5:
                result = find_last_valid_packet(data)
                if result:
                    x, raw_angle = result
                    angle.value = raw_angle_to_rad(raw_angle)
                    position.value = (x - 16220 / 2) / 27  # mm approx

                    # scale controller output to motor range
                    current_control = scale_control_output(control_signal.value)

                    if current_control != last_sent_control:
                        if (
                            abs(degrees(angle.value)) <= 180 + MAX_ANGLE_DEG
                            and abs(degrees(angle.value)) >= 180 - MAX_ANGLE_DEG
                            and abs(position.value) <= MAX_XPOS_MM
                        ):
                            send_control_signal(
                                ser, -current_control
                            )  # negative because of wiring
                        else:
                            # Out of bounds: stop motor
                            send_control_signal(ser, 0)
                            last_sent_control = 0
                        last_sent_control = current_control

    except KeyboardInterrupt:
        logger.info("Stopped.")
    finally:
        send_control_signal(ser, 0)  # stop motor on exit
        ser.close()


def start_serial_backend(shared_vars):
    p = multiprocessing.Process(
        target=hardwareUpdateLoop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
        ),
    )
    p.start()
    return p
