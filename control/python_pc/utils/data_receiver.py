import serial
import struct
from multiprocessing import Value

# Reads sensor values from a microcontroller over a serial port and stores them
# into shared ``Value`` objects for use by other processes.

def data_reader(shared_s1, shared_s2, run_flag):
    """Continuously read two sensor values from the serial port."""
    ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=0)
    while run_flag.value:
        # Read all bytes currently available and search for the sync byte
        data = ser.read_all()
        for i in range(len(data) - 5, -1, -1):
            if data[i] == 0xAA:
                packet = data[i+1:i+5]
                if len(packet) == 4:
                    s1, s2 = struct.unpack('<HH', packet)
                    shared_s1.value = s1
                    shared_s2.value = s2
                break