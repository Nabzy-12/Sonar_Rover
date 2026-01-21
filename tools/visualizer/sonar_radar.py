#!/usr/bin/env python3
"""
SONAR RADAR - Relative View Display
=====================================
Shows what's in front of the rover RIGHT NOW.
Forward is always UP - no angle tracking needed!

Turn the rover physically to scan around.
Points fade over time to show recent history.

Controls:
  WASD - Drive the rover
  SPACE - Stop
  C - Clear points
  R - Reset position
"""

import pygame
import serial
import serial.tools.list_ports
import math
import time
import argparse
import json
from collections import deque

# Display settings
WIDTH, HEIGHT = 900, 700
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT - 100  # Rover at bottom center
BG_COLOR = (15, 15, 25)
MAX_RANGE = 200  # cm
PIXELS_PER_CM = 2.5

# Point settings
MAX_POINTS = 500
POINT_LIFETIME = 8.0  # seconds before point fades completely

class RadarPoint:
    def __init__(self, distance, timestamp):
        self.distance = distance
        self.timestamp = timestamp
    
    def age(self):
        return time.time() - self.timestamp
    
    def alpha(self):
        # Fade from 1.0 to 0.0 over lifetime
        return max(0, 1.0 - (self.age() / POINT_LIFETIME))

class SonarRadar:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.points = deque(maxlen=MAX_POINTS)
        self.current_distance = 0
        self.state = "STOP"
        self.running = True
        self.last_reading_time = 0
        self.sweep_angle = 0  # For visual sweep effect
        
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(0.5)
            self.ser.reset_input_buffer()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, cmd):
        if self.ser:
            try:
                self.ser.write(f"{cmd}\n".encode())
            except:
                pass
    
    def read_data(self):
        if not self.ser or not self.ser.in_waiting:
            return
        
        try:
            line = self.ser.readline().decode().strip()
            if line.startswith('{'):
                data = json.loads(line)
                self.current_distance = data.get('d', 0)
                self.state = data.get('s', 'STOP')
                
                # Only add points when we get valid readings
                if 2 < self.current_distance < MAX_RANGE:
                    self.points.append(RadarPoint(self.current_distance, time.time()))
                    self.last_reading_time = time.time()
        except:
            pass
    
    def draw_radar_grid(self, screen, font):
        # Draw concentric range circles
        for r in range(50, MAX_RANGE + 1, 50):
            radius = int(r * PIXELS_PER_CM)
            # Darker circles
            pygame.draw.circle(screen, (30, 40, 50), (CENTER_X, CENTER_Y), radius, 1)
            # Range label
            label = font.render(f"{r}cm", True, (60, 70, 80))
            screen.blit(label, (CENTER_X + 5, CENTER_Y - radius - 15))
        
        # Draw radial lines (like spokes)
        for angle_deg in range(-90, 91, 30):
            angle_rad = math.radians(angle_deg - 90)  # -90 so 0 is up
            end_x = CENTER_X + math.cos(angle_rad) * MAX_RANGE * PIXELS_PER_CM
            end_y = CENTER_Y + math.sin(angle_rad) * MAX_RANGE * PIXELS_PER_CM
            pygame.draw.line(screen, (25, 35, 45), (CENTER_X, CENTER_Y), (end_x, end_y), 1)
        
        # Forward direction indicator (center line going up)
        pygame.draw.line(screen, (0, 80, 0), (CENTER_X, CENTER_Y), (CENTER_X, CENTER_Y - MAX_RANGE * PIXELS_PER_CM), 2)
    
    def draw_sweep_beam(self, screen):
        # Animated sweep beam effect
        self.sweep_angle += 2
        if self.sweep_angle > 30:
            self.sweep_angle = -30
        
        angle_rad = math.radians(self.sweep_angle - 90)
        beam_length = MAX_RANGE * PIXELS_PER_CM
        
        # Draw beam with gradient
        for i in range(10):
            alpha = 30 - i * 3
            angle_offset = math.radians(i * 0.5)
            end_x = CENTER_X + math.cos(angle_rad - angle_offset) * beam_length
            end_y = CENTER_Y + math.sin(angle_rad - angle_offset) * beam_length
            pygame.draw.line(screen, (0, alpha, 0), (CENTER_X, CENTER_Y), (end_x, end_y), 1)
    
    def draw_points(self, screen):
        # Remove expired points
        current_time = time.time()
        while self.points and self.points[0].age() > POINT_LIFETIME:
            self.points.popleft()
        
        # Draw points - all directly ahead (forward = up)
        for point in self.points:
            alpha = point.alpha()
            if alpha <= 0:
                continue
            
            # Distance determines Y position (up from rover)
            px = CENTER_X
            py = CENTER_Y - int(point.distance * PIXELS_PER_CM)
            
            # Color based on distance and age
            if point.distance < 30:
                base_color = (255, 50, 50)  # Red = close
            elif point.distance < 80:
                base_color = (255, 180, 0)  # Orange = medium
            else:
                base_color = (50, 255, 50)  # Green = far
            
            color = tuple(int(c * alpha) for c in base_color)
            size = max(2, int(5 * alpha))
            pygame.draw.circle(screen, color, (px, py), size)
    
    def draw_current_ping(self, screen, font):
        """Draw the current sonar ping prominently"""
        if self.current_distance > 2 and self.current_distance < MAX_RANGE:
            py = CENTER_Y - int(self.current_distance * PIXELS_PER_CM)
            
            # Bright ping indicator
            pygame.draw.circle(screen, (255, 255, 255), (CENTER_X, py), 8)
            pygame.draw.circle(screen, (0, 255, 255), (CENTER_X, py), 6)
            
            # Distance line
            pygame.draw.line(screen, (0, 150, 150), (CENTER_X, CENTER_Y), (CENTER_X, py), 2)
            
            # Label
            label = font.render(f"{self.current_distance}cm", True, (0, 255, 255))
            screen.blit(label, (CENTER_X + 15, py - 8))
    
    def draw_rover(self, screen):
        """Draw the rover at bottom center"""
        # Rover body
        pygame.draw.polygon(screen, (100, 150, 255), [
            (CENTER_X, CENTER_Y - 20),      # Nose (pointing up)
            (CENTER_X - 12, CENTER_Y + 10),  # Left rear
            (CENTER_X + 12, CENTER_Y + 10),  # Right rear
        ])
        # Sonar cone indicator
        pygame.draw.polygon(screen, (50, 80, 50), [
            (CENTER_X, CENTER_Y - 20),
            (CENTER_X - 40, CENTER_Y - 100),
            (CENTER_X + 40, CENTER_Y - 100),
        ], 1)
    
    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SONAR RADAR")
        clock = pygame.time.Clock()
        
        font = pygame.font.Font(None, 24)
        big_font = pygame.font.Font(None, 48)
        
        # Key states for movement
        keys_held = {'w': False, 'a': False, 's': False, 'd': False}
        
        print("Connecting to", self.port + "...")
        if not self.connect():
            print("Failed to connect!")
            return
        print("Connected! Forward is always UP.")
        print("Turn the rover physically to look around.")
        
        while self.running:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_c:
                        self.points.clear()
                    elif event.key == pygame.K_SPACE:
                        self.send_command("X")
                        keys_held = {k: False for k in keys_held}
                    # Movement keys
                    elif event.key == pygame.K_w and not keys_held['w']:
                        keys_held['w'] = True
                        self.send_command("F")
                    elif event.key == pygame.K_s and not keys_held['s']:
                        keys_held['s'] = True
                        self.send_command("B")
                    elif event.key == pygame.K_a and not keys_held['a']:
                        keys_held['a'] = True
                        self.send_command("L")
                    elif event.key == pygame.K_d and not keys_held['d']:
                        keys_held['d'] = True
                        self.send_command("R")
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_w and keys_held['w']:
                        keys_held['w'] = False
                        self.send_command("SF")
                    elif event.key == pygame.K_s and keys_held['s']:
                        keys_held['s'] = False
                        self.send_command("SF")
                    elif event.key == pygame.K_a and keys_held['a']:
                        keys_held['a'] = False
                        self.send_command("ST")
                    elif event.key == pygame.K_d and keys_held['d']:
                        keys_held['d'] = False
                        self.send_command("ST")
            
            # Read serial data
            self.read_data()
            
            # Draw
            screen.fill(BG_COLOR)
            
            # Radar elements
            self.draw_radar_grid(screen, font)
            self.draw_sweep_beam(screen)
            self.draw_points(screen)
            self.draw_current_ping(screen, font)
            self.draw_rover(screen)
            
            # Status bar at top
            status_color = {
                'STOP': (100, 100, 100),
                'FWD': (0, 255, 0),
                'REV': (255, 150, 0),
                'LEFT': (255, 0, 255),
                'RIGHT': (255, 0, 255),
            }.get(self.state[:3] if self.state else 'STO', (100, 100, 100))
            
            # Distance display
            dist_text = big_font.render(f"{self.current_distance}cm", True, (0, 255, 255))
            screen.blit(dist_text, (20, 15))
            
            # State
            state_text = font.render(self.state, True, status_color)
            screen.blit(state_text, (150, 25))
            
            # Points count
            points_text = font.render(f"Points: {len(self.points)}", True, (100, 100, 100))
            screen.blit(points_text, (WIDTH - 100, 15))
            
            # Instructions
            help_text = font.render("WASD: Move   SPACE: Stop   C: Clear   Turn rover to scan around", True, (80, 80, 80))
            screen.blit(help_text, (20, HEIGHT - 30))
            
            pygame.display.flip()
            clock.tick(60)
        
        if self.ser:
            self.send_command("X")
            self.ser.close()
        pygame.quit()

def main():
    parser = argparse.ArgumentParser(description='Sonar Radar Display')
    parser.add_argument('--port', '-p', default='COM3', help='Serial port')
    args = parser.parse_args()
    
    radar = SonarRadar(args.port)
    radar.run()

if __name__ == "__main__":
    main()
