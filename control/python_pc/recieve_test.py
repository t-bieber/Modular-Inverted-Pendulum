import logging
import struct

import serial

from .config import SERIAL_BAUDRATE, SERIAL_PORT

logger = logging.getLogger(__name__)


def find_last_valid_packet(buffer):
    for i in range(len(buffer) - 5, -1, -1):
        if buffer[i] == 0xAA:
            packet = buffer[i + 1 : i + 5]
            if len(packet) == 4:
                x_pos, raw_angle = struct.unpack("<HH", packet)
                return x_pos, raw_angle
    return None


def raw_angle_to_degrees(raw):
    return raw * 360.0 / 1200.0


def main():
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0)
        logger.info("Connected to %s at %d baud.", SERIAL_PORT, SERIAL_BAUDRATE)
    except serial.SerialException as e:
        logger.error("Failed to open serial port: %s", e)
        return

    # Press any key to continue
    input("Press Enter to start receiving data...")

    try:
        while True:
            data = ser.read_all()
            if len(data) >= 5:
                result = find_last_valid_packet(data)
                if result:
                    x, raw_angle = result
                    angle_deg = raw_angle_to_degrees(raw_angle)
                    logger.info("X = %4d  |  Angle = %7.2f°", x, angle_deg)
    except KeyboardInterrupt:
        logger.info("Stopped.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
