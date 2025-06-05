import csv

def logger_process(log_queue, run_flag, filename="log.csv"):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "sensor1", "sensor2", "control_output", "loop_duration"])
        while run_flag.value or not log_queue.empty():
            try:
                row = log_queue.get(timeout=0.1)
                writer.writerow(row)
            except:
                continue