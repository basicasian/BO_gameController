"""
simple_path_tracking_task.py

- All are pygame/pyglet environments: simple_aiming_task.py (Aiming), simple_tracking_task.py
(Tracking), simple_path_tracking_task.py (Path Tracking).
- All environments require an external joystick connection to run, otherwise the environments may not run properly.
- At the end of each environment file, there is test code, and running the code will perform a test (without any logging).
- After updating the screen scheduling, sometimes running the environments on a single screen (especially from the optimizer)
will result in a splash screen bug, for which no valid code solution has been found. For this issue, it is recommended to use an external monitor as a display
window for the game environment.

- All environments randomly change mission parameter settings (e.g., location, path, etc.) on reset.
- Specifically, there is a Bessel-based external force effect in the tracking task, see near the tenth
line of simple_tracking_task.py: enable_bezier
- This effect is off by default, and will be applied when passed a parameter of true.
- Note, however, that this may make the task difficult to complete, so choose carefully, and also modify the optimizer's pruning parameters
(see the “Optimizer” section for details).

Main components:
- PathReticle: Handles rendering and logic for the path, reticle, and target.
- PathTrackingTask: Manages the path tracking session, input handling, and performance metrics.
- main: Example entry point to run the path tracking task and print results.

Dependencies: pyglet, pygame, numpy, math, random, time.
"""

import time
import numpy as np
import pyglet
from pyglet.window import key
import math
import random
import pygame

class PathReticle:
    def __init__(self, window_width, window_height, friction=0.94, speed_factor=7, duration=15):
        self.window_width = window_width
        self.window_height = window_height
        self.center_x = window_width // 2
        self.center_y = window_height // 2
        self.duration = duration

        self.path_width = 45
        self.cursor_x = 0
        self.cursor_y = 0

        self.background_color = (255, 255, 255)
        self.path_color = (220, 220, 220)
        self.path_center_color = (100, 100, 100)
        self.cursor_color = (0, 0, 255)
        self.cursor_outside_color = (255, 0, 0)

        self.batch = pyglet.graphics.Batch()

        self.target_radius = 20
        self.target_color = (220, 220, 220)
        self.target_border_color = (255, 0, 0)

        self.control_points = self._generate_control_points()
        self.path_points = self._generate_path_points()

        self.path_lines = []
        self.path_centers = []




        self._draw_path()

        self.target_border = pyglet.shapes.Circle(
            self.path_points[-1][0], self.path_points[-1][1],
            self.target_radius + 2,
            color=self.target_border_color,
            batch=self.batch
        )
        self.target_circle = pyglet.shapes.Circle(
            self.path_points[-1][0], self.path_points[-1][1],
            self.target_radius,
            color=self.target_color,
            batch=self.batch
        )
        self.target_border.opacity = 255

        self.cursor_position = (self.path_points[0][0] - self.center_x, 
                               self.path_points[0][1] - self.center_y)

        self.cursor_circle = pyglet.shapes.Circle(
            self.center_x, self.center_y, 2,
            color=self.cursor_color, batch=self.batch
        )

        self.cursor_h_line = pyglet.shapes.Line(
            self.center_x - 12, self.center_y,
            self.center_x + 12, self.center_y,
            width=1, color=self.cursor_color, batch=self.batch
        )
        
        self.cursor_v_line = pyglet.shapes.Line(
            self.center_x, self.center_y - 12,
            self.center_x, self.center_y + 12,
            width=1, color=self.cursor_color, batch=self.batch
        )

        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = friction
        self.speed_factor = speed_factor
        
        self.update_cursor_position(*self.cursor_position)
        self.start_time = time.time()

    def _generate_control_points(self):
        points = []
        center_x, center_y = self.center_x, self.center_y

        start_x = center_x - 400
        start_y = center_y
        points.append((start_x, start_y))

        control1_x = center_x - 200
        control1_y = random.randint(center_y - 200, center_y + 200)
        points.append((control1_x, control1_y))

        control2_x = center_x + 200
        control2_y = random.randint(center_y - 200, center_y + 200)
        points.append((control2_x, control2_y))

        end_x = center_x + 400
        end_y = center_y
        points.append((end_x, end_y))
            
        return points

    def _bezier_point(self, t, points):
        x = (1-t)**3 * points[0][0] + 3*(1-t)**2*t * points[1][0] + \
            3*(1-t)*t**2 * points[2][0] + t**3 * points[3][0]
        y = (1-t)**3 * points[0][1] + 3*(1-t)**2*t * points[1][1] + \
            3*(1-t)*t**2 * points[2][1] + t**3 * points[3][1]
        return x, y

    def _generate_path_points(self):
        # 生成轨迹点
        points = []
        for t in np.linspace(0, 1, 100):
            x, y = self._bezier_point(t, self.control_points)
            points.append((x, y))
        return points

    def _draw_path(self):
        self.path_lines.clear()
        self.path_centers.clear()

        for i in range(len(self.path_points) - 1):
            path_line = pyglet.shapes.Line(
                self.path_points[i][0], self.path_points[i][1],
                self.path_points[i+1][0], self.path_points[i+1][1],
                width=self.path_width,
                color=self.path_color,
                batch=self.batch
            )
            self.path_lines.append(path_line)

            center_line = pyglet.shapes.Line(
                self.path_points[i][0], self.path_points[i][1],
                self.path_points[i+1][0], self.path_points[i+1][1],
                width=1,
                color=self.path_center_color,
                batch=self.batch
            )
            self.path_centers.append(center_line)

    def _find_nearest_point(self, x, y):
        # 计算到轨迹中心线的最短距离
        min_distance = float('inf')
        for point in self.path_points:
            distance = math.sqrt((x - point[0])**2 + (y - point[1])**2)
            if distance < min_distance:
                min_distance = distance
        return min_distance

    def update(self, dt, joystick_x=0, joystick_y=0):
        speed_factor = self.speed_factor
        target_vx = joystick_x * speed_factor * 60
        target_vy = -joystick_y * speed_factor * 60

        if abs(joystick_x) > 0.1 or abs(joystick_y) > 0.1:
            self.velocity_x = self.velocity_x * 0.8 + target_vx * 0.2
            self.velocity_y = self.velocity_y * 0.8 + target_vy * 0.2
        else:
            self.velocity_x *= self.friction
            self.velocity_y *= self.friction

            if abs(self.velocity_x) < 0.01:
                self.velocity_x = 0
            if abs(self.velocity_y) < 0.01:
                self.velocity_y = 0

        new_x = self.cursor_x + self.velocity_x * dt
        new_y = self.cursor_y + self.velocity_y * dt

        self.update_cursor_position(new_x, new_y)

    def update_cursor_position(self, x, y):
        self.cursor_x = x
        self.cursor_y = y

        screen_x = self.center_x + x
        screen_y = self.center_y + y

        self.cursor_circle.x = screen_x
        self.cursor_circle.y = screen_y

        self.cursor_h_line.x = screen_x - 12
        self.cursor_h_line.y = screen_y
        self.cursor_h_line.x2 = screen_x + 12
        self.cursor_h_line.y2 = screen_y
        
        self.cursor_v_line.x = screen_x
        self.cursor_v_line.y = screen_y - 12
        self.cursor_v_line.x2 = screen_x
        self.cursor_v_line.y2 = screen_y + 12

        distance = self._find_nearest_point(screen_x, screen_y)
        if distance <= self.path_width / 2:
            self.cursor_circle.color = self.cursor_color
            self.cursor_h_line.color = self.cursor_color
            self.cursor_v_line.color = self.cursor_color
        else:
            self.cursor_circle.color = self.cursor_outside_color
            self.cursor_h_line.color = self.cursor_outside_color
            self.cursor_v_line.color = self.cursor_outside_color
    
    def return_deviation(self):
        return self._find_nearest_point(self.center_x + self.cursor_x, 
                                      self.center_y + self.cursor_y)
    
    def draw(self):
        self.batch.draw()

    def is_in_target(self, x, y):
        # 检查是否在目标区域内
        target_x, target_y = self.path_points[-1]
        distance = math.sqrt((x - target_x)**2 + (y - target_y)**2)
        return distance <= self.target_radius

class PathTrackingTask:
    def __init__(self, duration=15, sampling_rate=20, friction=0.94, speed_factor=9):
        self.duration = duration
        self.sampling_interval = 1.0 / sampling_rate
        self.center_x = 0
        self.center_y = 0

        pygame.init()
        pygame.joystick.init()

        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Detected Joystick: {self.joystick.get_name()}")
        else:
            print("No Joystick Detected")

        display = pyglet.canvas.get_display()
        screens = display.get_screens()
        target_screen = screens[0]

        self.window = pyglet.window.Window(
            fullscreen=True,
            screen=target_screen,
            caption="Path Tracking Task"
        )

        self.center_x = self.window.width // 2
        self.center_y = self.window.height // 2

        self.reticle = PathReticle(self.window.width, self.window.height, 
                                  friction, speed_factor, self.duration)

        self.distances = []
        self.sampling_times = []
        self.start_time = None
        self.jitter_count = 0
        self.last_in_path = True
        self.target_stay_time = 0
        self.last_in_target = False

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.window.event(self.on_draw)

        self.time_label = pyglet.text.Label(
            text='Time: 15.0',
            x=self.window.width - 20,
            y=self.window.height - 20,
            anchor_x='right',
            anchor_y='top',
            color=(0, 0, 0, 255),
            font_size=10
        )
        
    def on_draw(self):
        self.window.clear()
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.window.clear()
        self.reticle.draw()
        self.time_label.draw()
        
    def update(self, dt):
        current_time = time.time() - self.start_time
        remaining_time = max(0, self.duration - current_time)
        self.time_label.text = f'Time: {remaining_time:.1f}'

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

        current_in_target = self.reticle.is_in_target(
            self.center_x + self.reticle.cursor_x,
            self.center_y + self.reticle.cursor_y
        )
        
        if current_in_target:
            if self.last_in_target:
                self.target_stay_time += dt
            else:
                self.target_stay_time = 0
                self.last_in_target = True
        else:
            self.target_stay_time = 0
            self.last_in_target = False

        if self.target_stay_time >= 0.1:
            pyglet.app.exit()
            return

        current_in_path = self.reticle.return_deviation() <= self.reticle.path_width / 2
        if self.last_in_path and not current_in_path:
            self.jitter_count += 1
        self.last_in_path = current_in_path

        if not self.sampling_times or (current_time - self.sampling_times[-1] >= self.sampling_interval):
            distance = self.reticle.return_deviation()
            self.distances.append(distance)
            self.sampling_times.append(current_time)
    
    def run(self, test_env=True):
        pyglet.clock.unschedule(self.update)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
        self.start_time = time.time()
        
        try:
            pyglet.app.run()
        finally:
            pyglet.clock.unschedule(self.update)
            if test_env:
                if self.joystick:
                    self.joystick.quit()
                pygame.quit()

            self.window.close()

        return {
            "sampling_times": self.sampling_times,
            "distances": self.distances,
            "jitter": self.jitter_count 
        }

def main():
    task = PathTrackingTask(
        duration=15, 
        sampling_rate=20
    )
    results = task.run()

    print(f"Task duration: {results['sampling_times'][-1]:.3f} seconds")
    print(f"Number of samples: {len(results['distances'])}")
    print(f"Average distance: {np.mean(results['distances']):.3f}")
    print(f"Max distance: {np.max(results['distances']):.3f}")
    print(f"Min distance: {np.min(results['distances']):.3f}")
    print(f"Jitter count: {results['jitter']}")

if __name__ == "__main__":
    main()