import serial
import struct
import math
import time
import csv
import sys

SERIAL_PORT = "COM5"         # <- Change this to your Teensy port
SERIAL_BAUDRATE = 115200
DURATION = 10.0              # Seconds to run
FREQ = 0.4                   # Oscillation frequency (Hz)

MIN_AMPLITUDE = 50
MAX_AMPLITUDE = 255
RAMP_DURATION = 10.0         # Time to ramp from MIN to MAX

def raw_angle_to_rad(raw_angle):
    return raw_angle * 2 * math.pi / 1200.0

def send_control_signal(ser, value):
    value = int(max(-255, min(255, value)))
    packet = struct.pack("<bh", 0x55, value)
    ser.write(packet)

def find_last_valid_packet(buffer):
    for i in range(len(buffer) - 5, -1, -1):
        if buffer[i] == 0xAA:
            packet = buffer[i + 1 : i + 5]
            if len(packet) == 4:
                x_pos, raw_angle = struct.unpack("<HH", packet)
                return x_pos, raw_angle
    return None

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0.1)
        print(f"Connected to {SERIAL_PORT} at {SERIAL_BAUDRATE} baud.")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        sys.exit(1)

    start_time = time.time()
    last_control = 0
    log = []

    try:
        while (time.time() - start_time) < DURATION:
            t = time.time() - start_time

            # Amplitude increases from MIN_AMPLITUDE to MAX_AMPLITUDE over RAMP_DURATION
            ramp_fraction = min(t / RAMP_DURATION, 1.0)
            amplitude = MIN_AMPLITUDE + (MAX_AMPLITUDE - MIN_AMPLITUDE) * ramp_fraction

            # Sine wave oscillation
            control = int(amplitude * math.sin(2 * math.pi * FREQ * t))

            if control != last_control:
                send_control_signal(ser, control)
                last_control = control

            data = ser.read_all()
            if data and len(data) >= 5:
                result = find_last_valid_packet(data)
                if result:
                    x, raw_angle = result
                    angle_rad = raw_angle_to_rad(raw_angle)
                    position_mm = ((x - 16220 / 2) / 27) / 1000 # (centered) encoder counts in m (approx)
                    log.append((t, position_mm, angle_rad, control))
                    print(f"{t:.2f}s  x={position_mm:.4f} m  θ={math.degrees(angle_rad):.2f}°  u={control}")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Interrupted.")

    finally:
        send_control_signal(ser, 0)
        ser.close()
        print("Serial closed. Saving log...")

        with open("log_data.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "position", "angle", "control_input"])
            writer.writerows(log)

        print("Log saved to log_data.csv")

if __name__ == "__main__":
    main()