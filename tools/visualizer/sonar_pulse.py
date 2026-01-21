"""
SONAR PULSE - Live Distance Visualizer
=======================================
A pulsing blob that reacts to distance in real-time.
- CLOSE: Big, red, intense
- FAR: Small, blue, calm

No scrolling - just pure, immediate depth feedback!
"""

import argparse
import math
import random
import re
import sys
import time

try:
    import pygame
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame-ce", "-q"])
    import pygame

try:
    import serial
    from serial.tools import list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class SonarPulse:
    def __init__(self, width: int = 1200, height: int = 800, max_dist: float = 150.0):
        pygame.init()
        pygame.display.set_caption("SONAR PULSE")
        
        self.width = width
        self.height = height
        self.max_dist = max_dist
        self.center_x = width // 2
        self.center_y = height // 2
        
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.font_big = pygame.font.SysFont("Consolas", 48, bold=True)
        self.font_huge = pygame.font.SysFont("Consolas", 72, bold=True)
        
        # Persistent points - they stay in place!
        self.points = []  # (x, y, base_dist_from_center)
        self.max_points = 50000
        self.points_generated = False
        
        # Current state
        self.current_dist = 100.0
        self.target_dist = 100.0  # For smooth interpolation
        self.state = "SCANNING"
        
        # Smoothing - light filter, no outlier rejection (was causing lock-up)
        self.reading_history = []
        self.history_size = 5
        
        # Distance history for graph
        self.dist_graph = []  # (time, raw_dist, smoothed_dist)
        self.graph_duration = 10.0  # Show last 10 seconds
        
        # Stats
        self.start_time = time.time()
        self.scan_count = 0
        self.fps = 60
        
        # Generate initial point cloud
        self._generate_points()
        
        # Build color gradient
        self.colors = self._build_gradient()
        
    def _build_gradient(self) -> list:
        """RED (close) -> Orange -> Yellow -> Green -> Cyan -> BLUE (far)"""
        colors = []
        keypoints = [
            (0.0, (255, 30, 30)),     # Bright RED - very close
            (0.12, (255, 80, 0)),     # Red-orange
            (0.25, (255, 160, 0)),    # Orange
            (0.38, (255, 230, 0)),    # Yellow
            (0.50, (150, 255, 50)),   # Yellow-green
            (0.62, (0, 255, 120)),    # Green
            (0.75, (0, 230, 200)),    # Cyan
            (0.88, (0, 150, 255)),    # Light blue
            (1.0, (30, 60, 180)),     # Deep blue - far
        ]
        
        for i in range(256):
            t = i / 255.0
            for j in range(len(keypoints) - 1):
                t1, c1 = keypoints[j]
                t2, c2 = keypoints[j + 1]
                if t1 <= t <= t2:
                    local_t = (t - t1) / (t2 - t1) if t2 > t1 else 0
                    r = int(c1[0] + (c2[0] - c1[0]) * local_t)
                    g = int(c1[1] + (c2[1] - c1[1]) * local_t)
                    b = int(c1[2] + (c2[2] - c1[2]) * local_t)
                    colors.append((r, g, b))
                    break
            else:
                colors.append(keypoints[-1][1])
        return colors
    
    def _generate_points(self):
        """Generate a dense circular point cloud."""
        self.points = []
        
        # Create points in a large circular area
        max_radius = min(self.width, self.height) * 0.45
        
        for _ in range(self.max_points):
            # Random point in circle with density falloff from center
            angle = random.uniform(0, 2 * math.pi)
            # Use square root for uniform distribution, then bias toward center
            r = max_radius * (random.random() ** 0.7)
            
            x = self.center_x + r * math.cos(angle)
            y = self.center_y + r * math.sin(angle) * 0.85  # Slight vertical squash
            
            # Store normalized distance from center (0-1)
            norm_dist = r / max_radius
            
            self.points.append((x, y, norm_dist))
        
        self.points_generated = True
    
    def add_reading(self, dist: float, state: str = ""):
        """Update with new sonar reading - simple median filter only."""
        self.state = state if state else "SCANNING"
        self.scan_count += 1
        
        now = time.time()
        raw_dist = dist  # Keep raw for graph
        
        # Clamp to valid range
        dist = max(2, min(dist, self.max_dist * 1.1))
        
        # Add to history
        self.reading_history.append(dist)
        if len(self.reading_history) > self.history_size:
            self.reading_history.pop(0)
        
        # Simple median - no outlier rejection (that was breaking it)
        sorted_history = sorted(self.reading_history)
        smoothed = sorted_history[len(sorted_history) // 2]
        
        self.target_dist = smoothed
        
        # Store for graph
        self.dist_graph.append((now, raw_dist, smoothed))
        # Trim old graph data
        cutoff = now - self.graph_duration
        self.dist_graph = [(t, r, s) for t, r, s in self.dist_graph if t > cutoff]
    
    def update(self, dt: float):
        """Smooth interpolation toward target distance."""
        # Smooth follow - faster when far from target
        diff = self.target_dist - self.current_dist
        self.current_dist += diff * min(1.0, dt * 8)
    
    def render(self):
        """Render the visualization."""
        self.screen.fill((8, 8, 20))  # Dark background
        
        # Calculate visibility threshold based on distance
        # Close = more points visible (bigger blob)
        # Far = fewer points visible (smaller blob)
        dist_ratio = self.current_dist / self.max_dist  # 0 = close, 1 = far
        visibility_threshold = 1.0 - dist_ratio * 0.85  # Close = 1.0, Far = 0.15
        
        # Get base color for current distance
        color_idx = int(min(1.0, max(0.0, dist_ratio)) * 255)
        base_color = self.colors[color_idx]
        
        # Draw points
        for (x, y, norm_dist) in self.points:
            # Point is visible if its distance from center < threshold
            if norm_dist < visibility_threshold:
                # Intensity based on how "inside" the blob this point is
                intensity = 1.0 - (norm_dist / visibility_threshold) * 0.4
                
                # Add slight color variation based on position
                color_variation = norm_dist * 0.3
                varied_idx = int(min(255, max(0, color_idx + color_variation * 50)))
                point_color = self.colors[varied_idx]
                
                # Apply intensity
                r = int(point_color[0] * intensity)
                g = int(point_color[1] * intensity)
                b = int(point_color[2] * intensity)
                
                # Point size - slightly larger near edge for glow effect
                size = 2 if norm_dist > visibility_threshold * 0.7 else 3
                
                pygame.draw.circle(self.screen, (r, g, b), (int(x), int(y)), size)
        
        # Draw UI
        self._draw_ui(base_color)
        
        pygame.display.flip()
    
    def _draw_ui(self, current_color):
        """Draw HUD elements."""
        # Big distance display at top
        dist_text = self.font_huge.render(f"{self.current_dist:.0f}", True, current_color)
        self.screen.blit(dist_text, (self.width // 2 - dist_text.get_width() // 2, 30))
        
        cm_text = self.font_big.render("cm", True, (100, 100, 100))
        self.screen.blit(cm_text, (self.width // 2 - cm_text.get_width() // 2, 100))
        
        # State indicator
        state_color = (255, 100, 100) if self.state == "REVERSE" else \
                      (255, 255, 100) if self.state == "WAIT" else \
                      (100, 255, 100)
        state_text = self.font.render(self.state, True, state_color)
        self.screen.blit(state_text, (self.width // 2 - state_text.get_width() // 2, 160))
        
        # Stats (bottom left)
        elapsed = time.time() - self.start_time
        stats = [
            f"SCANS: {self.scan_count:,}",
            f"TIME: {elapsed:.0f}s",
            f"FPS: {self.fps:.0f}",
        ]
        y = self.height - 80
        for line in stats:
            text = self.font.render(line, True, (60, 80, 60))
            self.screen.blit(text, (15, y))
            y += 22
        
        # Distance scale (right side)
        self._draw_scale()
        
        # Distance graph (bottom right)
        self._draw_graph()
        
        # Controls
        controls = self.font.render("SPACE: Regenerate points | ESC: Quit", True, (50, 50, 50))
        self.screen.blit(controls, (self.width // 2 - controls.get_width() // 2, self.height - 25))
    
    def _draw_scale(self):
        """Draw distance color scale."""
        x = self.width - 45
        y = 150
        h = 200
        w = 25
        
        # Gradient bar
        for i in range(h):
            t = i / h
            color = self.colors[int(t * 255)]
            pygame.draw.line(self.screen, color, (x, y + i), (x + w, y + i))
        
        # Border
        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, w, h), 1)
        
        # Labels
        close_label = self.font.render("CLOSE", True, self.colors[0])
        far_label = self.font.render("FAR", True, self.colors[-1])
        self.screen.blit(close_label, (x - 5, y - 25))
        self.screen.blit(far_label, (x + 5, y + h + 8))
        
        # Current position marker
        dist_ratio = self.current_dist / self.max_dist
        marker_y = y + int(dist_ratio * h)
        pygame.draw.polygon(self.screen, (255, 255, 255), [
            (x - 8, marker_y),
            (x - 2, marker_y - 5),
            (x - 2, marker_y + 5),
        ])
    
    def _draw_graph(self):
        """Draw distance history graph."""
        if len(self.dist_graph) < 2:
            return
        
        # Graph area (bottom right corner)
        gx, gy = self.width - 320, self.height - 150
        gw, gh = 300, 120
        
        # Background
        pygame.draw.rect(self.screen, (20, 25, 35), (gx, gy, gw, gh))
        pygame.draw.rect(self.screen, (50, 60, 70), (gx, gy, gw, gh), 1)
        
        # Labels
        title = self.font.render("DISTANCE (last 10s)", True, (80, 100, 80))
        self.screen.blit(title, (gx + 5, gy - 20))
        
        max_label = self.font.render(f"{self.max_dist:.0f}", True, (60, 60, 60))
        min_label = self.font.render("0", True, (60, 60, 60))
        self.screen.blit(max_label, (gx - 30, gy))
        self.screen.blit(min_label, (gx - 15, gy + gh - 15))
        
        # Get time range
        now = time.time()
        t_min = now - self.graph_duration
        
        # Draw raw data (gray) and smoothed (colored)
        raw_points = []
        smooth_points = []
        
        for (t, raw, smooth) in self.dist_graph:
            x = gx + int((t - t_min) / self.graph_duration * gw)
            
            # Raw (gray dots)
            raw_y = gy + gh - int(min(raw, self.max_dist) / self.max_dist * gh)
            raw_points.append((x, raw_y))
            
            # Smoothed (line)
            smooth_y = gy + gh - int(min(smooth, self.max_dist) / self.max_dist * gh)
            smooth_points.append((x, smooth_y))
        
        # Draw raw as small dots
        for (x, y) in raw_points:
            pygame.draw.circle(self.screen, (80, 80, 80), (x, y), 2)
        
        # Draw smoothed as line
        if len(smooth_points) > 1:
            # Color based on current distance
            color_idx = int(min(1.0, max(0.0, self.current_dist / self.max_dist)) * 255)
            line_color = self.colors[color_idx]
            pygame.draw.lines(self.screen, line_color, False, smooth_points, 2)
        
        # Legend
        pygame.draw.circle(self.screen, (80, 80, 80), (gx + gw - 80, gy + gh + 12), 3)
        raw_lbl = self.font.render("raw", True, (80, 80, 80))
        self.screen.blit(raw_lbl, (gx + gw - 70, gy + gh + 5))
        
        pygame.draw.line(self.screen, (200, 150, 50), (gx + gw - 40, gy + gh + 12), (gx + gw - 20, gy + gh + 12), 2)
        sm_lbl = self.font.render("smooth", True, (150, 150, 100))
        self.screen.blit(sm_lbl, (gx + gw - 18, gy + gh + 5))
    
    def handle_events(self) -> bool:
        """Handle input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self._generate_points()
        return True
    
    def run_serial(self, port: str, baud: int = 115200):
        """Run with live sonar data."""
        print(f"╔{'═'*50}╗")
        print(f"║{'SONAR PULSE - LIVE':^50}║")
        print(f"╠{'═'*50}╣")
        print(f"║  Port: {port:<42}║")
        print(f"║  Move closer = BIGGER + REDDER                  ║")
        print(f"║  Move away   = SMALLER + BLUER                  ║")
        print(f"╚{'═'*50}╝")
        
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=0.01)
            print("Connected!")
            
            running = True
            last_time = time.time()
            frame_count = 0
            fps_timer = time.time()
            
            while running:
                running = self.handle_events()
                
                now = time.time()
                dt = now - last_time
                last_time = now
                
                # Read serial
                while ser.in_waiting:
                    try:
                        line = ser.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            dist_match = re.search(r'dist_cm["\s:]+(\d+)', line)
                            state_match = re.search(r'state["\s:]+(\w+)', line)
                            if dist_match:
                                dist = float(dist_match.group(1))
                                state = state_match.group(1) if state_match else ""
                                self.add_reading(dist, state)
                    except:
                        pass
                
                self.update(dt)
                self.render()
                
                # FPS
                frame_count += 1
                if now - fps_timer > 1.0:
                    self.fps = frame_count / (now - fps_timer)
                    frame_count = 0
                    fps_timer = now
                
                self.clock.tick(60)
                
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.run_demo()
        finally:
            pygame.quit()
    
    def run_demo(self):
        """Demo mode."""
        print(f"╔{'═'*50}╗")
        print(f"║{'SONAR PULSE - DEMO':^50}║")
        print(f"╠{'═'*50}╣")
        print(f"║  Watch the blob pulse with simulated distance   ║")
        print(f"╚{'═'*50}╝")
        
        running = True
        last_time = time.time()
        frame_count = 0
        fps_timer = time.time()
        
        sim_dist = 80.0
        sim_velocity = -20.0
        sim_state = "DRIVE"
        
        while running:
            running = self.handle_events()
            
            now = time.time()
            dt = now - last_time
            last_time = now
            
            # Simulate rover
            sim_dist += sim_velocity * dt
            
            if sim_dist < 5:
                sim_state = "REVERSE"
                sim_velocity = 25.0
            elif sim_dist > 20 and sim_state == "REVERSE":
                sim_state = "WAIT"
                sim_velocity = 0
            elif sim_state == "WAIT" and random.random() < 0.03:
                sim_state = "DRIVE"
                sim_velocity = -20.0
            elif sim_dist > 130:
                sim_velocity = -20.0
            
            self.add_reading(max(3, sim_dist + random.gauss(0, 1)), sim_state)
            
            self.update(dt)
            self.render()
            
            frame_count += 1
            if now - fps_timer > 1.0:
                self.fps = frame_count / (now - fps_timer)
                frame_count = 0
                fps_timer = now
            
            self.clock.tick(60)
        
        pygame.quit()


def main():
    ap = argparse.ArgumentParser(description="Sonar Pulse Visualizer")
    ap.add_argument("--port", help="Serial port (e.g., COM3)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    
    viz = SonarPulse()
    
    if args.demo:
        viz.run_demo()
    elif args.port:
        viz.run_serial(args.port, args.baud)
    else:
        if HAS_SERIAL:
            ports = list(list_ports.comports())
            if ports:
                viz.run_serial(ports[0].device, args.baud)
                return
        viz.run_demo()


if __name__ == "__main__":
    main()
