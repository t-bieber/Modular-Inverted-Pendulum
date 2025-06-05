def compute_control_output(s1, s2):
    return s1 - s2  # dummy placeholder for PID, LQR etc.

def initialize_zero_point(shared_s1, shared_s2, zero_s1, zero_s2):
    zero_s1.value = shared_s1.value
    zero_s2.value = shared_s2.value