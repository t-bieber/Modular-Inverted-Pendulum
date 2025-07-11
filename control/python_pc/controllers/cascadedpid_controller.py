"""
cascadedpid_controller.py

This file implements a cascaded PID controller.
The outer loop controls the cart's position by outputting a desired pendulum angle.
The inner loop stabilizes the pendulum to this desired angle.

Structure:
- Outer PID: Controls cart position -> outputs target angle.
- Inner PID: Controls pendulum angle -> outputs motor control signal.

The inner loop runs every 10 ms by default.
"""
# Tuning variables exposed to user interface:
# /VARS
# /Outer Kp: float
# /Outer Ki: float
# /Outer Kd: float
# /Inner Kp: float
# /Inner Ki: float
# /Inner Kd: float
# /ENDVARS

import math
import multiprocessing
import time

from utils.settings_manager import SettingsManager

settings = SettingsManager()

MAX_ANGLE_DEG = settings.get_max_angle_deg()
MAX_XPOS_MM = settings.get_max_xpos_mm()


def cascadedpid_controller(
    position,
    angle,
    control_signal,
    execution_time,
    desired_angle,
    controller_active: bool,
    outer_Kp=1.0,
    outer_Ki=0.0,
    outer_Kd=0.0,
    inner_Kp=20.0,
    inner_Ki=0.0,
    inner_Kd=1.0,
):
    """Run a cascaded PID controller in its own loop."""
    dt = 0.01  # 10 ms loop

    # Outer loop (position PID) state
    pos_setpoint = 0.0
    pos_prev_error = 0.0
    pos_integral = 0.0
    desired_angle_offset = 0.0  # Keep last value for use in inner loop

    # Inner loop (angle PID) state
    angle_prev_error = 0.0
    angle_integral = 0.0

    loop_count = 0

    while controller_active:
        loop_start = time.perf_counter()

        # --- Outer PID every 5 loops ---
        if loop_count % 5 == 0:
            pos_error = pos_setpoint - position.value
            pos_integral += pos_error * (dt * 5)
            pos_derivative = (pos_error - pos_prev_error) / (dt * 5)
            desired_angle_offset = (
                outer_Kp * pos_error
                + outer_Ki * pos_integral
                + outer_Kd * pos_derivative
            )
            pos_prev_error = pos_error

        # Convert desired angle offset to radians around vertical (pi)
        scaled_desired_angle = (
            math.pi - desired_angle_offset * math.radians(5.0) / 8000.0
        )

        # Clamp desired angle to [-5°, 5°] from upright
        clamped_desired_angle = max(
            min(scaled_desired_angle, math.pi + math.radians(5)),
            math.pi - math.radians(5),
        )
        desired_angle.value = clamped_desired_angle

        # --- Inner PID ---
        angle_error = clamped_desired_angle - angle.value

        if abs(angle_error) > math.radians(MAX_ANGLE_DEG):
            angle_integral = 0
        else:
            angle_integral += angle_error * dt

        angle_derivative = (angle_error - angle_prev_error) / dt
        output = (
            inner_Kp * angle_error
            + inner_Ki * angle_integral
            + inner_Kd * angle_derivative
        )
        control_signal.value = output
        angle_prev_error = angle_error

        # Loop timing and delay
        elapsed = time.perf_counter() - loop_start
        execution_time.value = elapsed
        time.sleep(max(0, dt - elapsed))

        loop_count += 1

    control_signal.value = 0


def start_cascadedpid_controller(
    shared_vars, outer_Kp, outer_Ki, outer_Kd, inner_Kp, inner_Ki, inner_Kd
):
    shared_vars["controller_active"] = True
    """Helper to spawn ``cascadedpid_controller`` as a separate process."""
    p = multiprocessing.Process(
        target=cascadedpid_controller,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["execution_time"],
            shared_vars["desired_angle"],
            shared_vars["controller_active"],
            outer_Kp,
            outer_Ki,
            outer_Kd,
            inner_Kp,
            inner_Ki,
            inner_Kd,
        ),
    )
    p.start()
    return p  # return handle so caller can terminate/join
