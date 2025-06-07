# backends/sim_backend.py

import time
import math
import multiprocessing

def simulated_physics_loop(position, angle, control_signal, loop_time):
    theta = 0.2  # initial pendulum angle (radians)
    x = 0.0
    dt = 0.01

    while True:
        start = time.time()

        u = control_signal.value

        # Simple model: theta'' = -g*sin(theta) + u
        theta_dot = -9.81 * math.sin(theta) + u
        x_dot = u

        theta += theta_dot * dt
        x += x_dot * dt

        angle.value = theta
        position.value = x
        loop_time.value = (time.time() - start) * 1000

        time.sleep(dt)

def start_simulation_backend(shared_vars):
    p = multiprocessing.Process(
        target=simulated_physics_loop,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["loop_time"]
        )
    )
    p.start()
    return p
