# Sonar Rover – Project Overview

This repo is a starter for a micro:bit + 4tronix MiniBit rover with an ultrasonic sonar module.

High-level architecture:
- **Rover micro:bit** runs on the MiniBit, drives motors + reads sonar, streams telemetry over USB serial.
- Optional **Controller micro:bit** sends radio commands (tank drive) so you can drive without a cable.
- A **PC visualizer** reads serial telemetry and plots a simple “sonar sweep” map.

Planned features (incremental):
1. Obstacle avoid (done in firmware)
2. Follow target distance (done in firmware)
3. Scan/sweep mapping (done in firmware + visualizer)
4. Better mapping: integrate wheel odometry (would require encoders) or external localization
