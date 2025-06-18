import time

from utils.helpers import initialize_zero_point

# Simple routine to determine the zero reference for the sensors at startup.


def perform_homing(shared_s1, shared_s2, zero_s1, zero_s2):
    """Calibrate the two sensors and store their zero values."""
    print("Running initialization routine...")
    time.sleep(0.5)  # Let sensor stabilize
    initialize_zero_point(shared_s1, shared_s2, zero_s1, zero_s2)
    print(f"Zero point set: s1={zero_s1.value}, s2={zero_s2.value}")
