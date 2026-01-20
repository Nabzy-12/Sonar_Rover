"""
Sonar Rover - Radar-Style Visualizer
=====================================
A cool radar/sonar sweep display with depth-based coloring.
Blue = close, Green = medium, Yellow/Red = far

Can run in DEMO mode without the rover connected!
"""

import argparse
import json
import math
import random
import sys
import time
from collections import deque
from typing import Optional

import numpy as np

try:
    import serial
    from serial.tools import list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches


# Custom colormap: blue (close) -> cyan -> green -> yellow -> red (far)
RADAR_COLORS = [
    (0.0, 0.2, 1.0),   # Blue (close)
    (0.0, 0.8, 1.0),   # Cyan
    (0.0, 1.0, 0.4),   # Green
    (0.8, 1.0, 0.0),   # Yellow
    (1.0, 0.5, 0.0),   # Orange
    (1.0, 0.0, 0.0),   # Red (far)
]
RADAR_CMAP = LinearSegmentedColormap.from_list("radar", RADAR_COLORS, N=256)


def pick_port() -> Optional[str]:
    """Auto-detect micro:bit serial port."""
    if not HAS_SERIAL:
        return None
    ports = list(list_ports.comports())
    if not ports:
        return None
    # Prefer micro:bit / mbed ports
    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ["micro:bit", "mbed", "nrf", "daplink", "usb serial"]):
            return p.device
    return ports[0].device


class RadarVisualizer:
    def __init__(self, max_points: int = 8000, max_dist: float = 200.0, demo: bool = False):
        self.max_points = max_points
        self.max_dist = max_dist
        self.demo = demo
        
        # Point storage: (x, y, dist, age)
        self.points = deque(maxlen=max_points)
        
        # For demo mode
        self.demo_angle = 0.0
        self.demo_walls = self._generate_demo_environment()
        
        # Setup dark figure
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 10), facecolor='black')
        self.ax.set_facecolor('black')
        
        # Remove axes for cleaner look
        self.ax.set_xlim(-max_dist, max_dist)
        self.ax.set_ylim(-max_dist, max_dist)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Title
        mode_text = "DEMO MODE" if demo else "LIVE"
        self.title = self.ax.set_title(f"SONAR RADAR - {mode_text}", 
                                        color='#00ff00', fontsize=14, fontweight='bold')
        
        # Scatter plot for points
        self.scatter = self.ax.scatter([], [], s=4, c=[], cmap=RADAR_CMAP, 
                                        vmin=0, vmax=max_dist, alpha=0.8)
        
        # Draw radar grid circles
        for r in [50, 100, 150, 200]:
            if r <= max_dist:
                circle = plt.Circle((0, 0), r, fill=False, color='#003300', 
                                   linestyle='--', linewidth=0.5, alpha=0.5)
                self.ax.add_patch(circle)
                self.ax.text(r * 0.7, r * 0.7, f'{r}cm', color='#004400', 
                           fontsize=8, alpha=0.7)
        
        # Draw crosshairs
        self.ax.axhline(y=0, color='#003300', linewidth=0.5, alpha=0.5)
        self.ax.axvline(x=0, color='#003300', linewidth=0.5, alpha=0.5)
        
        # Sweep line (current scan direction)
        self.sweep_line, = self.ax.plot([0, 0], [0, max_dist], 
                                         color='#00ff00', linewidth=2, alpha=0.8)
        
        # Info text
        self.info_text = self.ax.text(-max_dist * 0.95, -max_dist * 0.9, '', 
                                       color='#00ff00', fontsize=10, 
                                       fontfamily='monospace')
        
        # Status indicators
        self.status_text = self.ax.text(-max_dist * 0.95, max_dist * 0.9, 
                                         'B BST    M MAP', color='#00aa00', 
                                         fontsize=10, fontfamily='monospace',
                                         bbox=dict(boxstyle='round', facecolor='#001100', 
                                                  edgecolor='#004400'))
        
        self.last_heading = 0.0
        self.point_count = 0
        self.start_time = time.time()
        
    def _generate_demo_environment(self):
        """Generate fake walls/obstacles for demo mode."""
        walls = []
        # Room corners (roughly rectangular room)
        walls.append(("rect", -80, -60, 160, 120))  # Main room
        # Some obstacles
        walls.append(("circle", 40, 30, 20))   # Round obstacle
        walls.append(("circle", -50, -20, 15)) # Another
        walls.append(("rect", -30, 50, 25, 30))  # Box
        return walls
    
    def _demo_raycast(self, angle_deg: float) -> float:
        """Simulate sonar reading in demo environment."""
        angle_rad = math.radians(angle_deg)
        dx = math.sin(angle_rad)
        dy = math.cos(angle_rad)
        
        min_dist = self.max_dist
        
        # Check against walls
        for wall in self.demo_walls:
            if wall[0] == "rect":
                _, x, y, w, h = wall
                # Simple ray-box intersection
                for dist in range(5, int(self.max_dist), 2):
                    px = dx * dist
                    py = dy * dist
                    if x <= px <= x + w and y <= py <= y + h:
                        min_dist = min(min_dist, dist)
                        break
            elif wall[0] == "circle":
                _, cx, cy, r = wall
                # Ray-circle intersection
                for dist in range(5, int(self.max_dist), 2):
                    px = dx * dist
                    py = dy * dist
                    if (px - cx)**2 + (py - cy)**2 <= r**2:
                        min_dist = min(min_dist, dist)
                        break
        
        # Add some noise
        if min_dist < self.max_dist:
            min_dist += random.gauss(0, 2)
            min_dist = max(5, min(self.max_dist, min_dist))
        
        return min_dist
    
    def add_point(self, heading_deg: float, dist_cm: float):
        """Add a sonar reading point."""
        if dist_cm <= 0 or dist_cm > self.max_dist:
            return
            
        # Convert polar to cartesian
        theta = math.radians(heading_deg)
        x = dist_cm * math.sin(theta)
        y = dist_cm * math.cos(theta)
        
        # Add some scatter for visual effect (simulates sonar beam width)
        for _ in range(3):
            scatter_angle = theta + random.gauss(0, 0.05)
            scatter_dist = dist_cm + random.gauss(0, 1.5)
            if scatter_dist > 0:
                sx = scatter_dist * math.sin(scatter_angle)
                sy = scatter_dist * math.cos(scatter_angle)
                self.points.append((sx, sy, scatter_dist, time.time()))
        
        self.last_heading = heading_deg
        self.point_count += 1
    
    def update_plot(self):
        """Update the visualization."""
        if not self.points:
            return
        
        # Extract point data
        now = time.time()
        xs, ys, dists, ages = [], [], [], []
        
        for x, y, d, t in self.points:
            age = now - t
            if age < 30:  # Fade out after 30 seconds
                xs.append(x)
                ys.append(y)
                dists.append(d)
                ages.append(age)
        
        if not xs:
            return
        
        # Update scatter
        offsets = np.column_stack([xs, ys])
        self.scatter.set_offsets(offsets)
        self.scatter.set_array(np.array(dists))
        
        # Fade based on age (newer = brighter)
        alphas = [max(0.1, 1.0 - (a / 30)) for a in ages]
        self.scatter.set_alpha(np.mean(alphas))
        
        # Update sweep line
        theta = math.radians(self.last_heading)
        self.sweep_line.set_data([0, self.max_dist * math.sin(theta)],
                                  [0, self.max_dist * math.cos(theta)])
        
        # Update info
        elapsed = now - self.start_time
        info = f"Points: {len(xs):,}\nHeading: {self.last_heading:.0f}°\nTime: {elapsed:.0f}s"
        self.info_text.set_text(info)
        
    def run_demo(self):
        """Run in demo mode (no hardware needed)."""
        print("Running in DEMO mode - simulating sonar sweep")
        print("Close the window to exit")
        
        try:
            while True:
                # Simulate continuous rotation scan
                self.demo_angle = (self.demo_angle + 2) % 360
                dist = self._demo_raycast(self.demo_angle)
                self.add_point(self.demo_angle, dist)
                
                self.update_plot()
                plt.pause(0.02)
                
        except KeyboardInterrupt:
            print("\nExiting...")
    
    def run_serial(self, port: str, baud: int = 115200):
        """Run with live serial data from micro:bit."""
        print(f"Connecting to {port} @ {baud}...")
        
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
            print("Connected! Waiting for data...")
            print("Put the rover in SCAN mode (press A+B on micro:bit)")
            
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                
                if line:
                    try:
                        msg = json.loads(line)
                        dist = float(msg.get("dist_cm", 0) or 0)
                        heading = float(msg.get("heading_deg", -1) or -1)
                        
                        if heading >= 0 and dist > 0:
                            self.add_point(heading, dist)
                            
                    except (json.JSONDecodeError, ValueError):
                        pass
                
                self.update_plot()
                plt.pause(0.01)
                
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            print("\nTry these fixes:")
            print("1. Make sure the micro:bit is plugged in via USB")
            print("2. Close any other programs using the serial port")
            print("3. Try a different USB port")
            print("\nRunning DEMO mode instead...")
            self.demo = True
            self.title.set_text("SONAR RADAR - DEMO MODE")
            self.run_demo()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            try:
                ser.close()
            except:
                pass


def main():
    ap = argparse.ArgumentParser(
        description="Radar-style sonar visualizer for micro:bit MiniBit rover",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python radar.py --demo          # Run demo without hardware
  python radar.py --port COM3     # Connect to micro:bit on COM3
  python radar.py                 # Auto-detect port, or run demo
        """)
    ap.add_argument("--port", help="Serial port (e.g., COM3). Auto-detects if omitted.")
    ap.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    ap.add_argument("--demo", action="store_true", help="Run in demo mode (no hardware)")
    ap.add_argument("--max-points", type=int, default=8000, help="Max points to display")
    ap.add_argument("--max-dist", type=float, default=200.0, help="Max distance in cm")
    args = ap.parse_args()
    
    viz = RadarVisualizer(
        max_points=args.max_points,
        max_dist=args.max_dist,
        demo=args.demo
    )
    
    if args.demo:
        viz.run_demo()
    elif args.port:
        viz.run_serial(args.port, args.baud)
    else:
        # Try to auto-detect, fall back to demo
        port = pick_port()
        if port:
            print(f"Auto-detected port: {port}")
            viz.run_serial(port, args.baud)
        else:
            print("No serial port found, running demo mode")
            viz.demo = True
            viz.title.set_text("SONAR RADAR - DEMO MODE")
            viz.run_demo()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
