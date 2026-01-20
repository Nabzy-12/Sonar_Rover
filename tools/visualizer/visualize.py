import argparse
import json
import math
import sys
import time

import numpy as np
import serial
from serial.tools import list_ports

import matplotlib.pyplot as plt


def pick_port() -> str:
    ports = list(list_ports.comports())
    if not ports:
        raise SystemExit("No serial ports found. Is the micro:bit plugged in?")

    # Prefer micro:bit / mbed ports if present
    preferred = []
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if "micro:bit" in desc or "mbed" in desc or "nrf" in desc or "daplink" in desc:
            preferred.append(p.device)

    if preferred:
        return preferred[0]

    # Otherwise just take the first
    return ports[0].device


def main() -> int:
    ap = argparse.ArgumentParser(description="Live sonar sweep visualizer (micro:bit MiniBit rover)")
    ap.add_argument("--port", help="Serial port (e.g. COM5). If omitted, auto-detect.")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--max-points", type=int, default=600)
    ap.add_argument("--min-cm", type=float, default=1.0)
    ap.add_argument("--max-cm", type=float, default=200.0)
    args = ap.parse_args()

    port = args.port or pick_port()
    print(f"Opening {port} @ {args.baud}…", flush=True)

    ser = serial.Serial(port=port, baudrate=args.baud, timeout=0.2)

    xs: list[float] = []
    ys: list[float] = []
    cs: list[float] = []  # color = time

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(7, 7))
    sc = ax.scatter([], [], s=12)

    ax.set_title("Sonar Rover – live sweep")
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.set_aspect("equal", adjustable="box")

    # Set a reasonable fixed view; you can zoom in/out in the UI
    lim = args.max_cm
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    last_print = time.time()

    def update_plot():
        if not xs:
            sc.set_offsets(np.zeros((0, 2)))
            return
        offsets = np.column_stack([xs, ys])
        sc.set_offsets(offsets)
        # Fade older points
        t = np.array(cs)
        t = (t - t.min()) / (t.max() - t.min() + 1e-9)
        colors = plt.cm.viridis(t)
        sc.set_color(colors)

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                plt.pause(0.01)
                continue

            # Expect JSON lines like: {"t":...,"mode":"scan",...}
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            dist = float(msg.get("dist_cm", 0.0) or 0.0)
            heading = float(msg.get("heading_deg", -1.0) or -1.0)

            if dist < args.min_cm or dist > args.max_cm:
                continue
            if heading < 0:
                # If compass isn’t available we can’t orient points; skip.
                continue

            theta = math.radians(heading)
            x = dist * math.sin(theta)
            y = dist * math.cos(theta)

            xs.append(x)
            ys.append(y)
            cs.append(time.time())

            if len(xs) > args.max_points:
                xs[:] = xs[-args.max_points :]
                ys[:] = ys[-args.max_points :]
                cs[:] = cs[-args.max_points :]

            update_plot()
            plt.pause(0.001)

            now = time.time()
            if now - last_print > 2.0:
                mode = msg.get("mode", "?")
                note = msg.get("note", "")
                print(f"mode={mode} dist_cm={dist:.0f} heading={heading:.0f} note={note}")
                last_print = now

    except KeyboardInterrupt:
        print("\nExiting…")
        return 0
    finally:
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
