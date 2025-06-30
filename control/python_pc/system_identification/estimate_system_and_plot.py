import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from control.matlab import lqr

def estimate_system_and_plot(csv_path: str, dt: float):
    df = pd.read_csv(csv_path)

    required = ["position", "angle", "control_input"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Raw signals
    position = df["position"].values
    angle = np.unwrap(df["angle"].values)  # in radians
    u = df["control_input"].values.astype(np.float64)

    # Savitzky-Golay smoothing and differentiation
    window = 21  # Must be odd; adjust based on your sample rate and noise
    poly = 3     # Polynomial order for fitting

    position_smooth = savgol_filter(position, window_length=window, polyorder=poly)
    angle_smooth = savgol_filter(angle, window_length=window, polyorder=poly)

    velocity = savgol_filter(position, window_length=window, polyorder=poly, deriv=1, delta=dt)
    angular_velocity = savgol_filter(angle, window_length=window, polyorder=poly, deriv=1, delta=dt)

    # State-space data
    X_k = np.vstack((position_smooth[:-1], velocity[:-1], angle_smooth[:-1], angular_velocity[:-1]))
    X_kplus1 = np.vstack((position_smooth[1:], velocity[1:], angle_smooth[1:], angular_velocity[1:]))
    U_k = u[:-1].reshape(1, -1)
    XU = np.vstack((X_k, U_k))

    # System identification (least squares)
    AB = X_kplus1 @ np.linalg.pinv(XU)
    A = AB[:, :4]
    B = AB[:, 4:]

    # Predict next state
    X_k_pred = A @ X_k + B @ U_k

    time = df["time"].values[1:] if "time" in df.columns else np.arange(len(position) - 1) * dt
    labels = ["Position", "Velocity", "Angle", "Angular Velocity"]

    # Plot actual vs predicted
    fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    for i in range(4):
        axs[i].plot(time, X_kplus1[i], label="Actual")
        axs[i].plot(time, X_k_pred[i], label="Predicted", linestyle="--")
        axs[i].set_ylabel(labels[i])
        axs[i].legend()
    axs[-1].set_xlabel("Time (s)")
    fig.suptitle("Model Prediction vs Actual State")
    plt.tight_layout()
    plt.show()

    # LQR design
    Q = np.diag([0.1, 0.01, 20, 1])
    R = np.array([[0.1]])

    K, _,  _ = lqr(A, B, Q, R)

    print("Estimated A matrix:")
    print(A)
    print("\nEstimated B matrix:")
    print(B)
    print("\nLQR Gain matrix K:")
    print(K)
    
    np.savetxt("A_matrix.csv", A, delimiter=",", header="Estimated A matrix", comments="")
    np.savetxt("B_matrix.csv", B, delimiter=",", header="Estimated B matrix", comments="")
    np.savetxt("K_matrix.csv", K, delimiter=",", header="LQR Gain matrix K", comments="")

    # Plot eigenvalues of (A - BK)
    eigvals, _ = np.linalg.eig(A - B @ K)
    print("Closed-loop eigenvalues:")
    print(eigvals)

    theta = np.linspace(0, 2 * np.pi, 100)
    circle_x = np.cos(theta)
    circle_y = np.sin(theta)

    plt.figure(figsize=(6, 6))
    plt.plot(circle_x, circle_y, 'k--', label='Unit Circle')
    plt.scatter(eigvals.real, eigvals.imag, color='red', label='Closed-loop Poles')
    plt.axhline(0, color='gray', lw=0.5)
    plt.axvline(0, color='gray', lw=0.5)
    plt.axis('equal')
    plt.grid(True)
    plt.title('Closed-loop Eigenvalues')
    plt.legend()
    plt.show()

    return A, B, K

if __name__ == "__main__":
    estimate_system_and_plot("log_data.csv", dt=0.01)
