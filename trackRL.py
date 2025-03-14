import gymnasium as gym
import numpy as np
from gymnasium import spaces
from simple_tracking_task import TrackingTask, SimpleReticle
from objective import PerformanceModel, error_calc
import pyglet
import time

class TrackingEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.action_space = spaces.Box(
            low=-1, high=1, shape=(2,), dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32
        )
        
        self.task = None
        self.perf_model = PerformanceModel()
        self.current_step = 0
        self.max_steps = 900
        
    def reset(self, seed=None):
        super().reset(seed=seed)

        if self.task is not None:
            self.task.window.close()
        self.task = TrackingTask(duration=15, sampling_rate=20)

        def on_experiment_end():
            self.task.window.close()
            pyglet.app.exit()
        self.task.on_experiment_end = on_experiment_end

        self.current_step = 0
        state = np.array([
            self.task.reticle.cursor_x,
            self.task.reticle.cursor_y,
            self.task.reticle.velocity_x,
            self.task.reticle.velocity_y
        ], dtype=np.float32)
        
        return state, {}
    
    def step(self, action):
        self.current_step += 1

        dt = 1/60.0
        joystick_x, joystick_y = action
        self.task.reticle.update(dt, joystick_x, joystick_y)

        state = np.array([
            self.task.reticle.cursor_x,
            self.task.reticle.cursor_y,
            self.task.reticle.velocity_x,
            self.task.reticle.velocity_y
        ], dtype=np.float32)

        distance = self.task.reticle.return_deviation()
        error = error_calc([distance])

        if self.task.first_target_entry_time is None and self.task.reticle.is_cursor_in_target():
            self.task.first_target_entry_time = self.current_step * dt
            
        if self.task.first_target_entry_time is not None:
            moving_time = self.task.first_target_entry_time
            reward = self.perf_model.compute_performance(error, moving_time)
        else:
            reward = -error

        terminated = self.current_step >= self.max_steps
        truncated = False
        
        info = {
            'distance': distance,
            'error': error,
            'moving_time': self.task.first_target_entry_time
        }
        
        return state, reward, terminated, truncated, info
    
    def render(self):
        self.task.on_draw()
        
    def close(self):
        if self.task is not None:
            self.task.window.close()

if __name__ == "__main__":
    env = TrackingEnv()
    obs, _ = env.reset()
    
    def update(dt):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Reward: {reward:.3f}, Distance: {info['distance']:.3f}")
        
        if terminated or truncated:
            env.close()
            pyglet.app.exit()
    
    # 设置pyglet更新间隔
    pyglet.clock.schedule_interval(update, 1/200)
    
    # 运行pyglet事件循环
    pyglet.app.run()