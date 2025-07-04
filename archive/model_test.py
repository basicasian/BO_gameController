"""
model_test.py

NOTE: Not used anymore, can be deleted.

This script is used for testing reinforcement learning models in a tracking environment.
It loads a trained PPO model, runs it in the `TrackingEnv` environment, and visualizes the agent's performance.
The script uses Pyglet for rendering and collects reward statistics for evaluation.

Main components:
- Model loading: Loads a PPO model from a specified file.
- Environment setup: Wraps `TrackingEnv` in a DummyVecEnv for compatibility with Stable Baselines3.
- Evaluation loop: Steps through the environment using the model's policy, renders each frame, and tracks rewards.
- Main block: Runs the evaluation and prints the final average score.

Dependencies: stable_baselines3, pyglet, matplotlib, trackRL (TrackingEnv).
"""

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env.dummy_vec_env import DummyVecEnv
from trackRL import TrackingEnv
import matplotlib
matplotlib.use('TkAgg')
import pyglet


model_name = "tracking_model_ppo_20250314_185905.zip"
model = PPO.load(model_name)
env = DummyVecEnv([lambda: TrackingEnv()])

state = env.reset()
done = False
truncated = False
rewards = []
score = 0.0

def update(dt):
    global state, done, truncated, score
    if not (done or truncated):
        action, _states = model.predict(state)
        next_state, reward, done, info = env.step(action)
        state = next_state
        rewards.append(reward[0])
        score += float(reward[0])
        env.envs[0].task.on_draw()

pyglet.clock.schedule_interval(update, 1/60.0)
pyglet.app.run()

env.close()
print(f"Final score: {score/len(rewards):.2f}")