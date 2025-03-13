import numpy as np
import time
import pygame
from BayesianOptimization import BayesianOptimizer
from preprocess import f_perf, error_calc, accuracy, res_speed
import testgizmo
import threading   
import queue
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


class TestEnvironment:
    def __init__(self):
        self.distance_queue = queue.Queue()
        self.running = False
        self.env_thread = None
        self.sample_thread = None
        self.game_running = True

    def collect_samples(self):
        self.distances = []
        while len(self.distances) < 100 and self.running:
            try:
                distance = self.distance_queue.get(timeout=0.1)
                self.distances.append(distance)
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
        moving_time = testgizmo.first_target_entry_time if testgizmo.first_target_entry_time is not None else time.time() - start_time

        acc_val = accuracy(error, 1.0)
        speed_val = res_speed(moving_time)
        print(f"Accuracy={acc_val:.3f}\nerror={error:.3f}\nspeed={speed_val:.3f}")
        perf = f_perf(acc_val, speed_val, w1=0.8)
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
    
    # 用于记录性能数据和采样点
    iterations = []
    performances = []
    all_points = []
    iteration_count = 0

    n_initial = 5
    print("\n=== Initial Sampling ===")
    for i in range(n_initial):
        gravity = np.random.uniform(0.1, 0.9)
        jump_speed = np.random.uniform(-10, -1)
        print(f"\n{i + 1}/{n_initial} round sampling:")
        perf = objective_function([gravity, jump_speed])
        optimizer.update([[gravity, jump_speed]], [perf])
        print(f"Sample {i + 1} done")
        
        # 记录初始采样的性能数据和采样点
        iterations.append(iteration_count)
        performances.append(perf)
        all_points.append([gravity, jump_speed])
        iteration_count += 1

    n_iterations = 15
    best_params = None
    best_perf = -np.inf

    for i in range(n_iterations):
        next_point = optimizer.suggest_next_point()
        x = np.linspace(0.1, 0.9, 30)
        y = np.linspace(-10, -1, 30)
        X, Y = np.meshgrid(x, y)
        points = np.stack([X.ravel(), Y.ravel()], axis=1)
        print(points.shape)
        ei_values = optimizer.expected_improvement(points)
        EI = ei_values.reshape(30, 30)
        plt.figure(figsize=(10, 8))
        plt.contourf(X, Y, EI, levels=20)
        plt.colorbar(label='Expected Improvement')

        # 绘制已采样的点
        all_points_array = np.array(all_points)   
        plt.scatter(all_points_array[:, 0], all_points_array[:, 1], 
                    c='red', marker='x', label='Previous samples')
        plt.scatter(next_point[0], next_point[1], 
                    c='white', marker='*', s=150, label='Next sample')
        plt.xlabel('Gravity')
        plt.ylabel('Jump Speed')
        plt.title(f'Expected Improvement - Iteration {i+1}')
        plt.legend()
        # plt.show()
        plt.savefig(f'ei_iteration.png')
        plt.close()

        perf = objective_function(next_point)
        optimizer.update([next_point], [perf])

        if perf > best_perf:
            best_perf = perf
            best_params = next_point

        print(f"Iteration {i + 1}:")
        print(f"Parameters: gravity={next_point[0]:.3f}, jump_speed={next_point[1]:.3f}")
        print(f"Performance: {perf:.3f}")
        print(f"Best so far: {best_perf:.3f}\n")
        
        # 记录优化迭代的性能数据和采样点
        iterations.append(iteration_count)
        performances.append(perf)
        all_points.append(next_point)
        iteration_count += 1

    # 绘制性能曲线
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, performances, 'b-o')
    plt.axvline(x=n_initial-1, color='r', linestyle='--', label='Initial Sampling End')
    plt.xlabel('Iteration')
    plt.xticks(iterations)
    plt.ylabel('Performance (f_perf)')
    plt.title('Performance vs. Iteration')
    plt.grid(True)
    plt.legend()
    plt.savefig('optimization_performance.png')
    plt.close()

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