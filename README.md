# Modular Inverted Pendulum
![This is a screenshot of the application main window.](https://github.com/t-bieber/Modular-Inverted-Pendulum/blob/main/images/screenshot_1.png)
Pssst, hey you! Do you want to apply some control theory?

## About this project
This project aims to provide detailed instructions for building your own inverted pendulum hardware setup and stabilizing it using either one of the sample controllers or letting you apply your own control logic to it.
### Cool story bro, but what's an inverted pendulum?
An inverted pendulum is a classic control theory problem: imagine balancing a broomstick on your hand. You need to constantly move your hand (or a cart) to keep the pendulum upright. There are multiple possible ways to do that mechanically, moving the cart holding the pendulum arm in a linear or rotational axis with a motor, using flywheels,  different kinds of oscillating motion, and probably more.
This project aims to build a classic inverted pendulum on a cart moving along a linear axis. 

[Here's a fantastic introductory lecture on the topic showing a real life system.](https://www.youtube.com/watch?v=D3bblng-Kcc)

## Project Status
Right now this is still a bit of a work in progress. Hardware instructions and more documentation are coming soon - check back later!
In the meantime, feel free to browse the code, try the simulation, or hook it up to real hardware (if you’re brave enough).


## Motivation

I've been fascinated with inverted pendulums since I saw a giant one at a science museum. Some years later, while studying electrical engineering I realized I could actually build one - so I did what every lazy college student does and typed into google: `how to build inverted pendulum`
Turns out, a ton of people have built them before and there's tons of literature about the dynamics and mathematical control theory aspects, but there's not really a how-to guide on building a hardware system. So that's what I'm trying to deliver here.

### Hardware + Simulation 
I've implemented a full nonlinear simulation backend, so you don’t need a full hardware setup to get started. Run the simulation mode and see everything work in real time. Then, when you're ready, flip a switch and use the exact same interface to control your real-world inverted pendulum. Seamless.
(todo: make it actually seamless...)

### Plug-and-Play Controllers
Want to use a PID controller? There's already one available. Prefer something fancier like LQR or even a custom neural net-based thing? Totally possible. The architecture is modular, just write your controller logic and plug it into the system.

### Control everything from a GUI
- Live plots of angle, position, and control effort
- Switch controllers or tune parameters without recompiling and uploading
