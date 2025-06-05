import time
from utils.helpers import compute_control_output

def pid_control_loop(shared_s1, shared_s2, run_flag, log_queue, zero_s1=None, zero_s2=None):
    loop_interval = 0.01    # 100 Hz
    while run_flag.value:
        start_time = time.time()

        s1 = shared_s1.value
        s2 = shared_s2.value

        try:
            s1 -= zero_s1.value
        except:
            print("Homing values not found")
        if zero_s1 and zero_s2:
            s1 -= zero_s1.value
            s2 -= zero_s2.value

        output = compute_control_output(s1, s2)

        end_time = time.time()
        duration = end_time - start_time

        log_queue.put((end_time, s1, s2, output, duration))

        sleep_time = loop_interval - duration
        if sleep_time > 0:
            time.sleep(sleep_time)