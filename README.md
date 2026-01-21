# Sonar Rover 🤖

**micro:bit + 4tronix MiniBit + Ultrasonic Sonar**

A PC-controlled rover with real-time sonar visualization.

## 🎯 Features

- **PC keyboard control** - WASD to drive the rover via USB serial
- **Real-time sonar display** - see distance readings as you drive
- **Two visualizer modes** - radar view and ambient pulse display

## 📋 Requirements

- micro:bit v2 on a 4tronix MiniBit chassis
- HC-SR04 ultrasonic sonar module (included with MiniBit)
- USB cable to PC
- Python 3.8+ with pygame-ce, pyserial

## 🚀 Quick Start

### 1. Flash the Firmware

1. Open [MakeCode](https://makecode.microbit.org/)
2. New Project → switch to **JavaScript** mode
3. Add extension: `github:4tronix/MiniBit`
4. Copy code from `firmware/simple_rover.ts`
5. Download and drag `.hex` to MICROBIT drive

### 2. Run the Visualizer

```powershell
cd tools/visualizer
pip install -r requirements.txt
python sonar_radar.py --port COM3
```

## 📁 Project Structure

```
Sonar_Rover/
├── firmware/
│   └── simple_rover.ts    # PC-controlled rover firmware
├── tools/visualizer/
│   ├── sonar_radar.py     # Radar-style display
│   ├── sonar_pulse.py     # Ambient pulse display
│   └── requirements.txt   # Python dependencies
└── README.md
```

## 🎮 Controls

### PC Keyboard (in visualizer window)
| Key | Action |
|-----|--------|
| W | Drive forward |
| S | Drive backward |
| A | Turn left |
| D | Turn right |
| SPACE | Stop |
| C | Clear display |

### micro:bit Buttons
| Button | Action |
|--------|--------|
| A | Emergency stop |
| B | Reset angle to 0 |

## 🔧 Troubleshooting

**No serial data?**
- Check the COM port number in Device Manager
- Try `--port COM3` (or your actual port)

**Rover doesn't respond?**
- Make sure firmware is flashed
- Check USB connection
- Press A on micro:bit to reset

## 📊 Serial Protocol

Firmware sends JSON at 115200 baud:
```json
{"d":42,"a":180,"s":"FWD"}
```
- `d` - distance in cm
- `a` - tracked angle (experimental)
- `s` - current state (STOP, FWD, REV, LEFT, RIGHT, etc.)

PC sends single-letter commands:
- `F` / `B` - start forward/backward
- `L` / `R` - start left/right turn
- `SF` / `ST` - stop forward/turn axis
- `X` - full stop

## ⚠️ Limitations

- **No mapping** - accurate angle tracking isn't possible without encoders or better sensors
- **Single sonar** - only sees what's directly ahead
- The compass is unusable due to motor magnetic interference

Future improvements would need wheel encoders or a servo-mounted sensor for proper mapping.
