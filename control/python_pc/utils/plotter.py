import matplotlib.pyplot as plt
import matplotlib.animation as animation

def plotter_process(log_queue, run_flag):
    from collections import deque
    import time

    times = deque(maxlen=200)
    sensor1 = deque(maxlen=200)
    sensor2 = deque(maxlen=200)
    output = deque(maxlen=200)
    duration = deque(maxlen=200)

    fig, ax = plt.subplots(2, 1, figsize=(8, 6))
    l1, = ax[0].plot([], [], label='Sensor1')
    l2, = ax[0].plot([], [], label='Sensor2')
    l3, = ax[0].plot([], [], label='Control')
    ax[0].legend()
    ax[0].set_title("Sensor and Control Output")

    l4, = ax[1].plot([], [], label='Loop Duration (s)', color='orange')
    ax[1].axhline(0.01, color='red', linestyle='--', linewidth=1, label='10ms Threshold')
    ax[1].legend()
    ax[1].set_title("Control Loop Timing")

    def update(frame):
        while not log_queue.empty():
            try:
                t, s1, s2, ctrl, dur = log_queue.get_nowait()
                times.append(t - start_time)
                sensor1.append(s1)
                sensor2.append(s2)
                output.append(ctrl)
                duration.append(dur)
            except:
                continue

        l1.set_data(times, sensor1)
        l2.set_data(times, sensor2)
        l3.set_data(times, output)
        l4.set_data(times, duration)

        for axis in ax:
            axis.relim()
            axis.autoscale_view()

        return l1, l2, l3, l4

    global start_time
    start_time = time.time()

    ani = animation.FuncAnimation(fig, update, interval=100)
    plt.tight_layout()
    plt.show()