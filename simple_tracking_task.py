import time
import numpy as np
import pyglet
from pyglet.window import key
import math
import random
import pygame

class SimpleReticle:
    def __init__(self, window_width, window_height, target_proportion=0.25):
        self.window_width = window_width
        self.window_height = window_height
        self.center_x = window_width // 2
        self.center_y = window_height // 2

        self.target_radius = 25

        self.cursor_x = 0
        self.cursor_y = 0
        
        # Colors
        self.background_color = (255, 255, 255)
        self.target_color = (220, 220, 220)
        self.target_border_color = (180, 180, 180)
        self.cursor_color = (0, 0, 255)
        self.cursor_outside_color = (255, 0, 0)
        self.axis_color = (100, 100, 100)

        self.batch = pyglet.graphics.Batch()

        self.target_border = pyglet.shapes.Circle(
            self.center_x, self.center_y, self.target_radius+1,
            color=self.target_border_color, batch=self.batch
        )

        self.target_circle = pyglet.shapes.Circle(
            self.center_x, self.center_y, self.target_radius,
            color=self.target_color, batch=self.batch
        )

        self.h_axis = pyglet.shapes.Line(
            0, self.center_y, self.window_width, self.center_y,
            width=1, color=self.axis_color, batch=self.batch
        )

        self.v_axis = pyglet.shapes.Line(
            self.center_x, 0, self.center_x, self.window_height,
            width=1, color=self.axis_color, batch=self.batch
        )

        self.cursor_circle = pyglet.shapes.Circle(
            self.center_x, self.center_y, 3,  # 3px cursor radius
            color=self.cursor_color, batch=self.batch
        )

        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = 0.98

        initial_angle = random.uniform(0, 2 * math.pi)
        initial_x = 180 * math.cos(initial_angle)
        initial_y = 180 * math.sin(initial_angle)
        
        self.cursor_position = (initial_x, initial_y)
        self.update_cursor_position(*self.cursor_position)

    def update(self, dt, joystick_x=0, speed_factor = 3, joystick_y=0, jitter_val = 0.1):

        jitter_x = np.random.normal(0, jitter_val)
        jitter_y = np.random.normal(0, jitter_val)

        target_vx = joystick_x * speed_factor * 60
        target_vy = -joystick_y * speed_factor * 60

        if abs(joystick_x) > 0.1 or abs(joystick_y) > 0.1:
            self.velocity_x = self.velocity_x * 0.8 + target_vx * 0.2
            self.velocity_y = self.velocity_y * 0.8 + target_vy * 0.2
        else:
            self.velocity_x *= self.friction + jitter_x
            self.velocity_y *= self.friction + jitter_y

            if abs(self.velocity_x) < 0.01:
                self.velocity_x = 0
            if abs(self.velocity_y) < 0.01:
                self.velocity_y = 0

        new_x = self.cursor_x + self.velocity_x * dt + jitter_x
        new_y = self.cursor_y + self.velocity_y * dt + jitter_y

        self.update_cursor_position(new_x, new_y)

    def update_cursor_position(self, x, y):
        self.cursor_x = x
        self.cursor_y = y
        
        # Update the visual cursor position
        self.cursor_circle.x = self.center_x + x
        self.cursor_circle.y = self.center_y + y
        
        # Update cursor color based on whether it's in the target
        if self.is_cursor_in_target():
            self.cursor_circle.color = self.cursor_color
        else:
            self.cursor_circle.color = self.cursor_outside_color
    
    def is_cursor_in_target(self):
        # Check if cursor is within target circle
        distance = math.sqrt(self.cursor_x**2 + self.cursor_y**2)
        return distance <= self.target_radius
    
    def return_deviation(self):
        # Calculate distance from cursor to center
        return math.sqrt(self.cursor_x**2 + self.cursor_y**2)

    
    def draw(self):
        self.batch.draw()

class TrackingTask:
    def __init__(self, duration=15, sampling_rate=20):
        self.duration = duration
        self.sampling_interval = 1.0 / sampling_rate

        pygame.init()
        pygame.joystick.init()

        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Detected Joystick: {self.joystick.get_name()}")
        else:
            print("No Joystick Detected")
        
        # Create window
        self.window = pyglet.window.Window(width=800, height=600, caption="Tracking Task")
        
        # Create reticle
        self.reticle = SimpleReticle(self.window.width, self.window.height, target_proportion=0.25)
        
        # Tracking data
        self.first_target_entry_time = None
        self.distances = []
        self.sampling_times = []
        self.is_sampling = False
        self.start_time = None
        
        # Keyboard state for backup control
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        
        # Set up event handlers
        self.window.event(self.on_draw)
        
    def on_draw(self):
        self.window.clear()
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.window.clear()
        self.reticle.draw()
        
    def update(self, dt):
        current_time = time.time() - self.start_time
        if current_time >= self.duration:
            pyglet.app.exit()
            return

        joystick_x = 0
        joystick_y = 0

        pygame.event.pump()

        if self.joystick:
            joystick_x = self.joystick.get_axis(0)
            joystick_y = self.joystick.get_axis(1)

            dead_zone = 0.1
            if abs(joystick_x) < dead_zone:
                joystick_x = 0
            if abs(joystick_y) < dead_zone:
                joystick_y = 0
        else:
            if self.keys[key.LEFT]:
                joystick_x = -1
            elif self.keys[key.RIGHT]:
                joystick_x = 1
                
            if self.keys[key.UP]:
                joystick_y = 1
            elif self.keys[key.DOWN]:
                joystick_y = -1

        self.reticle.update(dt, joystick_x, joystick_y)
        if self.first_target_entry_time is None and self.reticle.is_cursor_in_target():
            self.first_target_entry_time = current_time
            self.is_sampling = True
        if self.is_sampling:
            if not self.sampling_times or (current_time - self.sampling_times[-1] >= self.sampling_interval):
                distance = self.reticle.return_deviation()
                self.distances.append(distance)
                self.sampling_times.append(current_time)
    
    def run(self):
        pyglet.clock.schedule_interval(self.update, 1/60.0)
        self.start_time = time.time()
        pyglet.app.run()
        if self.joystick:
            self.joystick.quit()
        pygame.quit()

        return {
            "first_entry_time": self.first_target_entry_time,
            "sampling_times": self.sampling_times,
            "distances": self.distances
        }

def main():
    task = TrackingTask(duration=15, sampling_rate=20)
    results = task.run()

    if results["first_entry_time"] is not None:
        print(f"Moving time: {results['first_entry_time']:.3f}seconds")
        print(f"num of samples: {len(results['distances'])}")
        print(f"average distance: {np.mean(results['distances']):.3f}")
        print(f"max distance: {np.max(results['distances']):.3f}")
        print(f"min distance: {np.min(results['distances']):.3f}")
    else:
        print("No cursor in target zone")

if __name__ == "__main__":
    main()