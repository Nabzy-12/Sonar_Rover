# Sonar Visualizers 📊

Python visualizers for the sonar rover.

## Visualizers

| Script | Description |
|--------|-------------|
| `sonar_radar.py` | Radar-style display - shows distance ahead with fading points |
| `sonar_pulse.py` | Ambient pulse display - scanner sombre style visualization |

## Setup

```powershell
# Create virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

```powershell
# Radar view (recommended)
python sonar_radar.py --port COM3

# Pulse display
python sonar_pulse.py --port COM3
```

## Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Drive the rover |
| SPACE | Stop |
| C | Clear points |
| ESC | Quit |

## Serial Format

Expects JSON from micro:bit at 115200 baud:
```json
{"d":42,"a":180,"s":"FWD"}
```
