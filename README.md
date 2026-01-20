# Sonar Rover (micro:bit + 4tronix MiniBit + sonar)

This repo is a starter project for a MiniBit rover that can:
- avoid obstacles
- follow an object in front (distance keeping)
- do a simple scan/sweep and stream readings to your PC

## What you need

- micro:bit on a 4tronix MiniBit chassis
- the optional ultrasonic sonar module installed
- USB cable to your PC

## Flash the rover firmware

The rover MakeCode project is the repo root (so it can be imported directly into MakeCode).

1. Open MakeCode: https://makecode.microbit.org/
2. Import → Import URL → paste your GitHub repo URL
3. Download → copy the `.hex` to the micro:bit drive

If MakeCode prompts to calibrate the compass (figure-8 motion), do it once — the scan visualizer uses compass heading.

## Rover controls

- Button A: cycle modes (manual → avoid → follow → scan)
- Button B: brake/stop
- Buttons A+B: toggle scan on/off

## USB serial control (manual)

The rover listens for newline-terminated commands over the micro:bit serial port.

- Drive: `F` `B` `L` `R` `STOP`
- Modes: `MANUAL` `AVOID` `FOLLOW` `SCAN`
- Tank drive: `T:<left>,<right>` where values are -100..100 (example: `T:60,40`)

## PC visualizer (optional)

The visualizer reads JSON telemetry from USB serial and plots a simple 2D sweep.

1. Go to [tools/visualizer](tools/visualizer)
2. Create a venv + install deps:
	- `py -m venv .venv`
	- `./.venv/Scripts/Activate.ps1`
	- `pip install -r requirements.txt`
3. Run:
	- `python visualize.py`
	- or `python visualize.py --port COM5`

## Repo layout

- [main.ts](main.ts): rover firmware
- [firmware/controller](firmware/controller): optional second micro:bit “radio controller” firmware
- [tools/visualizer](tools/visualizer): Python visualizer
- [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md): architecture + next steps