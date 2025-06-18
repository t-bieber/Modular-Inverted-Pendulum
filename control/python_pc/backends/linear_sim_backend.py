"""
linear_sim_backend.py

This file implements the simulation backend for the modular inverted pendulum project.
It provides a physics loop that models the dynamics of a cart-pendulum system using a
linearized state-space model.
The simulation is run in its own process and updates shared variables for position,
angle, control signal, and loop execution time.

Credit: The equations and modeling approach used in this file are based on the
University of Michigans Control Tutorials for MATLAB and Simulink:
https://ctms.engin.umich.edu/CTMS/?example=InvertedPendulum&section=SystemModeling
"""

import math
import multiprocessing
import time

import numpy as np

# NumPy is used for matrix math to integrate the linear state-space model.
# ``multiprocessing`` allows this simulation to run concurrently with the GUI
# while sharing state via ``Value`` objects.


def simulated_physics_loop(position, angle, control_signal, sim_vars):
    """Physics loop running in a separate process for the linearized model."""

    # Physical parameters
    m_cart = sim_vars["cart_mass"]
    m_pend = sim_vars["pendulum_mass"]
    b = sim_vars["friction"]
    l_pend = sim_vars["length"]
    I_pendulum = 0.006
    g = 9.81
    dt = 0.01  # 10 ms timestep

    # Denominator for A and B matrices
    denom = I_pendulum * (m_cart + m_pend) + m_cart * m_pend * l_pend**2

    # State-space matrices (standard CCW-positive, so we flip signs manually in state)
    A = np.array(
        [
            [0, 1, 0, 0],
            [
                0,
                -(I_pendulum + m_pend * l_pend**2) * b / denom,
                m_pend**2 * g * l_pend**2 / denom,
                0,
            ],
            [0, 0, 0, 1],
            [
                0,
                -m_pend * l_pend * b / denom,
                m_pend * g * l_pend * (m_cart + m_pend) / denom,
                0,
            ],
        ]
    )

    B = np.array(
        [
            [0],
            [(I_pendulum + m_pend * l_pend**2) / denom],
            [0],
            [m_pend * l_pend / denom],
        ]
    )

    # Initial state with clockwise-positive convention
    rand_theta_offset = np.random.uniform(-0.2, 0.2)
    rand_theta_dot_offset = np.random.uniform(-0.1, 0.1)
    state = np.array(
        [
            [0.0],  # x
            [0.0],  # x_dot
            [-rand_theta_offset],  # θ - π, CW-positive
            [-rand_theta_dot_offset],  # θ_dot, CW-positive
        ]
    )

    while True:
        start = time.time()

        u = control_signal.value  # Control force

        # Euler integration: x(t+1) = x(t) + (A x + B u) * dt
        state = state + (A @ state + B * u) * dt

        # Convert to absolute angle (CW-positive), θ = -(state[2] + π)
        absolute_angle = -(state[2, 0] + math.pi)
        wrapped_angle = absolute_angle % (2 * math.pi)

        # Update shared variables
        position.value = state[0, 0]
        angle.value = wrapped_angle

        # Real-time sync
        elapsed = time.time() - start
        time.sleep(max(0, dt - elapsed))


def start_linear_simulation_backend(shared_vars, sim_vars):
    """Spawn the physics loop process and return the ``Process`` object."""
    p = multiprocessing.Process(
        target=simulated_physics_loop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            sim_vars,
        ),
    )
    p.start()
    # Return the process object so the caller can manage its lifecycle
    return p
