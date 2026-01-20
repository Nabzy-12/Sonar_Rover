"""
LIDAR-Style Depth Visualizer
=============================
Creates a dense point-cloud visualization similar to LIDAR scanners.
Blue = close, Cyan/Green = medium, Yellow/Orange/Red = far

Works in DEMO mode without hardware, or with live micro:bit data.
"""

import argparse
import json
import math
import random
import sys
import time
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

try:
    import serial
    from serial.tools import list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class LidarVisualizer:
    def __init__(self, max_points: int = 15000, max_dist: float = 250.0):
        self.max_points = max_points
        self.max_dist = max_dist
        
        # Point storage: deque of (x, y, dist, timestamp)
        self.points = deque(maxlen=max_points)
        
        # Create custom colormap: blue -> cyan -> green -> yellow -> orange -> red
        colors = [
            (0.0, 0.0, 0.8),    # Dark blue (very close)
            (0.0, 0.4, 1.0),    # Blue
            (0.0, 0.8, 1.0),    # Cyan
            (0.0, 1.0, 0.5),    # Cyan-green
            (0.2, 1.0, 0.2),    # Green
            (0.6, 1.0, 0.0),    # Yellow-green
            (1.0, 1.0, 0.0),    # Yellow
            (1.0, 0.6, 0.0),    # Orange
            (1.0, 0.3, 0.0),    # Red-orange
            (1.0, 0.0, 0.0),    # Red (far)
        ]
        self.cmap = LinearSegmentedColormap.from_list("lidar", colors, N=512)
        
        # Setup figure with black background
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 10), facecolor='black')
        self.ax = self.fig.add_subplot(111, facecolor='black')
        
        # Remove all borders and axes for immersive look
        self.ax.set_xlim(-max_dist, max_dist)
        self.ax.set_ylim(-max_dist * 0.3, max_dist)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Main scatter plot - will be updated
        self.scatter = self.ax.scatter([], [], s=2, c=[], cmap=self.cmap,
                                        vmin=0, vmax=max_dist, alpha=0.9)
        
        # HUD elements
        self.info_text = self.ax.text(
            -max_dist * 0.95, -max_dist * 0.25,
            '', color='#00ff00', fontsize=11,
            fontfamily='monospace', fontweight='bold'
        )
        
        # Distance bar indicator (bottom right)
        self.dist_text = self.ax.text(
            max_dist * 0.7, -max_dist * 0.25,
            '', color='#00ffff', fontsize=12,
            fontfamily='monospace', fontweight='bold'
        )
        
        # Scanner device graphic (bottom center) - like in the reference
        self._draw_scanner_device()
        
        # Stats
        self.scan_count = 0
        self.last_dist = 0
        self.last_heading = 0
        self.start_time = time.time()
        
        # Demo environment
        self.demo_angle = 0
        self.demo_env = self._create_demo_environment()
        
    def _draw_scanner_device(self):
        """Draw a simple scanner device graphic at bottom."""
        # Red scanner body
        from matplotlib.patches import FancyBboxPatch, Circle
        
        scanner_x = self.max_dist * 0.35
        scanner_y = -self.max_dist * 0.22
        
        # Main body
        body = FancyBboxPatch(
            (scanner_x, scanner_y), 60, 30,
            boxstyle="round,pad=0.02,rounding_size=5",
            facecolor='#440000', edgecolor='#880000', linewidth=2
        )
        self.ax.add_patch(body)
        
        # Screen/lens
        lens = Circle((scanner_x + 15, scanner_y + 15), 8,
                      facecolor='#001100', edgecolor='#00ff00', linewidth=1)
        self.ax.add_patch(lens)
        
        # Display
        display = FancyBboxPatch(
            (scanner_x + 30, scanner_y + 5), 25, 20,
            boxstyle="round,pad=0.01,rounding_size=2",
            facecolor='#002200', edgecolor='#004400', linewidth=1
        )
        self.ax.add_patch(display)
        
    def _create_demo_environment(self):
        """Create a complex demo environment with walls, pillars, etc."""
        env = []
        
        # Back wall
        for x in range(-200, 201, 3):
            env.append((x, 180 + random.gauss(0, 5), 'wall'))
        
        # Side walls
        for y in range(0, 181, 3):
            env.append((-180 + random.gauss(0, 3), y, 'wall'))
            env.append((180 + random.gauss(0, 3), y, 'wall'))
        
        # Central pillar/structure (like in the reference image)
        pillar_x, pillar_y = 0, 100
        pillar_r = 25
        for angle in range(0, 360, 5):
            rad = math.radians(angle)
            r = pillar_r + random.gauss(0, 2)
            env.append((pillar_x + r * math.cos(rad), 
                       pillar_y + r * math.sin(rad), 'pillar'))
        
        # Some smaller obstacles
        obstacles = [(-80, 60, 15), (90, 80, 12), (-50, 140, 18), (70, 150, 10)]
        for ox, oy, orad in obstacles:
            for angle in range(0, 360, 8):
                rad = math.radians(angle)
                r = orad + random.gauss(0, 1.5)
                env.append((ox + r * math.cos(rad), oy + r * math.sin(rad), 'obstacle'))
        
        # Ground points (scattered)
        for _ in range(200):
            x = random.uniform(-180, 180)
            y = random.uniform(10, 50)
            env.append((x, y, 'ground'))
            
        # Ceiling/top area
        for _ in range(150):
            x = random.uniform(-180, 180)
            y = random.uniform(160, 200)
            env.append((x, y, 'ceiling'))
        
        return env
    
    def _demo_scan(self, heading_deg: float) -> list:
        """Simulate a sonar scan in the demo environment."""
        hits = []
        
        # Convert heading to radians (0 = forward/up)
        base_angle = math.radians(heading_deg)
        
        # Sonar has a beam width - scan across it
        for beam_offset in np.linspace(-0.3, 0.3, 15):  # ~35 degree beam width
            angle = base_angle + beam_offset
            dx = math.sin(angle)
            dy = math.cos(angle)
            
            # Find closest hit
            min_dist = self.max_dist
            hit_type = None
            
            for (ex, ey, etype) in self.demo_env:
                # Distance from origin to this point along the ray
                # Project point onto ray
                dot = ex * dx + ey * dy
                if dot < 5:  # Behind us
                    continue
                    
                # Perpendicular distance from ray
                perp = abs(ex * dy - ey * dx)
                if perp < 8:  # Hit threshold
                    dist = math.sqrt(ex*ex + ey*ey)
                    if dist < min_dist:
                        min_dist = dist
                        hit_type = etype
            
            if min_dist < self.max_dist and hit_type:
                # Add some noise and scatter
                for _ in range(random.randint(2, 5)):
                    noise_angle = angle + random.gauss(0, 0.08)
                    noise_dist = min_dist + random.gauss(0, 3)
                    if noise_dist > 0:
                        hx = noise_dist * math.sin(noise_angle)
                        hy = noise_dist * math.cos(noise_angle)
                        hits.append((hx, hy, noise_dist))
        
        return hits
    
    def add_points(self, points_list):
        """Add multiple points from a scan."""
        now = time.time()
        for (x, y, d) in points_list:
            if 0 < d < self.max_dist:
                self.points.append((x, y, d, now))
        self.scan_count += 1
    
    def add_reading(self, heading_deg: float, dist_cm: float):
        """Add a single sonar reading and expand it into multiple points."""
        if dist_cm <= 0 or dist_cm > self.max_dist:
            return
            
        now = time.time()
        theta = math.radians(heading_deg)
        
        # Create multiple points to simulate beam width
        for _ in range(8):
            angle = theta + random.gauss(0, 0.15)
            d = dist_cm + random.gauss(0, 2)
            if d > 0:
                x = d * math.sin(angle)
                y = d * math.cos(angle)
                self.points.append((x, y, d, now))
        
        self.last_dist = dist_cm
        self.last_heading = heading_deg
        self.scan_count += 1
    
    def update_display(self):
        """Update the visualization."""
        if not self.points:
            return
            
        now = time.time()
        
        # Filter and extract points (fade old ones)
        xs, ys, dists = [], [], []
        cutoff = now - 45  # Keep points for 45 seconds
        
        for (x, y, d, t) in self.points:
            if t > cutoff:
                xs.append(x)
                ys.append(y)
                dists.append(d)
        
        if not xs:
            return
        
        # Update scatter plot
        offsets = np.column_stack([xs, ys])
        self.scatter.set_offsets(offsets)
        self.scatter.set_array(np.array(dists))
        
        # Vary point sizes slightly for depth effect (closer = slightly larger)
        sizes = 4 - (np.array(dists) / self.max_dist) * 2
        self.scatter.set_sizes(sizes)
        
        # Update HUD
        elapsed = now - self.start_time
        info = (f"SCAN: {self.scan_count:,}\n"
                f"PTS:  {len(xs):,}\n"
                f"TIME: {elapsed:.0f}s")
        self.info_text.set_text(info)
        
        # Distance readout
        dist_bar = "█" * min(20, int(self.last_dist / 10))
        self.dist_text.set_text(f"DIST: {self.last_dist:.0f}cm\n[{dist_bar}]")
    
    def run_demo(self):
        """Run in demo mode - simulates scanning environment."""
        print("╔════════════════════════════════════════╗")
        print("║     LIDAR VISUALIZER - DEMO MODE       ║")
        print("╠════════════════════════════════════════╣")
        print("║  Simulating sonar sweep of room        ║")
        print("║  Close window or Ctrl+C to exit        ║")
        print("╚════════════════════════════════════════╝")
        
        try:
            while plt.fignum_exists(self.fig.number):
                # Rotate scan
                self.demo_angle = (self.demo_angle + 3) % 360
                
                # Get simulated hits
                hits = self._demo_scan(self.demo_angle)
                self.add_points(hits)
                self.last_heading = self.demo_angle
                if hits:
                    self.last_dist = hits[0][2]
                
                self.update_display()
                plt.pause(0.03)
                
        except KeyboardInterrupt:
            print("\nExiting...")
    
    def run_serial(self, port: str, baud: int = 115200):
        """Run with live data from micro:bit."""
        print("╔════════════════════════════════════════╗")
        print("║     LIDAR VISUALIZER - LIVE MODE       ║")
        print("╠════════════════════════════════════════╣")
        print(f"║  Connecting to {port:.<24}║")
        print("║  Press A+B on micro:bit for SCAN mode  ║")
        print("╚════════════════════════════════════════╝")
        
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
            print(f"Connected! Listening...")
            
            no_data_count = 0
            
            while plt.fignum_exists(self.fig.number):
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                
                if line:
                    no_data_count = 0
                    try:
                        # Try to extract distance using regex (more robust than JSON)
                        import re
                        match = re.search(r'dist_cm["\s:]+(\d+)', line)
                        if match:
                            dist = float(match.group(1))
                            if dist > 0:
                                # Simulate rotation for visualization (robot is stationary)
                                self.last_heading = (self.last_heading + 3) % 360
                                self.add_reading(self.last_heading, dist)
                        elif line.startswith("{"):
                            # Fallback to JSON
                            msg = json.loads(line)
                            dist = float(msg.get("dist_cm", 0) or 0)
                            if dist > 0:
                                self.last_heading = (self.last_heading + 3) % 360
                                self.add_reading(self.last_heading, dist)
                    except Exception as e:
                        pass  # Silently ignore parse errors
                else:
                    no_data_count += 1
                    if no_data_count == 50:
                        print("No data received... Is the micro:bit in SCAN mode?")
                        print("Press A+B on the micro:bit, or press A to cycle modes")
                
                self.update_display()
                plt.pause(0.01)
                
        except serial.SerialException as e:
            print(f"\n⚠ Serial error: {e}")
            print("\nPossible fixes:")
            print("  1. Reconnect the micro:bit USB cable")
            print("  2. Close other programs using the port")
            print("  3. Check Windows Device Manager for the correct COM port")
            print("\nStarting DEMO mode instead...\n")
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
        description="LIDAR-style depth visualizer for micro:bit sonar rover"
    )
    ap.add_argument("--port", help="Serial port (e.g., COM3)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--demo", action="store_true", help="Run demo without hardware")
    ap.add_argument("--max-points", type=int, default=15000)
    ap.add_argument("--max-dist", type=float, default=250.0)
    args = ap.parse_args()
    
    viz = LidarVisualizer(max_points=args.max_points, max_dist=args.max_dist)
    
    if args.demo:
        viz.run_demo()
    elif args.port:
        viz.run_serial(args.port, args.baud)
    else:
        # Auto-detect or demo
        if HAS_SERIAL:
            ports = list(list_ports.comports())
            if ports:
                port = ports[0].device
                print(f"Auto-detected: {port}")
                viz.run_serial(port, args.baud)
                return 0
        
        print("No serial port found - running DEMO mode")
        viz.run_demo()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
