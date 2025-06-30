"""
lqr_controller.py

This file implements a Linear Quadratic Regulator (LQR) controller.
It estimates the full system state (position, velocity, angle, angular velocity)
and uses it to compute a control signal with u = -K @ state.

Structure:
- Full state feedback from estimated velocity and angular velocity
- u = -Kx * x - Kx_dot * ẋ - Ktheta * θ - Ktheta_dot * θ̇
"""

# Tuning variables exposed to user interface:
# /VARS
# /Kx: float
# /Kx_dot: float
# /Ktheta: float
# /Ktheta_dot: float
# /ENDVARS

import multiprocessing
import time


def lqr_controller(
    position,
    angle,
    control_signal,
    execution_time,
    Kx=1.0,
    Kx_dot=1.0,
    Ktheta=20.0,
    Ktheta_dot=1.5,
):
    """Run LQR controller loop using finite-difference velocity estimation."""
    dt = 0.01  # 10 ms loop

    prev_pos = position.value
    prev_angle = angle.value

    while True:
        loop_start = time.perf_counter()

        # Current measurements
        x = position.value
        theta = angle.value

        # Estimate derivatives (finite difference)
        x_dot = (x - prev_pos) / dt
        theta_dot = (theta - prev_angle) / dt

        # Save for next iteration
        prev_pos = x
        prev_angle = theta

        # Normalize angle around upright equilibrium at pi
        theta_error = theta - 3.14159265  # target is upright

        # Compute LQR control signal
        u = -(
            Kx * x +
            Kx_dot * x_dot +
            Ktheta * theta_error +
            Ktheta_dot * theta_dot
        )

        control_signal.value = u

        # Execution time for profiling
        elapsed = time.perf_counter() - loop_start
        execution_time.value = elapsed
        time.sleep(max(0, dt - elapsed))


def start_lqr_controller(shared_vars, Kx, Kx_dot, Ktheta, Ktheta_dot):
    """Helper to spawn ``lqr_controller`` as a separate process."""
    p = multiprocessing.Process(
        target=lqr_controller,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["execution_time"],
            # Kx,
            # Kx_dot,
            # Ktheta,
            # Ktheta_dot,
            500,
            320,
            120,
            260,
        ),
    )
    p.start()
    return p
