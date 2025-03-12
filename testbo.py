import numpy as np
import time
import pygame
from BayesianOptimization import BayesianOptimizer
from preprocess import f_perf, error_calc, accuracy, res_speed
import testgizmo
import threading
import queue


class TestEnvironment:
    def __init__(self):
        self.distance_queue = queue.Queue()
        self.running = False
        self.env_thread = None
        self.sample_thread = None
        self.game_running = True

    def collect_samples(self):
        self.distances = []
        while len(self.distances) < 50 and self.running:
            try:
                distance = self.distance_queue.get(timeout=0.1)
                self.distances.append(distance)
                print(f"采样进度: {len(self.distances)}/50", end='\r')
            except queue.Empty:
                continue
        self.running = False
        self.game_running = False
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def run_environment(self, gravity, jump_speed):
        testgizmo.GRAVITY = gravity
        testgizmo.JUMP_SPEED = jump_speed

        self.running = True
        start_time = time.time()

        testgizmo.main.distance_queue = self.distance_queue
        print(f"Gravity={gravity:.3f}, jump_speed={jump_speed:.3f}")

        self.sample_thread = threading.Thread(target=self.collect_samples)
        self.sample_thread.start()

        testgizmo.main()

        self.sample_thread.join()

        error = error_calc(self.distances)
        moving_time = time.time() - start_time

        acc_val = accuracy(error, 1.0)
        speed_val = res_speed(moving_time)
        perf = f_perf(acc_val, speed_val)
        return perf, error, moving_time


def objective_function(params):
    gravity, jump_speed = params
    env = TestEnvironment()

    perf, _, _ = env.run_environment(gravity, jump_speed)
    return perf


def main():
    bounds = [
        (0.1, 0.9),  # gravity
        (-10, -1)  # jump_speed
    ]

    optimizer = BayesianOptimizer(bounds)

    n_initial = 5
    print("\n=== Initial Sampling ===")
    for i in range(n_initial):
        gravity = np.random.uniform(0.1, 0.9)
        jump_speed = np.random.uniform(-10, -1)
        print(f"\n{i + 1}/{n_initial} round sampling:")
        perf = objective_function([gravity, jump_speed])
        optimizer.update([[gravity, jump_speed]], [perf])
        print(f"Sample {i + 1} done")

    n_iterations = 10
    best_params = None
    best_perf = -np.inf

    for i in range(n_iterations):
        next_point = optimizer.suggest_next_point()

        perf = objective_function(next_point)

        optimizer.update([next_point], [perf])

        if perf > best_perf:
            best_perf = perf
            best_params = next_point

        print(f"Iteration {i + 1}:")
        print(f"Parameters: gravity={next_point[0]:.3f}, jump_speed={next_point[1]:.3f}")
        print(f"Performance: {perf:.3f}")
        print(f"Best so far: {best_perf:.3f}\n")

    print("\nFinal test with best parameters:")
    print(f"Best parameters: gravity={best_params[0]:.3f}, jump_speed={best_params[1]:.3f}")

    env = TestEnvironment()
    final_perf, final_error, final_time = env.run_environment(
        best_params[0], best_params[1]
    )

    print(f"Final performance: {final_perf:.3f}")
    print(f"Final error: {final_error:.3f}")
    print(f"Final time: {final_time:.3f}s")


if __name__ == "__main__":
    main()