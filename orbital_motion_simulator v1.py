import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os


# =========================================================
# 1. PHYSICS ENGINE
# =========================================================
def run_simulation(r_init, v_init, gm=1.0, dt=0.01, num_steps=1000, r_earth=0.2):

    r = np.array(r_init, dtype=np.float64)
    v = np.array(v_init, dtype=np.float64)

    r_history = [r.copy()]
    v_history = [v.copy()]
    t_history = [0.0]

    collided = False

    for i in range(num_steps):

        r_mag = np.linalg.norm(r)

        if r_mag <= r_earth:
            collided = True
            break

        dir_to_earth = -r / r_mag
        a_mag = gm / (r_mag ** 2)
        a = a_mag * dir_to_earth

        v = v + a * dt
        r = r + v * dt

        r_history.append(r.copy())
        v_history.append(v.copy())
        t_history.append((i + 1) * dt)

    return np.array(t_history), np.array(r_history), np.array(v_history), collided


# =========================================================
# 2. SCENARIOS
# =========================================================
def generate_simulations():

    gm = 1.0
    r_earth = 0.2
    dt = 0.01

    scenarios = [
        ([1.0, 0.0], [0.0, 1.0], "Circular Orbit"),
        ([1.0, 0.0], [0.0, 0.65], "Elliptical Orbit"),
        ([1.0, 0.0], [0.0, 1.5], "Escape Trajectory"),
        ([1.0, 0.0], [0.0, 0.15], "Impact Trajectory")
    ]

    histories = []

    for r0, v0, name in scenarios:

        t, r, v, collided = run_simulation(r0, v0, gm, dt, 1500, r_earth)

        histories.append((r, v, collided, name))

        print("\nScenario:", name)
        print("Final Position:", r[-1])
        print("Final Velocity:", v[-1])
        print("Status:", "COLLIDED" if collided else "COMPLETED")

    return histories, r_earth


# =========================================================
# 3. STATIC PLOT (WITH SAVE PATH)
# =========================================================
def plot_static(histories, r_earth, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    axs = axs.ravel()

    for i, (r, v, collided, name) in enumerate(histories):

        ax = axs[i]
        ax.set_title(name)
        ax.set_aspect("equal")

        ax.add_patch(plt.Circle((0, 0), r_earth, color="blue", alpha=0.5))

        x = r[:, 0]
        y = r[:, 1]

        ax.plot(x, y, "purple")
        ax.scatter(x[0], y[0], color="green")
        ax.scatter(x[-1], y[-1], color="red" if not collided else "black")
        
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)

    plt.suptitle("Orbital Simulation - Static Output")
    plt.tight_layout()

    save_path = os.path.join(output_dir, "orbit_static.png")
    plt.savefig(save_path, dpi=300)

    print("\nSaved static image at:", save_path)

    plt.show()


# =========================================================
# 4. GIF ANIMATION (WITH SAVE PATH)
# =========================================================
def create_gif(histories, r_earth, output_dir, filename="orbit.gif"):

    os.makedirs(output_dir, exist_ok=True)

    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    axs = axs.ravel()

    lines = []
    dots = []

    for i, (r, v, collided, name) in enumerate(histories):

        ax = axs[i]
        ax.set_title(name)
        ax.set_aspect("equal")

        ax.add_patch(plt.Circle((0, 0), r_earth, color="blue", alpha=0.5))

        line, = ax.plot([], [], "purple")
        dot, = ax.plot([], [], "ro")

        lines.append(line)
        dots.append(dot)
        
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)

    max_len = max(len(h[0]) for h in histories)

    def update(frame):

        for i, (r, v, collided, name) in enumerate(histories):

            if frame < len(r):
                x = r[:frame, 0]
                y = r[:frame, 1]

                lines[i].set_data(x, y)
                if frame > 0:
                    dots[i].set_data([x[-1]], [y[-1]])
                else:
                    dots[i].set_data([r[0, 0]], [r[0, 1]])

        return lines + dots

    ani = FuncAnimation(fig, update, frames=max_len, interval=20, blit=True)

    gif_path = os.path.join(output_dir, filename)

    ani.save(gif_path, writer="pillow", fps=30)

    print("\nSaved GIF at:", gif_path)

    plt.show()


# =========================================================
# 5. MAIN (CHANGE THIS PATH)
# =========================================================
if __name__ == "__main__":

    # 👉 CHANGE THIS FOLDER TO ANYWHERE YOU WANT
    output_dir = r"C:\Users\aravi\Desktop\OrbitProjectOutputs"

    histories, r_earth = generate_simulations()

    plot_static(histories, r_earth, output_dir)

    create_gif(histories, r_earth, output_dir)