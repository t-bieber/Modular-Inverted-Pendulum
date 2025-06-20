import struct

import serial

PORT = "COM5"  # Teensy USB port
BAUDRATE = 115200


def send_control_signal(ser, control_value):
    """
    Sends a signed 16-bit control signal to Teensy.
    Format: [0x55][int16 low byte][int16 high byte]
    """
    control_value = int(max(-255, min(255, control_value)))  # Clamp
    packet = struct.pack("<bh", 0x55, control_value)  # 1 byte sync + 2 bytes int16
    ser.write(packet)


def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0)
        print(f"Connected to {PORT} at {BAUDRATE} baud.")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        return

    last_sent_control = None

    try:
        while True:
            try:
                current_control = int(input("Enter control signal (-127 to 128): "))
                if current_control != last_sent_control:
                    print(f"Sending control signal: {current_control}")
                    send_control_signal(
                        ser, current_control
                    )  # send control signal to teensy
                    last_sent_control = current_control
            except Exception:
                # if current control is not a valid integer, send 0 to motor
                send_control_signal(ser, 0)

    except KeyboardInterrupt:
        send_control_signal(ser, 0)
        print("\nStopped.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
