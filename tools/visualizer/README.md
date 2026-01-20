# Sonar Rover Visualizer

Shows a live 2D scatter plot from the rover’s USB serial telemetry.

## Setup

Create a venv and install deps:

- Windows PowerShell:
  - `py -m venv .venv`
  - `./.venv/Scripts/Activate.ps1`
  - `pip install -r requirements.txt`

## Run

- Auto-detect port:
  - `python visualize.py`

- Or specify port:
  - `python visualize.py --port COM5`

## Expected rover output

The rover firmware streams newline-delimited JSON like:

`{"t":123,"mode":"scan","dist_cm":42,"heading_deg":180,"note":"scan"}`
