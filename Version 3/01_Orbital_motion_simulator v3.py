"""
orbital_simulator_v3.py
=======================
Version 3: Spacecraft Orbital Maneuver Planning Simulator.
Extends Version 2 to support Keplerian orbital elements, custom thrust directions
(prograde, retrograde, radial-in, radial-out), finite burn event windows,
vector arrows (gravity, velocity, thrust) on animated outputs, and expanded
performance telemetry plotting.

This script is fully self-contained and runnable in a single click.

Units:
  - All kinematics, dynamics, energy, momentum, delta-v, and impulse are
    modeled and reported in normalized units (where GM = 1.0, R_earth = 0.2).
  - Spacecraft mass, fuel, and engine thrust remain in SI units (kg, N).
  - Time is reported in normalized time units.
  
Note on Delta-V calculation:
  - Remaining Delta-V is estimated using the Tsiolkovsky Rocket Equation,
    assuming a constant exhaust velocity: ve = Thrust / burn_rate.
  
Integration: Euler-Cromer method.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ==============================================================================
# USER INPUT SECTION
# ==============================================================================
# Modify only the variables in this section to customize your simulation run.
output_dir = r"C:\OrbitalSimulatorOutputs"

r_init = [1.0, 0.0]        # Initial position vector [x, y] (normalized length units)
v_init = [0.0, 1.0]        # Initial velocity vector [vx, vy] (normalized velocity units)

spacecraft_mass = 1000.0   # Spacecraft dry mass (kg)
fuel_mass = 500.0          # Initial fuel mass (kg)

thrust_force = 1000.0      # Engine maximum thrust force (N)
burn_rate = 2.0            # Fuel burn rate (kg/s)
throttle = 1.0             # Throttle setting [0.0 to 1.0]

burn_direction = "prograde" # Direction: "prograde", "retrograde", "radial_out", "radial_in"

# Finite Burn Event Window (normalized time units)
burn_start_time = 1.0      # Start engine burn at this time
burn_end_time = 4.0        # Shut down engine at this time

dt = 0.01                  # Timestep size (normalized time units)
num_steps = 3000           # Maximum simulation steps to run
# ==============================================================================

# Simulation Constants
gm = 1.0                   # Standard gravitational parameter (normalized GM = 1.0)
r_earth = 0.2              # Radius of Earth (collision boundary)

# ==============================================================================
# ORBIT CLASSIFICATION AND CALCULATIONS
# ==============================================================================
def calculate_orbital_elements(r, v):
    """
    Computes Keplerian orbital elements from state vectors r and v.
    All variables include educational aerospace comments.
    """
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)
    
    # 1. Specific Mechanical Energy (epsilon = v^2/2 - GM/r)
    # Physical meaning: Sum of kinetic and potential energy per unit mass.
    # Units: normalized specific energy units
    # Aerospace relevance: Dictates the size (semi-major axis) and type of conic section.
    epsilon = 0.5 * (v_mag**2) - gm / r_mag

    # 2. Specific Angular Momentum (h = r x v)
    # Physical meaning: Momentum of the orbit per unit mass.
    # Units: normalized angular momentum units
    # Aerospace relevance: Constant of motion; perpendicular to the orbit plane.
    h = r[0] * v[1] - r[1] * v[0]

    # 3. Eccentricity Vector (e_vec = ((v^2 - GM/r)r - (r.v)v) / GM)
    # Physical meaning: Vector pointing from central body toward periapsis.
    # Units: Dimensionless
    # Aerospace relevance: Direction aligns with the line of apsides.
    e_vec = (1.0 / gm) * np.array([v[1] * h, -v[0] * h]) - r / r_mag
    e = np.linalg.norm(e_vec)

    # 4. Semi-major Axis (a = -GM / 2*epsilon)
    # Physical meaning: Average distance of the spacecraft from the orbital foci.
    # Units: normalized length units
    # Aerospace relevance: Governs orbital period and energy.
    if abs(epsilon) > 1e-10:
        a = -gm / (2.0 * epsilon)
    else:
        a = float('inf')

    # 5. Periapsis and Apoapsis radii (rp = h^2 / (GM*(1+e)), ra = a*(1+e))
    # Physical meaning: Minimum and maximum distances from the central body.
    # Units: normalized length units
    # Aerospace relevance: Critical for surface clearance (rp) and apogee maneuvers (ra).
    r_p = (h**2) / (gm * (1.0 + e)) if (1.0 + e) > 0 else 0.0
    
    if e < 1.0:
        r_a = a * (1.0 + e)
    else:
        r_a = float('inf')  # Parabolas and hyperbolas do not have a closed apoapsis

    # 6. Estimated Orbital Period (T = 2*pi*sqrt(a^3 / GM))
    # Physical meaning: Time required for one full revolution.
    # Units: normalized time units
    # Aerospace relevance: Fundamental to orbit synchronization and ground tracking.
    if e < 1.0 and a > 0:
        T_period = 2.0 * np.pi * np.sqrt(a**3 / gm)
    else:
        T_period = float('inf')

    return {
        "energy": epsilon,
        "angular_momentum": h,
        "eccentricity": e,
        "eccentricity_vec": e_vec,
        "semi_major_axis": a,
        "periapsis": r_p,
        "apoapsis": r_a,
        "period": T_period
    }

def classify_orbit(eccentricity, collided):
    """
    Classifies orbit type based on eccentricity magnitude and collision status.
    Refined Thresholds:
      - e < 0.001: Circular
      - 0.001 <= e < 0.999: Elliptical
      - 0.999 <= e <= 1.001: Parabolic
      - e > 1.001: Hyperbolic
    """
    if collided:
        return "Impact Trajectory"
    elif eccentricity < 0.001:
        return "Circular Orbit"
    elif eccentricity < 0.999:
        return "Elliptical Orbit"
    elif eccentricity <= 1.001:
        return "Parabolic Escape"
    else:
        return "Hyperbolic Escape"

# ==============================================================================
# SIMULATION ENGINE
# ==============================================================================
def run_simulation_v3():
    """
    Executes the finite burn orbital mechanics simulation.
    Uses Euler-Cromer integration and tracks propellant mass, thrust vectoring,
    and Keplerian elements throughout.
    """
    r = np.array(r_init, dtype=np.float64)
    v = np.array(v_init, dtype=np.float64)
    
    current_fuel = float(fuel_mass)
    current_mass = spacecraft_mass + current_fuel
    
    # Pre-allocate history tracking lists
    t_hist = [0.0]
    r_hist = [r.copy()]
    v_hist = [v.copy()]
    
    # Calculate t=0 accelerations
    r_mag = np.linalg.norm(r)
    dir_to_earth = -r / r_mag
    a_grav_init = (gm / (r_mag**2)) * dir_to_earth
    
    a_grav_hist = [a_grav_init]
    a_thrust_hist = [np.array([0.0, 0.0])]
    mass_hist = [current_mass]
    fuel_hist = [current_fuel]
    speed_hist = [np.linalg.norm(v)]
    altitude_hist = [r_mag - r_earth]
    
    # Energy and angular momentum
    elements_0 = calculate_orbital_elements(r, v)
    energy_hist = [elements_0["energy"]]
    h_hist = [elements_0["angular_momentum"]]
    live_class_hist = [classify_orbit(elements_0["eccentricity"], False)]
    ecc_hist = [elements_0["eccentricity"]]
    sma_hist = [elements_0["semi_major_axis"]]
    
    # Delta-V and Impulse tracking
    total_delta_v = 0.0
    delta_v_hist = [0.0]
    thrust_acc_mag_hist = [0.0]
    grav_acc_mag_hist = [np.linalg.norm(a_grav_init)]
    impulse_delivered = 0.0
    
    collided = False
    
    for i in range(num_steps):
        t_curr = i * dt
        r_mag = np.linalg.norm(r)
        
        # Check collision with Earth surface
        if r_mag <= r_earth:
            collided = True
            break
            
        # 1. Gravity acceleration
        dir_to_earth = -r / r_mag
        a_grav_mag = gm / (r_mag**2)
        a_grav_vec = a_grav_mag * dir_to_earth
        
        # 2. Burn Event Check and Propulsion Update
        # Spacecraft burns only if t is within [burn_start, burn_end] and fuel remains
        is_burning = (burn_start_time <= t_curr <= burn_end_time) and (current_fuel > 0)
        active_throttle = throttle if is_burning else 0.0
        
        if active_throttle > 0:
            # Propellant mass loss
            fuel_used = burn_rate * active_throttle * dt
            current_fuel = max(0.0, current_fuel - fuel_used)
            current_mass = spacecraft_mass + current_fuel
            
            # Compute burn unit direction vector
            v_mag = np.linalg.norm(v)
            if burn_direction == "prograde":
                dir_thrust = v / v_mag if v_mag > 1e-8 else np.zeros(2)
            elif burn_direction == "retrograde":
                dir_thrust = -v / v_mag if v_mag > 1e-8 else np.zeros(2)
            elif burn_direction == "radial_out":
                dir_thrust = r / r_mag
            elif burn_direction == "radial_in":
                dir_thrust = -r / r_mag
            else:
                dir_thrust = np.zeros(2)
                
            # Newton's Second Law: a_thrust = F_thrust / m
            a_thrust_mag = (thrust_force * active_throttle) / current_mass
            a_thrust_vec = a_thrust_mag * dir_thrust
            
            # Track Delta-V and Impulse
            dv = a_thrust_mag * dt
            total_delta_v += dv
            impulse_delivered += (thrust_force * active_throttle) * dt
        else:
            # Coasting or out of fuel
            a_thrust_mag = 0.0
            a_thrust_vec = np.array([0.0, 0.0])
            current_mass = spacecraft_mass
            
        # 3. Total Acceleration (vector addition)
        a_total = a_grav_vec + a_thrust_vec
        
        # 4. Euler-Cromer Integration
        v = v + a_total * dt
        r = r + v * dt
        
        # Calculate instantaneous elements for live telemetry panel
        el = calculate_orbital_elements(r, v)
        
        # Save step histories
        t_hist.append((i + 1) * dt)
        r_hist.append(r.copy())
        v_hist.append(v.copy())
        a_grav_hist.append(a_grav_vec)
        a_thrust_hist.append(a_thrust_vec)
        mass_hist.append(current_mass)
        fuel_hist.append(current_fuel)
        speed_hist.append(np.linalg.norm(v))
        altitude_hist.append(r_mag - r_earth)
        energy_hist.append(el["energy"])
        h_hist.append(el["angular_momentum"])
        live_class_hist.append(classify_orbit(el["eccentricity"], collided))
        ecc_hist.append(el["eccentricity"])
        sma_hist.append(el["semi_major_axis"])
        delta_v_hist.append(total_delta_v)
        thrust_acc_mag_hist.append(a_thrust_mag)
        grav_acc_mag_hist.append(a_grav_mag)

    # Compile history as dictionary of numpy arrays
    history = {
        "t": np.array(t_hist),
        "r": np.array(r_hist),
        "v": np.array(v_hist),
        "a_grav": np.array(a_grav_hist),
        "a_thrust": np.array(a_thrust_hist),
        "mass": np.array(mass_hist),
        "fuel": np.array(fuel_hist),
        "speed": np.array(speed_hist),
        "altitude": np.array(altitude_hist),
        "energy": np.array(energy_hist),
        "h": np.array(h_hist),
        "live_class": np.array(live_class_hist),
        "ecc": np.array(ecc_hist),
        "sma": np.array(sma_hist),
        "delta_v": np.array(delta_v_hist),
        "thrust_acc_mag": np.array(thrust_acc_mag_hist),
        "grav_acc_mag": np.array(grav_acc_mag_hist),
        "collided": collided,
        "total_delta_v": total_delta_v,
        "impulse": impulse_delivered
    }
    
    return history

# ==============================================================================
# TELEMETRY LOGGING
# ==============================================================================
def print_mission_report(history):
    """
    Computes final orbital elements and outputs a comprehensive telemetry report.
    Reports all elements in normalized units.
    """
    final_r = history["r"][-1]
    final_v = history["v"][-1]
    
    # Calculate final orbital parameters
    el = calculate_orbital_elements(final_r, final_v)
    orbit_type = classify_orbit(el["eccentricity"], history["collided"])
    
    # Calculate remaining Delta-V potential using Tsiolkovsky Rocket Equation:
    # dV_rem = c * ln(m_current / m_dry), where exhaust velocity c = Thrust / m_dot
    # Note: Remaining Delta-V is estimated assuming a constant exhaust velocity.
    if burn_rate > 0 and history["fuel"][-1] > 0:
        exhaust_vel = thrust_force / burn_rate
        remaining_dv = exhaust_vel * np.log(history["mass"][-1] / spacecraft_mass)
    else:
        remaining_dv = 0.0
        
    print("=" * 60)
    print("           ORBITAL SIMULATOR v3 MISSION REPORT")
    print("=" * 60)
    print(f"Mission Status:           {'COLLIDED' if history['collided'] else 'COMPLETED'}")
    print(f"Eccentricity (e):         {el['eccentricity']:.6f}")
    print(f"Orbit Type:               {orbit_type}")
    print(f"Collision Status:         {'COLLIDED' if history['collided'] else 'No Collision'}")
    print("-" * 60)
    print(f"Specific Mechanical Energy:  {el['energy']:.6f} (normalized units)")
    print(f"Specific Ang. Momentum:   {el['angular_momentum']:.6f} (normalized units)")
    print(f"Semi-Major Axis (a):      {el['semi_major_axis']:.6f} (normalized units)")
    print(f"Periapsis Radius (rp):    {el['periapsis']:.6f} (normalized units)")
    if el['eccentricity'] < 0.999:
        print(f"Apoapsis Radius (ra):     {el['apoapsis']:.6f} (normalized units)")
        print(f"Orbital Period (T):       {el['period']:.6f} (normalized units)")
    else:
        print("Apoapsis Radius (ra):     N/A (Escape Trajectory)")
        print("Orbital Period (T):       N/A (Escape Trajectory)")
    print("-" * 60)
    print(f"Maximum Altitude:         {np.max(history['altitude']):.6f} (normalized units)")
    print(f"Maximum Speed:            {np.max(history['speed']):.6f} (normalized units)")
    print(f"Fuel Consumed:            {fuel_mass - history['fuel'][-1]:.1f} kg")
    print(f"Remaining Fuel:           {history['fuel'][-1]:.1f} kg")
    print(f"Final Spacecraft Mass:    {history['mass'][-1]:.1f} kg")
    print(f"Total Delta-V Produced:   {history['total_delta_v']:.4f} (normalized units)")
    print(f"Remaining Delta-V Cap.:   {remaining_dv:.4f} (normalized units)")
    print(f"Total Impulse Delivered:  {history['impulse']:.1f} (normalized units)")
    print(f"Simulation Duration:      {history['t'][-1]:.2f} (normalized units)")
    print(f"Simulation Steps:         {len(history['t']) - 1}")
    print("=" * 60)

    # Return elements for use in titles
    return el, orbit_type

# ==============================================================================
# PLOTTING AND VISUALIZATION
# ==============================================================================
def generate_plots(history, el, orbit_type):
    """
    Saves static trajectory plot and performance graphs.
    """
    os.makedirs(output_dir, exist_ok=True)
    r_arr = history["r"]
    collided = history["collided"]

    # 1. Trajectory Plot: orbit_v3.png
    print("Generating static trajectory plot...")
    fig_orbit, ax_orbit = plt.subplots(figsize=(8, 8), dpi=100)
    
    # Plot Earth
    earth = plt.Circle((0, 0), r_earth, color='royalblue', alpha=0.8, zorder=2, label='Earth')
    ax_orbit.add_patch(earth)
    ax_orbit.plot(0, 0, 'o', color='white', markersize=3, zorder=3)
    
    # Plot Trajectory
    ax_orbit.plot(r_arr[:, 0], r_arr[:, 1], '-', color='darkorchid', linewidth=2.0, zorder=4, label='Spacecraft Path')
    
    # Mark Start/End
    ax_orbit.plot(r_arr[0, 0], r_arr[0, 1], 'o', color='forestgreen', markersize=8, zorder=5, label='Start')
    if collided:
        ax_orbit.plot(r_arr[-1, 0], r_arr[-1, 1], 'X', color='red', markersize=10, zorder=6, label='Impact')
    else:
        ax_orbit.plot(r_arr[-1, 0], r_arr[-1, 1], 'o', color='crimson', markersize=8, zorder=5, label='End')
        
    # Annotate Periapsis and Apoapsis on the static trajectory plot
    e_mag = np.linalg.norm(el["eccentricity_vec"])
    if e_mag > 1e-5:
        e_hat = el["eccentricity_vec"] / e_mag
        
        # Periapsis position vector: rp_vec = rp * e_hat
        rp_pos = el["periapsis"] * e_hat
        ax_orbit.plot(rp_pos[0], rp_pos[1], 'D', color='darkcyan', markersize=7, zorder=5, 
                      label=f'Periapsis (rp = {el["periapsis"]:.3f})')
        ax_orbit.annotate("Periapsis", (rp_pos[0], rp_pos[1]), textcoords="offset points", 
                          xytext=(5, 5), fontsize=9, fontweight='bold', color='darkcyan')
        
        # Apoapsis position vector: ra_vec = -ra * e_hat (for elliptical orbits)
        if el["eccentricity"] < 0.999:
            ra_pos = -el["apoapsis"] * e_hat
            ax_orbit.plot(ra_pos[0], ra_pos[1], 'D', color='magenta', markersize=7, zorder=5, 
                          label=f'Apoapsis (ra = {el["apoapsis"]:.3f})')
            ax_orbit.annotate("Apoapsis", (ra_pos[0], ra_pos[1]), textcoords="offset points", 
                              xytext=(-25, -12), fontsize=9, fontweight='bold', color='magenta')
        
    ax_orbit.set_aspect('equal', adjustable='box')
    ax_orbit.grid(True, linestyle=':', alpha=0.6)
    ax_orbit.set_xlabel('X Position (normalized units)', fontsize=11)
    ax_orbit.set_ylabel('Y Position (normalized units)', fontsize=11)
    ax_orbit.set_title(f'Orbital Maneuver: {orbit_type}\n(e = {el["eccentricity"]:.5f})', fontsize=13, fontweight='bold', pad=12)
    ax_orbit.legend(loc='upper right', frameon=True)
    
    max_bound = max(np.max(np.abs(r_arr[:, 0])), np.max(np.abs(r_arr[:, 1])))
    limit = max(max_bound * 1.15, 1.2)
    ax_orbit.set_xlim(-limit, limit)
    ax_orbit.set_ylim(-limit, limit)
    
    plt.tight_layout()
    orbit_path = os.path.join(output_dir, "orbit_v3.png")
    plt.savefig(orbit_path, bbox_inches='tight')
    plt.close(fig_orbit)
    print(f"Saved: {orbit_path}")

    # 2. Performance Plots
    # List of configuration items to loop through and save
    plots_config = [
        # V2 Plots
        {"filename": "fuel_vs_time.png", "title": "Spacecraft Remaining Fuel vs. Time", "ylabel": "Fuel Mass (kg)", "ydata": history["fuel"], "color": "tab:orange"},
        {"filename": "mass_vs_time.png", "title": "Spacecraft Total Mass vs. Time", "ylabel": "Total Mass (kg)", "ydata": history["mass"], "color": "tab:blue"},
        {"filename": "speed_vs_time.png", "title": "Spacecraft Speed vs. Time", "ylabel": "Speed (normalized units)", "ydata": history["speed"], "color": "tab:red"},
        {"filename": "altitude_vs_time.png", "title": "Spacecraft Altitude vs. Time", "ylabel": "Altitude (normalized units)", "ydata": history["altitude"], "color": "tab:green"},
        {"filename": "energy_vs_time.png", "title": "Spacecraft Total Mechanical Energy vs. Time", "ylabel": "Energy (normalized units)", "ydata": history["energy"], "color": "tab:purple"},
        # V3 Plots
        {"filename": "delta_v_vs_time.png", "title": "Accumulated Delta-V vs. Time", "ylabel": "Delta-V (normalized units)", "ydata": history["delta_v"], "color": "darkcyan"},
        {"filename": "thrust_acceleration_vs_time.png", "title": "Thrust Acceleration vs. Time", "ylabel": "Thrust Acceleration (normalized units)", "ydata": history["thrust_acc_mag"], "color": "crimson"},
        {"filename": "grav_acceleration_vs_time.png", "title": "Gravitational Acceleration vs. Time", "ylabel": "Grav Acceleration (normalized units)", "ydata": history["grav_acc_mag"], "color": "navy"},
        {"filename": "angular_momentum_vs_time.png", "title": "Specific Angular Momentum vs. Time", "ylabel": "Specific Angular Momentum (normalized units)", "ydata": history["h"], "color": "indigo"}
    ]

    for p in plots_config:
        print(f"Generating performance plot: {p['title']}...")
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        ax.plot(history["t"], p["ydata"], color=p["color"], linewidth=2.0)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_xlabel("Time (normalized units)", fontsize=11)
        ax.set_ylabel(p["ylabel"], fontsize=11)
        ax.set_title(p["title"], fontsize=13, fontweight='bold', pad=12)
        
        plt.tight_layout()
        file_path = os.path.join(output_dir, p["filename"])
        plt.savefig(file_path, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {file_path}")

def generate_animation(history, orbit_type):
    """
    Creates and saves the orbit_v3.gif animation containing quiver vectors
    (gravity, velocity, thrust) and a live telemetry panel.
    """
    print("Generating animated GIF...")
    fig_anim, ax_anim = plt.subplots(figsize=(9, 9), dpi=100)
    
    r_arr = history["r"]
    v_arr = history["v"]
    a_grav_arr = history["a_grav"]
    a_thrust_arr = history["a_thrust"]
    t_arr = history["t"]
    fuel_arr = history["fuel"]
    mass_arr = history["mass"]
    speed_arr = history["speed"]
    altitude_arr = history["altitude"]
    live_class = history["live_class"]
    ecc_arr = history["ecc"]
    sma_arr = history["sma"]
    collided = history["collided"]
    
    total_len = len(r_arr)
    num_frames = min(150, total_len) # Limit frames to optimize output size

    # Plot Earth
    earth = plt.Circle((0, 0), r_earth, color='royalblue', alpha=0.8, zorder=2)
    ax_anim.add_patch(earth)
    ax_anim.plot(0, 0, 'o', color='white', markersize=3, zorder=3)
    
    # Path line and spacecraft marker
    trail_line, = ax_anim.plot([], [], '--', color='darkorchid', linewidth=1.5, zorder=4, label='Path')
    spacecraft_dot, = ax_anim.plot([], [], 'o', color='crimson', markersize=8, zorder=5, label='Spacecraft')
    
    # Quiver vectors (gravity, velocity, thrust)
    # We apply scale factor of 0.25 (drawn at 25% size in axes scale) so arrows fit nicely on plot
    draw_scale = 0.25
    vel_arrow = ax_anim.quiver(0, 0, 0, 0, color='forestgreen', scale=1.0, scale_units='xy', angles='xy', zorder=6, label='Velocity Vector (scaled)')
    grav_arrow = ax_anim.quiver(0, 0, 0, 0, color='royalblue', scale=1.0, scale_units='xy', angles='xy', zorder=6, label='Gravity Vector (scaled)')
    thrust_arrow = ax_anim.quiver(0, 0, 0, 0, color='crimson', scale=1.0, scale_units='xy', angles='xy', zorder=6, label='Thrust Vector (scaled)')
    
    # Live Telemetry panel
    telemetry_box = ax_anim.text(
        0.02, 0.98, '', transform=ax_anim.transAxes, verticalalignment='top',
        fontsize=9, fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='gray')
    )
    
    ax_anim.set_aspect('equal', adjustable='box')
    ax_anim.grid(True, linestyle=':', alpha=0.6)
    ax_anim.set_xlabel('X Position (normalized units)', fontsize=11)
    ax_anim.set_ylabel('Y Position (normalized units)', fontsize=11)
    ax_anim.set_title(f'Orbital Simulation: {orbit_type}', fontsize=13, fontweight='bold', pad=12)
    ax_anim.legend(loc='lower right', frameon=True, fontsize=8)
    
    max_bound = max(np.max(np.abs(r_arr[:, 0])), np.max(np.abs(r_arr[:, 1])))
    limit = max(max_bound * 1.15, 1.2)
    ax_anim.set_xlim(-limit, limit)
    ax_anim.set_ylim(-limit, limit)
    plt.tight_layout()
    
    def init():
        trail_line.set_data([], [])
        spacecraft_dot.set_data([], [])
        telemetry_box.set_text('')
        return trail_line, spacecraft_dot, vel_arrow, grav_arrow, thrust_arrow, telemetry_box

    def update(frame):
        idx = int(frame * (total_len - 1) / (num_frames - 1))
        
        trail_line.set_data(r_arr[:idx+1, 0], r_arr[:idx+1, 1])
        spacecraft_dot.set_data([r_arr[idx, 0]], [r_arr[idx, 1]])
        
        # Scale vectors for visualization
        v_vec = v_arr[idx] * draw_scale
        g_vec = a_grav_arr[idx] * draw_scale
        t_vec = a_thrust_arr[idx] * draw_scale
        
        # Update arrows
        vel_arrow.set_offsets(r_arr[idx])
        vel_arrow.set_UVC(v_vec[0], v_vec[1])
        
        grav_arrow.set_offsets(r_arr[idx])
        grav_arrow.set_UVC(g_vec[0], g_vec[1])
        
        thrust_arrow.set_offsets(r_arr[idx])
        thrust_arrow.set_UVC(t_vec[0], t_vec[1])
        
        # Determine throttle active at this step
        is_burning = (burn_start_time <= t_arr[idx] <= burn_end_time) and (fuel_arr[idx] > 0)
        curr_throttle = throttle if is_burning else 0.0
        
        # Update telemetry box (with eccentricity and semi-major axis)
        telemetry_box.set_text(
            f"MISSION TELEMETRY PANEL\n"
            f"-----------------------\n"
            f"Time:       {t_arr[idx]:.2f} (normalized units)\n"
            f"Altitude:   {altitude_arr[idx]:.4f} (normalized units)\n"
            f"Speed:      {speed_arr[idx]:.4f} (normalized units)\n"
            f"Eccentr. (e): {ecc_arr[idx]:.5f}\n"
            f"SMA (a):    {sma_arr[idx]:.4f} (normalized units)\n"
            f"Fuel Mass:  {fuel_arr[idx]:.1f} kg\n"
            f"Total Mass: {mass_arr[idx]:.1f} kg\n"
            f"Throttle:   {curr_throttle*100:.1f} %\n"
            f"Orbit Type: {live_class[idx]}"
        )
        
        # Set collision marker at the end if collided
        if collided and idx == total_len - 1:
            spacecraft_dot.set_marker('X')
            spacecraft_dot.set_color('red')
            spacecraft_dot.set_markersize(10)
        else:
            spacecraft_dot.set_marker('o')
            spacecraft_dot.set_color('crimson')
            spacecraft_dot.set_markersize(8)
            
        return trail_line, spacecraft_dot, vel_arrow, grav_arrow, thrust_arrow, telemetry_box

    anim = FuncAnimation(fig_anim, update, frames=num_frames, init_func=init, blit=True, interval=50)
    gif_path = os.path.join(output_dir, "orbit_v3.gif")
    anim.save(gif_path, writer='pillow', fps=20)
    plt.close(fig_anim)
    print(f"Saved: {gif_path}")

# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def main():
    # 1. Run simulation
    history = run_simulation_v3()
    
    # 2. Print mission report
    el, orbit_type = print_mission_report(history)
    
    # 3. Generate static plots
    generate_plots(history, el, orbit_type)
    
    # 4. Generate animation
    generate_animation(history, orbit_type)

if __name__ == "__main__":
    main()
