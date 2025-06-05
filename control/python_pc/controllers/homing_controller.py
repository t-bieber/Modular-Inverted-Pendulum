import time
from utils.helpers import initialize_zero_point

def perform_homing(shared_s1, shared_s2, zero_s1, zero_s2):
    print("Running initialization routine...")
    time.sleep(0.5)  # Let sensor stabilize
    initialize_zero_point(shared_s1, shared_s2, zero_s1, zero_s2)
    print(f"Zero point set: s1={zero_s1.value}, s2={zero_s2.value}")