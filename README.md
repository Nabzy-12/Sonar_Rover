# Sonar Rover 🤖

**micro:bit + 4tronix MiniBit + Ultrasonic Sonar**

A sonar-based rover that visualizes depth data like a LIDAR scanner.

## 🎯 Features

- **Real-time sonar scanning** - streams distance readings via USB serial
- **Multiple visualizers** - radar, point cloud, and depth views
- **Rover control modes** - manual, obstacle avoidance, object following
- **Color-coded distance** - LEDs change color based on proximity

## 📋 Requirements

- micro:bit v2 on a 4tronix MiniBit chassis
- HC-SR04 ultrasonic sonar module (included with MiniBit)
- USB cable to PC
- Python 3.8+ with matplotlib, numpy, pyserial

## 🚀 Quick Start

### 1. Flash the Firmware

**Option A: Simple Scanner (recommended to start)**
1. Open [MakeCode](https://makecode.microbit.org/)
2. New Project → switch to **JavaScript** mode
3. Add extension: `github:4tronix/MiniBit`
4. Copy code from `firmware/fast_scanner.ts`
5. Download and drag `.hex` to MICROBIT drive

**Option B: Full Rover (advanced)**
1. Open [MakeCode](https://makecode.microbit.org/)
2. Import → Import URL → paste this GitHub repo URL
3. Download and flash

### 2. Run the Visualizer

```powershell
cd tools/visualizer
pip install -r requirements.txt
python radar.py --port COM3
```

Or try other visualizers:
- `radar.py` - Classic radar sweep display
- `lidar.py` - LIDAR-style point cloud
- `pointcloud.py` - 3D point cloud builder
- `depth_scanner.py` - First-person depth view

## 📁 Project Structure

```
Sonar_Rover/
├── main.ts              # Full rover firmware (MakeCode import)
├── pxt.json             # MakeCode project config
├── firmware/
│   ├── fast_scanner.ts  # Simple fast scanning firmware
│   ├── sonar_test.ts    # Basic sonar test
│   └── controller/      # Optional radio controller
├── tools/visualizer/
│   ├── radar.py         # Radar-style visualizer
│   ├── lidar.py         # LIDAR point cloud
│   ├── pointcloud.py    # 3D point cloud builder
│   └── requirements.txt # Python dependencies
└── docs/                # Documentation
```

## 🎮 Controls (Full Rover Mode)

| Button | Action |
|--------|--------|
| A | Cycle modes: Manual → Avoid → Follow → Scan |
| B | Stop/Brake |
| A+B | Toggle scanning |

### Serial Commands
- `F` `B` `L` `R` `STOP` - Drive commands
- `MANUAL` `AVOID` `FOLLOW` `SCAN` - Mode switching
- `T:<left>,<right>` - Tank drive (-100 to 100)

## 🔧 Troubleshooting

**No serial data?**
- Make sure micro:bit is connected via USB
- Check the COM port number in Device Manager
- Try `--port COM3` (or your port)

**MakeCode import fails?**
- Use "Import URL" not "Open"
- Make sure to add the MiniBit extension

**VS Code shows TypeScript errors?**
- These are expected - the type stubs are for IntelliSense only
- MakeCode provides the real implementations

## 📊 Serial Data Format

The firmware sends JSON telemetry:
```json
{"dist_cm":42,"heading_deg":180}
```

## 🛠️ Status

- ✅ Sonar hardware working
- ✅ Serial communication working
- ✅ Basic visualizers working
- 🔄 Point cloud visualizer (WIP)
- 📋 Autonomous scanning (TODO)

## Repo layout

- [main.ts](main.ts): rover firmware
- [firmware/controller](firmware/controller): optional second micro:bit “radio controller” firmware
- [tools/visualizer](tools/visualizer): Python visualizer
- [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md): architecture + next steps