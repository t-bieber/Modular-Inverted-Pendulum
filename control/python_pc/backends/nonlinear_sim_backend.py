"""
nonlinear_sim_backend.py

Simulates the full nonlinear dynamics of the cart-pendulum system.
Unlike the linearized model, this version captures behavior at large angles and swing-up.

This backend runs in its own process and updates shared multiprocessing variables.
"""

import time
import math
import multiprocessing
import numpy as np

def nonlinear_physics_loop(position, angle, control_signal):
    # Physical parameters
    m_cart = 0.5       # kg
    m_pend = 0.2       # kg
    l = 0.3            # m (length to pendulum center of mass)
    g = 9.81           # m/s^2
    b_cart = 0.08       # cart damping (linear friction)
    b_pend = 0.015      # pendulum friction at pivot (angular)

    dt = 0.01  # 10ms loop time

    # Initial state: x, x_dot, theta, theta_dot
    x = 0.0
    x_dot = 0.0
    theta = 0 + np.random.uniform(-0.2, 0.2)  # upright + offset
    theta_dot = 0 + np.random.uniform(-0.1, 0.1)

    while True:
        start_time = time.perf_counter()
        u = control_signal.value  # Motor force

        # === Nonlinear dynamics ===
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)

        total_mass = m_cart + m_pend
        pendulum_mass_length = m_pend * l

        # Cart friction in `temp`
        temp = (u + pendulum_mass_length * theta_dot**2 * sin_theta - b_cart * x_dot) / total_mass

        # Add pendulum pivot friction to theta_acc
        theta_acc = (
            g * sin_theta
            + cos_theta * temp
            - b_pend * theta_dot / pendulum_mass_length
        ) / (
            l * (4/3 - (m_pend * cos_theta**2) / total_mass)
        )

        x_acc = temp - (pendulum_mass_length * theta_acc * cos_theta) / total_mass

        # === Euler integration ===
        x_dot += x_acc * dt
        x += x_dot * dt

        theta_dot += theta_acc * dt
        theta += theta_dot * dt

        # Wrap angle to [0, 2π]
        wrapped_angle = (theta + math.pi) % (2 * math.pi)

        # === Update shared values ===
        position.value = x
        angle.value = wrapped_angle

        # Sleep to maintain real-time simulation
        elapsed = time.perf_counter() - start_time
        time.sleep(max(0, dt - elapsed))


def start_nonlinear_simulation_backend(shared_vars):
    p = multiprocessing.Process(
        target=nonlinear_physics_loop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
        )
    )
    p.start()
    return p
