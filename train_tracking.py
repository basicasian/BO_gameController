from stable_baselines3 import PPO
from stable_baselines3.common.vec_env.dummy_vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import BaseCallback
from trackRL import TrackingEnv
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from datetime import datetime
import torch

class TrainingCallback(BaseCallback):
    def __init__(self, check_freq, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.rewards = []
        self.losses = []
        self.episode_reward = 0
        self.episode_rewards = []
        self.device = 'cpu' if not torch.cuda.is_available() else 'cuda'
        print(self.device)
        
    def _on_step(self):
        if self.n_calls % self.check_freq == 0:
            if len(self.episode_rewards) > 0:
                self.rewards.append(np.mean(self.episode_rewards[-10:]))

            if len(self.model.logger.name_to_value) > 0:
                self.losses.append(self.model.logger.name_to_value.get('train/loss', 0))

            plt.clf()
            
            plt.subplot(1, 2, 1)
            plt.plot(self.rewards)
            plt.title('Average Reward')
            plt.xlabel('Steps')
            plt.ylabel('Reward')
            
            plt.subplot(1, 2, 2)
            plt.plot(self.losses)
            plt.title('Training Loss')
            plt.xlabel('Steps')
            plt.ylabel('Loss')
            
            plt.tight_layout()
            plt.pause(0.1)

        self.episode_reward += self.locals['rewards'][0]

        if self.locals['dones'][0]:
            self.episode_rewards.append(self.episode_reward)
            self.episode_reward = 0
            
        return True

env = DummyVecEnv([lambda: TrackingEnv()])

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=1024,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2
)

callback = TrainingCallback(check_freq=1000)

total_timesteps = 100000
model.learn(
    total_timesteps=total_timesteps,
    callback=callback
)

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
model.save(f"tracking_model_ppo_{current_time}")

mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10, render=False)
print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

env.close()
plt.show()