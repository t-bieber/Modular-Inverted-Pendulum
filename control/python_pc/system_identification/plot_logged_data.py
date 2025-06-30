import pandas as pd
import matplotlib.pyplot as plt

def plot_logged_data(csv_file="log_data.csv"):
    df = pd.read_csv(csv_file)

    if not all(col in df.columns for col in ["time", "position", "angle", "control_input"]):
        print("CSV does not contain required columns.")
        return

    df["angle_deg"] = df["angle"] * 180 / 3.14159265

    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axs[0].plot(df["time"], df["position"], label="Position (m)")
    axs[0].set_ylabel("Position (m)")
    axs[0].legend()

    axs[1].plot(df["time"], df["angle_deg"], label="Angle (deg)", color="orange")
    axs[1].set_ylabel("Angle (°)")
    axs[1].legend()

    axs[2].plot(df["time"], df["control_input"], label="Control Input", color="green")
    axs[2].set_ylabel("Motor Input")
    axs[2].set_xlabel("Time (s)")
    axs[2].legend()

    fig.suptitle("Logged Motor and Sensor Data")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_logged_data()