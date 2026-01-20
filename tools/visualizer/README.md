# Sonar Visualizers 📊

Multiple visualization styles for sonar data from the micro:bit rover.

## Visualizers

| Script | Description |
|--------|-------------|
| `radar.py` | Classic radar sweep - simple and reliable |
| `lidar.py` | LIDAR-style point cloud view |
| `pointcloud.py` | Accumulating 3D point cloud |
| `depth_scanner.py` | First-person depth view |
| `visualize.py` | Original simple scatter plot |

## Setup

```powershell
# Create virtual environment
py -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## Usage

```powershell
# Radar view (recommended)
python radar.py --port COM3

# LIDAR point cloud
python lidar.py --port COM3

# 3D point cloud builder  
python pointcloud.py --port COM3

# Demo mode (no hardware)
python radar.py --demo
```

## Serial Format

Expects JSON from micro:bit:
```json
{"dist_cm":42,"heading_deg":180}
```
