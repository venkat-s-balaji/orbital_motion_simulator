# Orbital Motion Simulator

A physics-based spacecraft trajectory simulator developed in Python to explore orbital mechanics, numerical methods, spacecraft propulsion, and fuel consumption.

This project began as a gravity-only orbital mechanics simulator (Version 1) and evolved into a propulsion-enabled spacecraft dynamics simulator (Version 2).

---

# Table of Contents

* [Introduction](#introduction)
* [Project Goals](#project-goals)
* [Physics Background](#physics-background)
* [Version 1](#version-1)
* [Version 2](#version-2)
* [Numerical Methods](#numerical-methods)
* [How to Run](#how-to-run)
* [Results and Visualizations](#results-and-visualizations)
* [Limitations](#limitations)
* [Future Development](#future-development)
* [Author](#author)

---

# Introduction

Orbital motion is one of the fundamental problems in aerospace engineering. The objective of this project is to simulate spacecraft motion around Earth while investigating how gravity, velocity, mass, thrust, and fuel consumption influence trajectories.

The simulator demonstrates how different initial conditions produce:

* Circular Orbits
* Elliptical Orbits
* Escape Trajectories
* Earth Impact Trajectories

and later extends these concepts through spacecraft propulsion modeling.

---

# Project Goals

This project was created to gain hands-on experience with:

* Orbital Mechanics
* Newtonian Gravity
* Spacecraft Propulsion
* Fuel Consumption Modeling
* Numerical Integration Methods
* Scientific Computing using Python
* Aerospace Engineering Simulation
* Engineering Data Visualization

---

# Physics Background

## Newtonian Gravity

The spacecraft experiences gravitational acceleration directed toward Earth:

a = GM / r²

where:

* G = Universal Gravitational Constant
* M = Mass of Earth
* r = Distance from Earth's center

Instead of calculating gravitational force directly, the simulator uses gravitational acceleration because spacecraft mass cancels out when Newton's Law of Gravitation is combined with Newton's Second Law.

The quantity:

GM

is known as the Standard Gravitational Parameter.

---

## Spacecraft Propulsion

Version 2 introduces propulsion using Newton's Second Law:

F = ma

which gives:

a_thrust = F_thrust / m

where:

* F_thrust = Engine Thrust Force
* m = Current Spacecraft Mass

As fuel is consumed, spacecraft mass decreases and thrust acceleration increases.

This behavior mirrors real spacecraft.

---

## Mechanical Energy

The simulator tracks total mechanical energy:

E = K + U

where:

Kinetic Energy:

E_k = 1/2 mv²

Potential Energy:

E_p = -GMm/r

Total Energy:

E = 1/2 mv² - GMm/r

Energy values are reported in normalized units because the simulator uses normalized distances and velocities rather than real-world SI units.

---

# Version 1

## Description

Version 1 simulates orbital motion under gravity only.

No propulsion system is included.

The objective is to observe how initial velocity determines orbital behavior.

## Features

* Inverse-square gravity
* Circular orbit simulation
* Elliptical orbit simulation
* Escape trajectory simulation
* Earth impact simulation
* Collision detection
* Euler-Cromer integration
* Static trajectory visualization
* Animated trajectory visualization

## Version 1 Visualization

<img width="1000" height="1000" alt="orbit" src="https://github.com/user-attachments/assets/03252c02-06c4-4555-843e-36585d434edd" />


<img width="3000" height="3000" alt="orbit_static" src="https://github.com/user-attachments/assets/6684ade9-e3d3-4627-919f-63c48389e54d" />


## Example Scenarios

### Circular Orbit

Initial Conditions:

```python
v_init = [0.0, 1.0]
```

Produces a nearly constant orbital radius.

### Elliptical Orbit

```python
v_init = [0.0, 0.65]
```

Produces a bound orbit with changing radius.

### Escape Trajectory

```python
v_init = [0.0, 1.5]
```

Produces a trajectory with sufficient energy to leave Earth's gravitational influence.

### Impact Trajectory

```python
v_init = [0.0, 0.15]
```

Results in collision with Earth.

---

# Version 2

## Description

Version 2 extends the simulator by introducing spacecraft propulsion and fuel consumption.

Instead of pre-defining the orbit type, the simulator accepts spacecraft parameters and automatically determines whether the resulting trajectory is:

* Circular Orbit
* Elliptical Orbit
* Escape Trajectory
* Impact Trajectory

based on the physics of the simulation.

## New Features

* Adjustable spacecraft mass
* Adjustable fuel mass
* Adjustable thrust force
* Adjustable burn rate
* Adjustable throttle setting
* Dynamic mass updates
* Fuel consumption tracking
* Energy tracking
* Orbit classification
* Telemetry reporting
* Performance analysis plots

## User Inputs

```python
r_init
v_init

spacecraft_mass
fuel_mass

thrust_force
burn_rate
throttle

dt
num_steps
```

## Important Note

To observe pure orbital mechanics:

```python
throttle = 0.0
```

To study propulsion effects:

```python
throttle > 0.0
```

With propulsion enabled, spacecraft can spiral outward, gain orbital energy, and potentially escape Earth's gravitational influence.

## Version 2 Visualization

<img width="779" height="790" alt="orbit_v2" src="https://github.com/user-attachments/assets/09b4c6f8-20ca-46bb-b573-b09c04e0b18b" />


---

# Numerical Methods

The simulator uses the Euler-Cromer integration method.

Velocity is updated first:

v_new = v_old + a·dt

Position is then updated using the newly updated velocity:

r_new = r_old + v_new·dt

Compared to standard Euler integration, Euler-Cromer provides improved stability and better energy behavior for orbital simulations.

---

# How to Run

Clone the repository:

```bash
git clone <repository-url>
```

Navigate into the project:

```bash
cd orbital-simulator
```

Run Version 1:

```bash
python orbital_simulator_v1.py
```

Run Version 2:

```bash
python orbital_simulator_v2.py
```

Generated outputs will be automatically saved to:

```text
simulation_outputs/
```

---

# Results and Visualizations

Version 2 generates:

```text
orbit_v2.png
orbit_v2.gif

fuel_vs_time.png
mass_vs_time.png
speed_vs_time.png
altitude_vs_time.png
energy_vs_time.png
```

## Performance Plots

<img width="989" height="490" alt="fuel_vs_time" src="https://github.com/user-attachments/assets/317632c8-b9f7-4125-af31-fd3f31e22a9e" />


<img width="989" height="490" alt="mass_vs_time" src="https://github.com/user-attachments/assets/4959efda-9a3d-46ff-b00c-2f7bd37864a5" />


<img width="989" height="490" alt="speed_vs_time" src="https://github.com/user-attachments/assets/695c343e-9fc2-48f7-a4ec-0f350cbfb8f0" />


<img width="989" height="490" alt="altitude_vs_time" src="https://github.com/user-attachments/assets/92818c26-5fce-4149-a39c-b5d74a4f519d" />


<img width="990" height="490" alt="energy_vs_time" src="https://github.com/user-attachments/assets/ba99f74d-e950-4004-8475-2564b7d2339f" />


---

# Limitations

Current assumptions:

* Fixed Earth position
* Two-dimensional motion
* No atmospheric drag
* No planetary rotation
* No Moon gravity
* No multi-body effects
* No rocket staging
* No attitude control system
* Normalized units rather than SI units

These simplifications allow the simulator to focus on fundamental orbital dynamics.

---

# Future Development

Planned future improvements include:

* Real-world SI units
* Earth-based orbital altitudes
* Atmospheric drag modeling
* Hohmann transfer maneuvers
* Retrograde and radial burns
* Multi-stage rockets
* Moon and planetary gravity
* N-body simulations
* Mission planning capabilities
* Interactive graphical interface
* 3D orbital visualization

---

# Author

**Venkat Balaji**

Mechanical Engineering Student

Academic Interests:

* Orbital Mechanics
* Spacecraft Propulsion
* Aerospace Engineering
* Numerical Simulation
* Space Mission Design

This project was developed as an independent study in orbital mechanics and spacecraft dynamics.
