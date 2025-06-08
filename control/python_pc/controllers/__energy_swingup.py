"""
__energy_swingup.py

Energy based swing-up controller used as a pre-stage before stabilizing
controllers. The controller increases the pendulum's energy while
keeping the cart within ±1 m of the centre.  Once the pendulum is within
the user defined ``catch_angle`` and ``catch_momentum`` thresholds the
process terminates so that a stabilizing controller can take over.
"""
#/VARS
#/Catch angle: float
#/Catch momentum: float
#/ENDVARS

import time
import math
import multiprocessing


def energy_swingup(position, angle, control_signal, loop_time,
                   catch_angle=0.2, catch_momentum=0.2,
                   pos_limit=1.0):
    """Swing the pendulum up using an energy based approach while keeping the
    cart within ``pos_limit`` meters of the center."""
    m = 0.2   # kg
    l = 0.3   # m
    g = 9.81  # m/s^2
    k = 10.0  # control gain for energy shaping
    k_pos = 20.0  # position correction gain
    dt = 0.01
    prev_angle = angle.value
    prev_pos = position.value
    stable_steps = 20
    stable_count = 0

    while True:
        start = time.perf_counter()
        theta = angle.value - math.pi
        theta_dot = (angle.value - prev_angle) / dt
        prev_angle = angle.value
        x = position.value
        x_dot = (position.value - prev_pos) / dt
        prev_pos = position.value

        # Mechanical energy relative to the upright position
        potential = m * g * l * (1 - math.cos(theta))
        kinetic = 0.5 * m * (l ** 2) * theta_dot ** 2
        energy = potential + kinetic

        # Simple energy shaping law
        u = k * theta_dot * math.cos(theta) * energy
        # Keep cart near the center if it drifts too far
        if x > pos_limit:
            u += -k_pos * (x - pos_limit) - 2.0 * x_dot
        elif x < -pos_limit:
            u += -k_pos * (x + pos_limit) - 2.0 * x_dot
        u = max(min(u, 10.0), -10.0)
        control_signal.value = u

        loop_time.value = time.perf_counter() - start

        if (abs(theta) < catch_angle and
                abs(theta_dot) < catch_momentum and
                abs(x) <= pos_limit):
            stable_count += 1
            if stable_count >= stable_steps:
                control_signal.value = 0.0
                break
        else:
            stable_count = 0
        time.sleep(max(0, dt - loop_time.value))


def start_energy_swingup(shared_vars, catch_angle, catch_momentum):
    p = multiprocessing.Process(
        target=energy_swingup,
        args=(
            shared_vars["position"],
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["loop_time"],
            catch_angle,
            catch_momentum,
        )
    )
    p.start()
    return p

