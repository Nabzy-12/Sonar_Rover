"""
3D Point Cloud Scanner
=======================
Creates a persistent 3D-like point cloud visualization.
Points accumulate over time as you scan around.
Looks like Scanner Sombre / LIDAR games.

Use with rotating rover OR manually rotate the device!
"""

import argparse
import math
import re
import time
import random
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


class PointCloudScanner:
    def __init__(self, max_points: int = 50000, max_dist: float = 300.0, fov: float = 90.0):
        self.max_points = max_points
        self.max_dist = max_dist
        self.fov = fov  # Field of view in degrees
        
        # Point cloud storage: list of (screen_x, screen_y, dist, timestamp)
        self.points = deque(maxlen=max_points)
        
        # Virtual camera angle (simulates looking around)
        self.camera_angle = 0.0
        self.camera_speed = 0.8  # degrees per reading
        
        # Screen dimensions
        self.width = 1200
        self.height = 700
        
        # Create colormap matching reference: blue -> cyan -> green -> yellow -> orange -> red
        colors = [
            [0.0, 0.0, 0.9],    # Deep blue (very close)
            [0.0, 0.3, 1.0],    # Blue
            [0.0, 0.7, 1.0],    # Cyan
            [0.0, 1.0, 0.7],    # Cyan-green
            [0.0, 1.0, 0.0],    # Green
            [0.4, 1.0, 0.0],    # Yellow-green
            [0.8, 0.9, 0.0],    # Yellow
            [1.0, 0.6, 0.0],    # Orange
            [1.0, 0.2, 0.0],    # Red-orange
            [0.8, 0.0, 0.0],    # Dark red (far)
        ]
        self.cmap = LinearSegmentedColormap.from_list("scanner", colors, N=512)
        
        # Setup dark figure
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 9), facecolor='black')
        self.ax = self.fig.add_subplot(111, facecolor='black')
        self.ax.set_xlim(0, self.width)
        self.ax.set_ylim(0, self.height)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Scatter plot for points
        self.scatter = self.ax.scatter([], [], s=[], c=[], cmap=self.cmap, 
                                        vmin=0, vmax=max_dist, alpha=0.85)
        
        # Scanner device overlay (bottom right like reference)
        self._draw_scanner()
        
        # HUD text
        self.dist_text = self.ax.text(self.width - 20, 40, '', color='#00ff00',
                                       fontsize=14, fontfamily='monospace',
                                       fontweight='bold', ha='right')
        self.points_text = self.ax.text(20, self.height - 30, '', color='#00ff00',
                                         fontsize=11, fontfamily='monospace')
        
        # Stats
        self.last_dist = 0
        self.scan_count = 0
        self.start_time = time.time()
        self.demo_mode = False
        
        # For smooth animation
        self.last_update = time.time()
        
    def _draw_scanner(self):
        """Draw scanner device in corner like reference images."""
        from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
        
        # Scanner body
        x, y = self.width - 180, 60
        body = FancyBboxPatch((x, y), 150, 80, boxstyle="round,pad=0.02,rounding_size=8",
                               facecolor='#1a0000', edgecolor='#440000', linewidth=2)
        self.ax.add_patch(body)
        
        # Lens
        lens = Circle((x + 35, y + 40), 20, facecolor='#001100', edgecolor='#00aa00', linewidth=2)
        self.ax.add_patch(lens)
        lens_inner = Circle((x + 35, y + 40), 8, facecolor='#003300', edgecolor='#00ff00', linewidth=1)
        self.ax.add_patch(lens_inner)
        
        # Screen
        screen = Rectangle((x + 70, y + 15), 60, 50, facecolor='#001a00', edgecolor='#004400', linewidth=1)
        self.ax.add_patch(screen)
        
    def add_reading(self, dist: float, heading_offset: float = 0):
        """Add a sonar reading and create multiple points from it."""
        if dist <= 0:
            return
            
        self.last_dist = dist
        self.scan_count += 1
        
        # Update virtual camera angle
        self.camera_angle += self.camera_speed + heading_offset
        
        # Convert sonar reading to screen coordinates
        # Simulate 3D projection: distance affects both position and spread
        
        # Horizontal position based on camera angle
        angle_rad = math.radians(self.camera_angle % 360)
        base_x = self.width / 2 + (self.width * 0.4) * math.sin(angle_rad)
        
        # Vertical position - closer objects appear lower/larger
        # This creates the "floor" effect seen in references
        depth_factor = dist / self.max_dist  # 0 = close, 1 = far
        base_y = self.height * (0.3 + 0.5 * depth_factor)  # Close = low, far = high
        
        # Point size - closer = bigger
        base_size = max(1, 8 - 6 * depth_factor)
        
        # Create multiple points with scatter to simulate beam width
        num_points = max(3, int(15 - 10 * depth_factor))  # More points for close objects
        
        now = time.time()
        
        for _ in range(num_points):
            # Add randomness to simulate sonar beam spread
            spread_x = random.gauss(0, 15 + 30 * depth_factor)
            spread_y = random.gauss(0, 20 + 40 * (1 - depth_factor))
            
            px = base_x + spread_x
            py = base_y + spread_y
            
            # Keep points on screen
            px = max(10, min(self.width - 10, px))
            py = max(10, min(self.height - 50, py))
            
            # Vary size slightly
            size = base_size * random.uniform(0.5, 1.5)
            
            # Vary distance slightly for color variation
            point_dist = dist + random.gauss(0, dist * 0.05)
            point_dist = max(1, min(self.max_dist, point_dist))
            
            self.points.append((px, py, point_dist, size, now))
    
    def update_display(self):
        """Update the visualization with all points."""
        if not self.points:
            return
            
        now = time.time()
        
        # Extract visible points (fade old ones)
        xs, ys, dists, sizes = [], [], [], []
        max_age = 60  # Points last 60 seconds
        
        for (px, py, d, s, t) in self.points:
            age = now - t
            if age < max_age:
                # Fade alpha with age
                age_factor = 1.0 - (age / max_age) * 0.5
                xs.append(px)
                ys.append(py)
                dists.append(d)
                sizes.append(s * age_factor)
        
        if not xs:
            return
        
        # Update scatter plot
        self.scatter.set_offsets(np.column_stack([xs, ys]))
        self.scatter.set_array(np.array(dists))
        self.scatter.set_sizes(np.array(sizes) ** 2)  # Size is area
        
        # Update HUD
        self.dist_text.set_text(f"DIST: {self.last_dist:.0f}cm")
        
        elapsed = now - self.start_time
        mode = "DEMO" if self.demo_mode else "LIVE"
        self.points_text.set_text(f"{mode} | Points: {len(xs):,} | Scans: {self.scan_count:,} | Time: {elapsed:.0f}s")
    
    def run_demo(self):
        """Run demo - simulates scanning a room/environment."""
        self.demo_mode = True
        print("╔═══════════════════════════════════════════╗")
        print("║     3D POINT CLOUD SCANNER - DEMO         ║")
        print("╠═══════════════════════════════════════════╣")
        print("║  Simulating environment scan              ║")
        print("║  Watch the point cloud build up!          ║")
        print("║  Close window to exit                     ║")
        print("╚═══════════════════════════════════════════╝")
        
        # Create demo environment - simulate a room with objects
        demo_t = 0
        
        try:
            while plt.fignum_exists(self.fig.number):
                demo_t += 0.02
                
                # Simulate scanning a room with varying distances
                # Base distance oscillates (like rotating in a room)
                angle = demo_t * 2
                
                # Room walls at varying distances
                wall_dist = 150 + 80 * math.sin(angle) + 40 * math.sin(angle * 2.3)
                
                # Random objects (furniture, etc)
                if random.random() < 0.15:
                    # Close object
                    dist = random.uniform(30, 80)
                elif random.random() < 0.1:
                    # Very close (hand, nearby object)
                    dist = random.uniform(10, 40)
                else:
                    # Background
                    dist = wall_dist + random.gauss(0, 20)
                
                dist = max(5, min(self.max_dist, dist))
                
                # Add extra points for denser cloud
                for _ in range(3):
                    self.add_reading(dist + random.gauss(0, 10))
                
                self.update_display()
                plt.pause(0.015)
                
        except KeyboardInterrupt:
            print("\nExiting...")
    
    def run_serial(self, port: str, baud: int = 115200):
        """Run with live serial data."""
        self.demo_mode = False
        print("╔═══════════════════════════════════════════╗")
        print("║     3D POINT CLOUD SCANNER - LIVE         ║")
        print("╠═══════════════════════════════════════════╣")
        print(f"║  Port: {port:<35}║")
        print("║  Rotate the rover or wave objects!        ║")
        print("║  Points will build up over time           ║")
        print("╚═══════════════════════════════════════════╝")
        
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.02)
            print("Connected! Scanning...")
            
            while plt.fignum_exists(self.fig.number):
                # Read multiple lines if available (faster processing)
                lines_read = 0
                while ser.in_waiting and lines_read < 10:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        match = re.search(r'dist_cm["\s:]+(\d+)', line)
                        if match:
                            dist = float(match.group(1))
                            if dist > 0:
                                self.add_reading(dist)
                                lines_read += 1
                
                self.update_display()
                plt.pause(0.01)
                
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            print("Starting DEMO mode...")
            self.run_demo()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            try:
                ser.close()
            except:
                pass


def main():
    ap = argparse.ArgumentParser(description="3D Point Cloud Scanner - LIDAR-style visualization")
    ap.add_argument("--port", help="Serial port (e.g., COM3)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--demo", action="store_true", help="Run demo mode")
    ap.add_argument("--max-points", type=int, default=50000)
    ap.add_argument("--max-dist", type=float, default=300.0)
    args = ap.parse_args()
    
    scanner = PointCloudScanner(max_points=args.max_points, max_dist=args.max_dist)
    
    if args.demo:
        scanner.run_demo()
    elif args.port:
        scanner.run_serial(args.port, args.baud)
    else:
        if HAS_SERIAL:
            ports = list(list_ports.comports())
            if ports:
                scanner.run_serial(ports[0].device, args.baud)
                return 0
        print("No serial port - running demo")
        scanner.run_demo()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
