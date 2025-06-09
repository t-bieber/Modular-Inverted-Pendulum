"""
__energy_swingup.py

Energy based swing-up controller used as a pre-stage before stabilizing
controllers. The controller increases the pendulum's energy while
keeping the cart within ±1m of the centre.  Once the pendulum is within
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


def phase_swingup(position, angle, control_signal, loop_time,
                  catch_angle=0.2, catch_momentum=0.2,
                  max_cart_range=0.5):
    """
    Symmetric phase-based swing-up controller with a kick to initiate motion.
    """
    import time
    import math

    dt = 0.01
    prev_angle = angle.value
    prev_pos = position.value
    stable_count = 0
    stable_steps = 20

    pump_force = 3.62
    kick_force = 5.0
    kick_duration = 0.3
    kick_steps = int(kick_duration / dt)
    step_counter = 0

    while True:
        start = time.perf_counter()

        theta = angle.value - math.pi
        theta_dot = (angle.value - prev_angle) / dt
        prev_angle = angle.value

        x = position.value
        x_dot = (position.value - prev_pos) / dt
        prev_pos = position.value

        u = 0.0

        # === Initial Kick ===
        if step_counter < kick_steps:
            direction = -1 if theta > 0 else 1
            u = direction * kick_force

        else:
            # === Symmetric Pumping based on quadrant ===
            if theta < 0 and theta_dot < 0:
                u = -pump_force
            elif theta > 0 and theta_dot > 0:
                u = pump_force

            # Clamp cart motion within bounds
            if x > max_cart_range:
                u += -20.0 * (x - max_cart_range) - 2.0 * x_dot
            elif x < -max_cart_range:
                u += -20.0 * (x + max_cart_range) - 2.0 * x_dot

        control_signal.value = u
        loop_time.value = time.perf_counter() - start

        # Handoff condition
        if abs(theta) < catch_angle and abs(theta_dot) < catch_momentum:
            stable_count += 1
            if stable_count >= stable_steps:
                control_signal.value = 0.0
                break
        else:
            stable_count = 0

        step_counter += 1
        time.sleep(max(0, dt - loop_time.value))


def start_phase_swingup(shared_vars, catch_angle, catch_momentum):
    p = multiprocessing.Process(
        target=phase_swingup,
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

