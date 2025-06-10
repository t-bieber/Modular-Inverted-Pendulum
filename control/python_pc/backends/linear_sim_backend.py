"""
linear_sim_backend.py

This file implements the simulation backend for the modular inverted pendulum project.
It provides a physics loop that models the dynamics of a cart-pendulum system using a linearized state-space model.
The simulation is run in its own process and updates shared variables for position, angle, control signal, and loop execution time.

Credit: The equations and modeling approach used in this file are based on the University of Michigans Control Tutorials for MATLAB and Simulink:
https://ctms.engin.umich.edu/CTMS/?example=InvertedPendulum&section=SystemModeling
"""

import time
import math
import multiprocessing
import numpy as np

# NumPy is used for matrix math to integrate the linear state-space model.
# ``multiprocessing`` allows this simulation to run concurrently with the GUI
# while sharing state via ``Value`` objects.

def simulated_physics_loop(position, angle, control_signal):
    """Physics loop running in a separate process for the linearized model."""
    # System parameters (unchanged)
    m_cart = 0.5
    m_pend = 0.2
    b = 0.1
    l_pend = 0.3
    I_pendulum = 0.006
    g = 9.81
    dt = 0.01
    
    # Linearized state-space model around θ=π (upright position)
    # State vector: [x, x_dot, θ-π, θ_dot]
    
    # Common denominator term
    denom = I_pendulum*(m_cart + m_pend) + m_cart*m_pend*l_pend**2
    
    # State matrix (A)
    A = np.array([
        [0, 1, 0, 0],
        [0, -(I_pendulum + m_pend*l_pend**2)*b/denom, m_pend**2*g*l_pend**2/denom, 0],
        [0, 0, 0, 1],
        [0, -m_pend*l_pend*b/denom, m_pend*g*l_pend*(m_cart + m_pend)/denom, 0]
    ])
    
    # Input matrix (B)
    B = np.array([
        [0],
        [(I_pendulum + m_pend*l_pend**2)/denom],
        [0],
        [m_pend*l_pend/denom]
    ])
    
    # Initial state [x, x_dot, θ-π, θ_dot]
    rand_theta_offset = np.random.uniform(-0.2, 0.2)        # Small random offset for initial angle
    rand_theta_dot_offset = np.random.uniform(-0.1, 0.1)    # Small random offset for initial velocity
    state = np.array([[0.0], [0.0], [0 + rand_theta_offset], [0 + rand_theta_dot_offset]])

    while True:
        start = time.time()
        u = control_signal.value

    # State-space update (Euler discretization)
        state = state + (A @ state + B * u) * dt

        # Convert to absolute angle and wrap to [0, 2π]
        absolute_angle = state[2] + math.pi
        wrapped_angle = absolute_angle % (2 * math.pi)
        
    # Update shared variables that other processes/threads read from
        angle.value = wrapped_angle  # Wrapped angle [0, 2π] (0=down, π=up)
        position.value = state[0][0]

        # Accurate timing
        elapsed = time.time() - start
        remaining_time = dt - elapsed
        if remaining_time > 0:
            time.sleep(remaining_time)

def start_linear_simulation_backend(shared_vars):
    """Spawn the physics loop process and return the ``Process`` object."""
    p = multiprocessing.Process(
        target=simulated_physics_loop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
        )
    )
    p.start()
    # Return the process object so the caller can manage its lifecycle
    return p