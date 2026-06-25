

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# 👉 CHANGE THIS FOLDER TO ANYWHERE YOU WANT
output_dir = 

# ==============================================================================
# USER INPUT SECTION
# ==============================================================================
# All parameters in this section can be modified by the user.

r_init = [1.0, 0.0]     # Initial position vector [x, y] (normalized units)
v_init = [0.0, 0.75]     # Initial velocity vector [vx, vy] (normalized units)

spacecraft_mass = 1000.0  # Structural dry mass of the spacecraft (kg)
fuel_mass = 500.0         # Initial fuel mass (kg)

thrust_force = 100.0     # Engine thrust force (N)
burn_rate = 2.0           # Fuel consumption rate (kg/s)
throttle = 0.0            # Throttle setting [0.0, 1.0]

dt = 0.01                 # Timestep size (seconds)
num_steps = 3000          # Maximum simulation steps to run
# ==============================================================================

# Simulation Constants
gm = 1.0                  # Gravitational parameter GM (normalized)
r_earth = 0.2             # Earth radius (collision boundary)

def run_orbital_simulation():
    """
    Executes the orbital physics simulation under gravity, prograde thrust,
    and fuel consumption using Euler-Cromer numerical integration.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize states
    r = np.array(r_init, dtype=np.float64)
    v = np.array(v_init, dtype=np.float64)
    
    current_fuel = float(fuel_mass)
    current_mass = spacecraft_mass + current_fuel
    
    # Pre-calculate initial parameters at t=0
    r_mag = np.linalg.norm(r)
    dir_to_earth = -r / r_mag
    a_grav_init = (gm / (r_mag ** 2)) * dir_to_earth
    
    v_mag = np.linalg.norm(v)
    dir_v = v / v_mag if v_mag > 1e-8 else np.zeros(2)
    
    if current_fuel > 0:
        a_thrust_init = ((thrust_force * throttle) / current_mass) * dir_v
    else:
        a_thrust_init = np.array([0.0, 0.0])
        
    init_energy = 0.5 * current_mass * (v_mag**2) - (gm * current_mass) / r_mag
    
    # Lists to store history of physical quantities
    t_hist = [0.0]
    r_hist = [r.copy()]
    v_hist = [v.copy()]
    a_grav_hist = [a_grav_init]
    a_thrust_hist = [a_thrust_init]
    mass_hist = [current_mass]
    fuel_hist = [current_fuel]
    speed_hist = [v_mag]
    altitude_hist = [r_mag - r_earth]
    energy_hist = [init_energy]
    
    collided = False
    
    # Simulation Loop
    for i in range(num_steps):
        r_mag = np.linalg.norm(r)
        
        # Collision Detection: Spacecraft hits Earth's surface
        if r_mag <= r_earth:
            collided = True
            break
            
        # 1. Gravity: a_g = GM / r^2 toward Earth
        dir_to_earth = -r / r_mag
        a_grav_mag = gm / (r_mag ** 2)
        a_grav_vec = a_grav_mag * dir_to_earth
        
        # 2. Propulsion & Fuel Consumption (Newton's Second Law: a_thrust = F_thrust/m)
        if current_fuel > 0:
            # Decrease fuel mass
            fuel_used = burn_rate * throttle * dt
            current_fuel = max(0.0, current_fuel - fuel_used)
            current_mass = spacecraft_mass + current_fuel
            
            # Apply thrust in current velocity direction (prograde burn)
            v_mag = np.linalg.norm(v)
            dir_v = v / v_mag if v_mag > 1e-8 else np.zeros(2)
            
            a_thrust_mag = (thrust_force * throttle) / current_mass
            a_thrust_vec = a_thrust_mag * dir_v
        else:
            # Out of fuel: thrust acceleration drops to zero
            a_thrust_vec = np.array([0.0, 0.0])
            current_mass = spacecraft_mass
            
        # 3. Total Acceleration via vector addition
        a_total = a_grav_vec + a_thrust_vec
        
        # 4. Euler-Cromer Integration
        v = v + a_total * dt
        r = r + v * dt
        
        # Store state
        t_hist.append((i + 1) * dt)
        r_hist.append(r.copy())
        v_hist.append(v.copy())
        a_grav_hist.append(a_grav_vec)
        a_thrust_hist.append(a_thrust_vec)
        mass_hist.append(current_mass)
        fuel_hist.append(current_fuel)
        
        v_mag_new = np.linalg.norm(v)
        speed_hist.append(v_mag_new)
        altitude_hist.append(r_mag - r_earth)
        
        # Mechanical Energy: E = 0.5 * m * v^2 - (GM * m) / r
        energy = 0.5 * current_mass * (v_mag_new**2) - (gm * current_mass) / r_mag
        energy_hist.append(energy)

    # Convert histories to NumPy arrays
    t_arr = np.array(t_hist)
    r_arr = np.array(r_hist)
    v_arr = np.array(v_hist)
    a_grav_arr = np.array(a_grav_hist)
    a_thrust_arr = np.array(a_thrust_hist)
    mass_arr = np.array(mass_hist)
    fuel_arr = np.array(fuel_hist)
    speed_arr = np.array(speed_hist)
    altitude_arr = np.array(altitude_hist)
    energy_arr = np.array(energy_hist)
    
    # ==========================================================================
    # ORBIT CLASSIFICATION
    # ==========================================================================
    # Use specific mechanical energy: epsilon = v^2/2 - GM/r
    final_r_mag = np.linalg.norm(r_arr[-1])
    final_v_mag = np.linalg.norm(v_arr[-1])
    epsilon = 0.5 * (final_v_mag**2) - gm / final_r_mag
    
    if collided:
        classification = "Impact Trajectory"
    elif epsilon >= 0:
        classification = "Escape Trajectory"
    else:
        # Check radius variation to distinguish circular from elliptical
        r_mags = np.linalg.norm(r_arr, axis=1)
        r_min = np.min(r_mags)
        r_max = np.max(r_mags)
        radius_variation = (r_max - r_min) / np.mean(r_mags)
        
        # If radius variation is small, classify as Circular Orbit
        if radius_variation < 0.03:
            classification = "Circular Orbit"
        else:
            classification = "Elliptical Orbit"
            
    # ==========================================================================
    # CONSOLE LOGGING
    # ==========================================================================
    print("=" * 60)
    print("           ORBITAL SIMULATOR v2 TELEMETRY REPORT")
    print("=" * 60)
    print(f"Initial Position:         [{r_arr[0, 0]:.4f}, {r_arr[0, 1]:.4f}] units")
    print(f"Initial Velocity:         [{v_arr[0, 0]:.4f}, {v_arr[0, 1]:.4f}] units/s")
    print(f"Initial Mass:             {mass_arr[0]:.1f} kg")
    print(f"Final Mass:               {mass_arr[-1]:.1f} kg")
    print(f"Initial Fuel:             {fuel_arr[0]:.1f} kg")
    print(f"Remaining Fuel:           {fuel_arr[-1]:.1f} kg")
    print(f"Fuel Consumed:            {fuel_arr[0] - fuel_arr[-1]:.1f} kg")
    print(f"Maximum Altitude:         {np.max(altitude_arr):.4f} units")
    print(f"Minimum Altitude:         {np.min(altitude_arr):.4f} units")
    print(f"Final Speed:              {speed_arr[-1]:.4f} units/s")
    print(f"Final Energy:             {energy_arr[-1]:.4f} units")
    print(f"Orbit Classification:     {classification}")
    print(f"Collision Status:         {'COLLIDED' if collided else 'No Collision'}")
    print(f"Number of Steps:          {len(t_arr) - 1}")
    print("=" * 60)

    # ==========================================================================
    # STATIC VISUALIZATION (orbit_v2.png)
    # ==========================================================================
    print("Generating static trajectory plot...")
    fig_orbit, ax_orbit = plt.subplots(figsize=(8, 8), dpi=100)
    
    # Plot Earth
    earth = plt.Circle((0, 0), r_earth, color='royalblue', alpha=0.8, zorder=2, label='Earth')
    ax_orbit.add_patch(earth)
    ax_orbit.plot(0, 0, 'o', color='white', markersize=3, zorder=3)
    
    # Plot Trajectory
    ax_orbit.plot(r_arr[:, 0], r_arr[:, 1], '-', color='darkorchid', linewidth=2.0, zorder=4, label='Spacecraft Path')
    
    # Mark Start (Green) and End (Red)
    ax_orbit.plot(r_arr[0, 0], r_arr[0, 1], 'o', color='forestgreen', markersize=8, zorder=5, label='Start')
    if collided:
        ax_orbit.plot(r_arr[-1, 0], r_arr[-1, 1], 'X', color='red', markersize=10, zorder=6, label='Impact Point')
    else:
        ax_orbit.plot(r_arr[-1, 0], r_arr[-1, 1], 'o', color='crimson', markersize=8, zorder=5, label='End')
        
    ax_orbit.set_aspect('equal', adjustable='box')
    ax_orbit.grid(True, linestyle=':', alpha=0.6)
    ax_orbit.set_xlabel('X Position (units)', fontsize=11)
    ax_orbit.set_ylabel('Y Position (units)', fontsize=11)
    ax_orbit.set_title(f'Spacecraft Trajectory: {classification}', fontsize=13, fontweight='bold', pad=12)
    ax_orbit.legend(loc='upper right', frameon=True)
    
    # Bounds safety padding
    max_bound = max(np.max(np.abs(r_arr[:, 0])), np.max(np.abs(r_arr[:, 1])))
    limit = max(max_bound * 1.15, 1.2)
    ax_orbit.set_xlim(-limit, limit)
    ax_orbit.set_ylim(-limit, limit)
    
    plt.tight_layout()
    orbit_png_path = os.path.join(output_dir, "orbit_v2.png")
    plt.savefig(orbit_png_path, bbox_inches='tight')
    plt.close(fig_orbit)
    print(f"Saved static plot: {orbit_png_path}")

    # ==========================================================================
    # ANIMATED GIF (orbit_v2.gif)
    # ==========================================================================
    print("Generating animated GIF...")
    fig_anim, ax_anim = plt.subplots(figsize=(8, 8), dpi=100)
    
    # Plot Earth on background
    earth_anim = plt.Circle((0, 0), r_earth, color='royalblue', alpha=0.8, zorder=2)
    ax_anim.add_patch(earth_anim)
    ax_anim.plot(0, 0, 'o', color='white', markersize=3, zorder=3)
    
    # Plot objects to update in animation
    trail_line, = ax_anim.plot([], [], '--', color='darkorchid', linewidth=1.5, zorder=4, label='Path')
    spacecraft_dot, = ax_anim.plot([], [], 'o', color='crimson', markersize=8, zorder=5, label='Spacecraft')
    
    ax_anim.set_aspect('equal', adjustable='box')
    ax_anim.grid(True, linestyle=':', alpha=0.6)
    ax_anim.set_xlabel('X Position (units)', fontsize=11)
    ax_anim.set_ylabel('Y Position (units)', fontsize=11)
    ax_anim.set_title(f'Orbital Animation: {classification}', fontsize=13, fontweight='bold', pad=12)
    ax_anim.legend(loc='upper right', frameon=True)
    ax_anim.set_xlim(-limit, limit)
    ax_anim.set_ylim(-limit, limit)
    plt.tight_layout()
    
    # Downsample animation to around 150 frames for processing speed
    total_len = len(r_arr)
    num_frames = min(150, total_len)
    
    def init():
        trail_line.set_data([], [])
        spacecraft_dot.set_data([], [])
        return trail_line, spacecraft_dot

    def update(frame):
        # Map current frame to the index in the history array
        idx = int(frame * (total_len - 1) / (num_frames - 1))
        
        trail_line.set_data(r_arr[:idx+1, 0], r_arr[:idx+1, 1])
        spacecraft_dot.set_data([r_arr[idx, 0]], [r_arr[idx, 1]])
        
        # If it collided and we've reached the last step, change marker to red 'X'
        if collided and idx == total_len - 1:
            spacecraft_dot.set_marker('X')
            spacecraft_dot.set_color('red')
            spacecraft_dot.set_markersize(10)
        else:
            spacecraft_dot.set_marker('o')
            spacecraft_dot.set_color('crimson')
            spacecraft_dot.set_markersize(8)
            
        return trail_line, spacecraft_dot

    anim = FuncAnimation(fig_anim, update, frames=num_frames, init_func=init, blit=True, interval=50)
    orbit_gif_path = os.path.join(output_dir, "orbit_v2.gif")
    anim.save(orbit_gif_path, writer='pillow', fps=20)
    plt.close(fig_anim)
    print(f"Saved animated GIF: {orbit_gif_path}")

    # ==========================================================================
    # PERFORMANCE PLOTS (Separate PNG files)
    # ==========================================================================
    plots_config = [
        {
            "filename": "fuel_vs_time.png",
            "title": "Spacecraft Remaining Fuel vs. Time",
            "ylabel": "Fuel Mass (kg)",
            "ydata": fuel_arr,
            "color": "tab:orange"
        },
        {
            "filename": "mass_vs_time.png",
            "title": "Spacecraft Total Mass vs. Time",
            "ylabel": "Total Mass (kg)",
            "ydata": mass_arr,
            "color": "tab:blue"
        },
        {
            "filename": "speed_vs_time.png",
            "title": "Spacecraft Speed vs. Time",
            "ylabel": "Speed (units/s)",
            "ydata": speed_arr,
            "color": "tab:red"
        },
        {
            "filename": "altitude_vs_time.png",
            "title": "Spacecraft Altitude vs. Time",
            "ylabel": "Altitude (units)",
            "ydata": altitude_arr,
            "color": "tab:green"
        },
        {
            "filename": "energy_vs_time.png",
            "title": "Spacecraft Total Mechanical Energy vs. Time",
            "ylabel": "Energy (J)",
            "ydata": energy_arr,
            "color": "tab:purple"
        }
    ]

    for p in plots_config:
        print(f"Generating performance plot: {p['title']}...")
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        ax.plot(t_arr, p["ydata"], color=p["color"], linewidth=2.0)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_xlabel("Time (s)", fontsize=11)
        ax.set_ylabel(p["ylabel"], fontsize=11)
        ax.set_title(p["title"], fontsize=13, fontweight='bold', pad=12)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, p["filename"])
        plt.savefig(file_path, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {file_path}")

    print("\nAll orbital simulation outputs successfully written to:")
    print(output_dir)

if __name__ == "__main__":
    run_orbital_simulation()
