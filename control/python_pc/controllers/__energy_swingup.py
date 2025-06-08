"""
__energy_swingup.py

Energy based swing-up controller used as a pre-stage before stabilizing
controllers. The controller increases the pendulum's energy until the
angle and angular velocity fall below user defined thresholds.
"""
#/VARS
#/Catch angle: float
#/Catch momentum: float
#/ENDVARS

import time
import math
import multiprocessing


def energy_swingup(angle, control_signal, loop_time,
                   catch_angle=0.1, catch_momentum=0.5):
    """Swing the pendulum up using an energy based approach."""
    m = 0.2   # kg
    l = 0.3   # m
    g = 9.81  # m/s^2
    k = 10.0  # control gain
    dt = 0.01
    prev_angle = angle.value

    while True:
        start = time.perf_counter()
        theta = angle.value - math.pi
        theta_dot = (angle.value - prev_angle) / dt
        prev_angle = angle.value

        # Mechanical energy relative to the upright position
        potential = m * g * l * (1 - math.cos(theta))
        kinetic = 0.5 * m * (l ** 2) * theta_dot ** 2
        energy = potential + kinetic

        # Simple energy shaping law
        u = k * theta_dot * math.cos(theta) * energy
        u = max(min(u, 10.0), -10.0)
        control_signal.value = u

        loop_time.value = time.perf_counter() - start

        if abs(theta) < catch_angle and abs(theta_dot) < catch_momentum:
            control_signal.value = 0.0
            break
        time.sleep(max(0, dt - loop_time.value))


def start_energy_swingup(shared_vars, catch_angle, catch_momentum):
    p = multiprocessing.Process(
        target=energy_swingup,
        args=(
            shared_vars["angle"],
            shared_vars["control_signal"],
            shared_vars["loop_time"],
            catch_angle,
            catch_momentum,
        )
    )
    p.start()
    return p

