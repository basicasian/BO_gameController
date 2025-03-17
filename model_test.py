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