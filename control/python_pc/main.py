from multiprocessing import Process, Value, Queue
from utils.data_receiver import data_reader
from controllers.pid_controller import pid_control_loop
from controllers.homing_controller import perform_homing
from utils.logger import logger_process
from utils.plotter import plotter_process

if __name__ == '__main__':
    from ctypes import c_int, c_bool
    import time

    shared_s1 = Value(c_int, 0)
    shared_s2 = Value(c_int, 0)
    zero_s1 = Value(c_int, 0)
    zero_s2 = Value(c_int, 0)
    run_flag = Value(c_bool, True)
    log_queue = Queue()
    plot_queue = Queue()

    reader = Process(target=data_reader, args=(shared_s1, shared_s2, run_flag))
    reader.start()

    # Run homing sequence before launching PID
    perform_homing(shared_s1, shared_s2, zero_s1, zero_s2)

    controller = Process(target=pid_control_loop, args=(shared_s1, shared_s2, run_flag, log_queue, zero_s1, zero_s2))
    logger = Process(target=logger_process, args=(log_queue, run_flag))
    plotter = Process(target=plotter_process, args=(log_queue, run_flag))

    controller.start()
    logger.start()
    plotter.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        run_flag.value = False

    reader.join()
    controller.join()
    logger.join()
    plotter.join()