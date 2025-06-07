import time
import math
import multiprocessing
from utils.helpers import compute_control_output

def pid_controller(position, angle, control_signal, Kp=1.0, Ki=0.0, Kd=0.0):
    setpoint = math.pi
    prev_error = 0.0
    integral = 0.0
    dt = 0.01

    while True:
        error = math.pi - angle.value
        #print(f"PID Error: {error:.4f}, Position: {position.value:.4f}, Angle: {angle.value:.4f}")
        integral += error * dt
        derivative = (error - prev_error) / dt
        output = Kp * error + Ki * integral + Kd * derivative
        control_signal.value = output
        prev_error = error
        time.sleep(dt)

def start_pid_controller(shared_vars, Kp, Ki, Kd):
    p = multiprocessing.Process(
        target=pid_controller,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            Kp,
            Ki,
            Kd
        )
    )
    p.start()
    return p