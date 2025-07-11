"""
nonlinear_sim_backend.py

Simulates the full nonlinear dynamics of the cart-pendulum system.
Unlike the linearized model, this version captures behavior at large
angles and swing-up.

This backend runs in its own process and updates shared multiprocessing variables.
"""

import math
import multiprocessing
import time

import numpy as np

# This backend uses the full nonlinear equations of motion. It is a bit more
# computationally expensive than the linear version but allows testing swing-up
# behaviour. The process runs independently and shares state via ``Value``
# instances.


def nonlinear_physics_loop(position, angle, control_signal, sim_vars):
    """
    Nonlinear physics loop for the cart-pendulum system.
    - θ = 0 points straight down
    - θ increases counterclockwise
    - x > 0 means cart moves right
    - θ̇ > 0 means pendulum rotates counterclockwise
    """

    # Physical parameters
    m_cart = sim_vars["cart_mass"]
    m_pend = sim_vars["pendulum_mass"]
    pendulum_length = sim_vars["length"]  # Length to pendulum center of mass
    g = 9.81
    b_cart = sim_vars["friction"]
    b_pend = sim_vars["damping"]

    dt = 0.01  # 10 ms timestep

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
        pendulum_mass_length = m_pend * pendulum_length

        # Cart friction in `temp`
        temp = (
            u + pendulum_mass_length * theta_dot**2 * sin_theta - b_cart * x_dot
        ) / total_mass

        # Add pendulum pivot friction to theta_acc
        theta_acc = (
            g * sin_theta + cos_theta * temp - b_pend * theta_dot / pendulum_mass_length
        ) / (pendulum_length * (4 / 3 - (m_pend * cos_theta**2) / total_mass))

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


def start_nonlinear_simulation_backend(shared_vars, sim_vars):
    """Launch ``nonlinear_physics_loop`` in a new ``Process`` and return it."""
    p = multiprocessing.Process(
        target=nonlinear_physics_loop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            sim_vars,
        ),
    )
    p.start()
    # Caller can terminate or join this process as needed
    return p
