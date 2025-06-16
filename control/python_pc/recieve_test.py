import serial
import struct

PORT = 'COM5'  # Teensy USB port
BAUDRATE = 115200

def find_last_valid_packet(buffer):
    for i in range(len(buffer) - 5, -1, -1):
        if buffer[i] == 0xAA:
            packet = buffer[i+1:i+5]
            if len(packet) == 4:
                x_pos, raw_angle = struct.unpack('<HH', packet)
                return x_pos, raw_angle
    return None

def raw_angle_to_degrees(raw):
    return raw * 360.0 / 1200.0

def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0)
        print(f"Connected to {PORT} at {BAUDRATE} baud.")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
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
                    print(f"X = {x:4d}  |  Angle = {angle_deg:7.2f}°")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
