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
    outer_Kp=1.0,
    outer_Ki=0.0,
    outer_Kd=0.0,
    inner_Kp=20.0,
    inner_Ki=0.0,
    inner_Kd=1.0,
):
    """Run a cascaded PID controller in its own loop."""
    # PID state
    dt = 0.01  # 10 ms loop

    # Outer loop (position PID) state
    pos_setpoint = 0.0  # We want the cart centered
    pos_prev_error = 0.0
    pos_integral = 0.0

    # Inner loop (angle PID) state
    angle_prev_error = 0.0
    angle_integral = 0.0

    while True:
        # Each iteration computes the next control action based on the
        # current cart position and pendulum angle.
        loop_start = time.perf_counter()

        # Outer PID: cart position -> desired pendulum offset angle
        pos_error = pos_setpoint - position.value

        # Deadband: do nothing if we're close to center
        # deadband_threshold = 0  # mm
        # if abs(pos_error) < deadband_threshold:
        #     desired_angle_offset = 0.0
        #     pos_integral = 0.0  # Anti-windup: avoid accumulating error in dead zone
        #     pos_derivative = 0.0
        #else:
        pos_integral += pos_error * dt
        pos_derivative = (pos_error - pos_prev_error) / dt
        desired_angle_offset = (
            outer_Kp * pos_error
            + outer_Ki * pos_integral
            + outer_Kd * pos_derivative
            )

        pos_prev_error = pos_error

        scaled_desired_angle = (
            math.pi - desired_angle_offset * math.radians(5.0) / 8000.0
        )
        
        # clamp desired angle to [-5 degrees, 5 degrees] from pi
        clamped_desired_angle = max(
            min(scaled_desired_angle, math.pi + math.radians(5)),
            math.pi - math.radians(5),
        )

        desired_angle.value = clamped_desired_angle

        # Inner PID: pendulum angle -> motor command
        angle_error = clamped_desired_angle - angle.value  # P

        # if out of controllable angle range, don't accumulate error
        if(abs(angle_error) > math.radians(MAX_ANGLE_DEG)):     # I
            angle_integral = 0
        else:
            angle_integral += angle_error * dt
        
        angle_derivative = (angle_error - angle_prev_error) / dt    # D
        output = (
            inner_Kp * angle_error
            + inner_Ki * angle_integral
            + inner_Kd * angle_derivative
        )
        control_signal.value = output
        angle_prev_error = angle_error

        # Loop timing
        elapsed = time.perf_counter() - loop_start
        execution_time.value = elapsed  # expose loop duration to the GUI
        time.sleep(max(0, dt - elapsed))


def start_cascadedpid_controller(
    shared_vars, outer_Kp, outer_Ki, outer_Kd, inner_Kp, inner_Ki, inner_Kd
):
    """Helper to spawn ``cascadedpid_controller`` as a separate process."""
    p = multiprocessing.Process(
        target=cascadedpid_controller,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["execution_time"],
            shared_vars["desired_angle"],
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
