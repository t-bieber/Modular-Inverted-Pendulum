"""
pid_controller.py

This file implements a simple pid controller that only takes into account the angle of the pendulum.
This will lead to the pendulum running off the track sooner or later, as the position is not considered.
It runs in its own process and updates the shared control signal variable.

Hint: The simulation model can be stabilized sufficiently using Kp = 20.0, Ki = 0.0, Kd = 1.0.
"""
#/VARS
#/Kp: float
#/Ki: float
#/Kd: float
#/ENDVARS

import time
import math
import multiprocessing

def pid_controller(angle, control_signal, loop_time, Kp=1.0, Ki=0.0, Kd=0.0):
    setpoint = math.pi
    prev_error = 0.0
    integral = 0.0
    dt = 0.01

    while True:
        start_time = time.perf_counter()
        error = setpoint - angle.value   # Setpoint is π radians (upright position)
        #print(f"PID Error: {error:.4f}, Position: {position.value:.4f}, Angle: {angle.value:.4f}")
        integral += error * dt
        derivative = (error - prev_error) / dt
        output = Kp * error + Ki * integral + Kd * derivative
        control_signal.value = output  # Update shared control signal variable
        prev_error = error
        elapsed = time.perf_counter() - start_time
        loop_time.value = elapsed     # Update shared loop time variable
        time.sleep(max(0, dt - elapsed))

def start_pid_controller(shared_vars, Kp, Ki, Kd):
    p = multiprocessing.Process(
        target=pid_controller,
        args=(
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["loop_time"],
            Kp,
            Ki,
            Kd
        )
    )
    p.start()
    return p