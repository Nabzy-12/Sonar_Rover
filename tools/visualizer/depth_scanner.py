"""
First-Person Depth Scanner
===========================
Shows a first-person view like LIDAR/depth cameras.
Builds up a depth image as the scanner sweeps.
Blue = close, Red = far

Similar to the reference images with that immersive depth view.
"""

import argparse
import re
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


class DepthScanner:
    def __init__(self, width: int = 400, height: int = 300, max_dist: float = 200.0):
        self.width = width
        self.height = height
        self.max_dist = max_dist
        
        # Depth buffer - stores distance values
        # Initialize with max_dist (far/unknown)
        self.depth_buffer = np.full((height, width), max_dist, dtype=np.float32)
        
        # Color buffer for display
        self.display = np.zeros((height, width, 3), dtype=np.float32)
        
        # Scan position (sweeps left to right)
        self.scan_x = 0
        self.scan_speed = 3  # pixels per reading
        
        # Create depth colormap: blue -> cyan -> green -> yellow -> red
        self.colors = np.array([
            [0.0, 0.0, 1.0],    # Blue (close)
            [0.0, 0.5, 1.0],    # Cyan-blue
            [0.0, 1.0, 1.0],    # Cyan
            [0.0, 1.0, 0.5],    # Cyan-green
            [0.0, 1.0, 0.0],    # Green
            [0.5, 1.0, 0.0],    # Yellow-green
            [1.0, 1.0, 0.0],    # Yellow
            [1.0, 0.5, 0.0],    # Orange
            [1.0, 0.0, 0.0],    # Red (far)
        ])
        
        # Setup figure
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(14, 8), facecolor='black')
        self.ax.set_facecolor('black')
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05)
        
        # Image display
        self.im = self.ax.imshow(self.display, aspect='auto', interpolation='bilinear')
        
        # Scan line indicator
        self.scan_line = self.ax.axvline(x=0, color='#00ff00', linewidth=2, alpha=0.7)
        
        # HUD
        self.title = self.ax.set_title("DEPTH SCANNER - LIVE", color='#00ff00', 
                                        fontsize=14, fontweight='bold')
        
        self.info_text = self.ax.text(10, height - 20, '', color='#00ff00', 
                                       fontsize=11, fontfamily='monospace')
        
        self.dist_text = self.ax.text(width - 100, height - 20, '', color='#00ffff',
                                       fontsize=12, fontfamily='monospace', fontweight='bold')
        
        # Stats
        self.last_dist = 0
        self.scan_count = 0
        self.start_time = time.time()
        self.demo_mode = False
        
    def dist_to_color(self, dist: float) -> np.ndarray:
        """Convert distance to RGB color."""
        # Normalize distance to 0-1
        t = np.clip(dist / self.max_dist, 0, 1)
        
        # Map to color index
        idx = t * (len(self.colors) - 1)
        idx_low = int(idx)
        idx_high = min(idx_low + 1, len(self.colors) - 1)
        frac = idx - idx_low
        
        # Interpolate between colors
        color = self.colors[idx_low] * (1 - frac) + self.colors[idx_high] * frac
        return color
    
    def add_reading(self, dist: float):
        """Add a sonar reading at current scan position."""
        if dist <= 0:
            dist = self.max_dist
        
        self.last_dist = dist
        self.scan_count += 1
        
        # Get color for this distance
        color = self.dist_to_color(dist)
        
        # Calculate vertical spread based on distance (closer = taller)
        # This creates the "depth" effect
        spread = int(self.height * 0.8 * (1 - dist / self.max_dist) + self.height * 0.1)
        spread = max(20, min(self.height - 20, spread))
        
        center_y = self.height // 2
        
        # Draw vertical column at scan position with some thickness
        for dx in range(self.scan_speed):
            x = (self.scan_x + dx) % self.width
            
            # Create vertical gradient (brighter in center)
            for y in range(self.height):
                dist_from_center = abs(y - center_y)
                
                if dist_from_center < spread // 2:
                    # Inside the "object" - full color with slight gradient
                    intensity = 1.0 - (dist_from_center / (spread // 2)) * 0.3
                    self.display[y, x] = color * intensity
                    self.depth_buffer[y, x] = dist
                else:
                    # Outside - fade to black (far/empty)
                    fade = max(0, 1 - (dist_from_center - spread // 2) / 50)
                    self.display[y, x] = color * fade * 0.3
                    
            # Add some noise/scatter for realism
            for _ in range(5):
                scatter_y = center_y + int(np.random.normal(0, spread // 3))
                scatter_y = max(0, min(self.height - 1, scatter_y))
                noise_color = color * np.random.uniform(0.7, 1.0)
                self.display[scatter_y, x] = np.maximum(self.display[scatter_y, x], noise_color)
        
        # Advance scan position
        self.scan_x = (self.scan_x + self.scan_speed) % self.width
        
        # Slight decay of old pixels (creates trail effect)
        self.display *= 0.995
    
    def update_display(self):
        """Update the visualization."""
        self.im.set_array(np.clip(self.display, 0, 1))
        self.scan_line.set_xdata([self.scan_x, self.scan_x])
        
        elapsed = time.time() - self.start_time
        mode = "DEMO" if self.demo_mode else "LIVE"
        self.info_text.set_text(f"MODE: {mode}  SCANS: {self.scan_count:,}  TIME: {elapsed:.0f}s")
        self.dist_text.set_text(f"DIST: {self.last_dist:.0f}cm")
    
    def run_demo(self):
        """Run demo mode with simulated environment."""
        self.demo_mode = True
        self.title.set_text("DEPTH SCANNER - DEMO MODE")
        print("Running DEMO mode - simulating depth scanner")
        print("Close window to exit")
        
        # Create a simulated environment
        demo_time = 0
        
        try:
            while plt.fignum_exists(self.fig.number):
                # Simulate varying distances (like scanning a room)
                demo_time += 0.05
                
                # Create interesting patterns
                base = 80 + 40 * np.sin(demo_time * 0.5)  # Slow wave
                variation = 30 * np.sin(demo_time * 2)     # Faster detail
                noise = np.random.normal(0, 5)             # Noise
                
                # Occasional "objects" (closer readings)
                if np.random.random() < 0.1:
                    dist = np.random.uniform(20, 60)
                else:
                    dist = base + variation + noise
                
                dist = max(5, min(self.max_dist, dist))
                
                self.add_reading(dist)
                self.update_display()
                plt.pause(0.02)
                
        except KeyboardInterrupt:
            print("\nExiting...")
    
    def run_serial(self, port: str, baud: int = 115200):
        """Run with live serial data."""
        self.demo_mode = False
        print(f"Connecting to {port}...")
        
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.05)
            print("Connected! Move objects in front of the sonar to see depth!")
            
            while plt.fignum_exists(self.fig.number):
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                
                if line:
                    # Extract distance using regex
                    match = re.search(r'dist_cm["\s:]+(\d+)', line)
                    if match:
                        dist = float(match.group(1))
                        self.add_reading(dist)
                
                self.update_display()
                plt.pause(0.005)
                
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            print("Running DEMO mode instead...")
            self.run_demo()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            try:
                ser.close()
            except:
                pass


def main():
    ap = argparse.ArgumentParser(description="First-person depth scanner visualization")
    ap.add_argument("--port", help="Serial port (e.g., COM3)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--demo", action="store_true", help="Run demo mode")
    ap.add_argument("--width", type=int, default=500)
    ap.add_argument("--height", type=int, default=350)
    ap.add_argument("--max-dist", type=float, default=200.0)
    args = ap.parse_args()
    
    scanner = DepthScanner(width=args.width, height=args.height, max_dist=args.max_dist)
    
    if args.demo:
        scanner.run_demo()
    elif args.port:
        scanner.run_serial(args.port, args.baud)
    else:
        # Auto-detect
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
