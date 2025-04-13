import optuna
import pyglet
from objective import PerformanceModel, error_calc
from simple_tracking_task import TrackingTask
import time
import pygame
import numpy as np

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected Joystick: {joystick.get_name()}")
else:
    print("No Joystick Detected")
    pygame.quit()

def tracking_objective(trial):

    if not joystick:
        print("No Joystick Detected")
        return 0.0


    speed_factor = trial.suggest_float('speed_factor', 1.0, 10.0)
    friction = trial.suggest_float('friction', 0.93, 0.9999)

    print("\n" + "="*50)
    print("Trial #{}:".format(trial.number))
    print("Speed Factor: {:.2f}".format(speed_factor))
    print("Friction: {:.3f}".format(friction))
    print("="*50)

    scores = []
    for i in range(20):
        print(f"\nSample {i+1}/20")
        task = TrackingTask(duration=15, sampling_rate=20, enable_bezier=False)
        task.reticle.friction = friction
        task.reticle.speed_factor = speed_factor
        
        def on_experiment_end():
            task.window.close()
            pyglet.app.exit()
        task.on_experiment_end = on_experiment_end
        task.update = task.update

        results = task.run(test_env=False)
        
        error = error_calc(results["distances"])
        moving_time = results['sampling_times'][-1]

        perf_model = PerformanceModel()
        score = perf_model.compute_performance(error, moving_time)
        scores.append(score)
        
        print(f"Sample Score: {score:.4f}")

        if i == 4:
            current_avg = sum(scores) / 5

            previous_scores = [t.value for t in trial.study.trials if t.value is not None]
            if previous_scores:
                prev_mean = np.mean(previous_scores)
                prev_std = np.std(previous_scores)
                
                if current_avg < (prev_mean - prev_std):
                    print(f"\nEarly stopping: Current avg ({current_avg:.4f}) is significantly lower than historical performance (mean: {prev_mean:.4f}, std: {prev_std:.4f})")
                    return 0.0

    final_scores = scores[10:]
    final_score = sum(final_scores) / 10

    std_dev = np.std(final_scores)
    std_factor = 0.6
    
    stability_factor = (1-std_factor) + std_factor * np.exp(-std_dev)

    adjusted_score = final_score * stability_factor
    
    print("\nFinal Results: ")
    print(f"Average Score (last 10 samples): {final_score:.4f}")
    print(f"Standard Deviation: {std_dev:.4f}")
    print(f"Stability Factor: {stability_factor:.4f}")
    print(f"Adjusted Score: {adjusted_score:.4f}")
    
    return adjusted_score

def run_tracking_optimization():
    study = optuna.create_study(direction='maximize')
    n_trials = 10

    study.optimize(tracking_objective, n_trials=n_trials)
    
    print("\n" + "="*50)

    print(f"  speed_factor: {study.best_params['speed_factor']:.2f}")
    print(f"  friction: {study.best_params['friction']:.3f}")
    print(f"Best Score: {study.best_value:.4f}")
    print("="*50)

    save_results = input("\nSave? (y/n): ").lower() == 'y'
    if save_results:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"tracking_optimization_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("Tracking BO Results:\n")
            f.write("Best Para:\n")
            for param_name, param_value in study.best_params.items():
                f.write(f"  {param_name}: {param_value}\n")
            f.write(f"Best Score: {study.best_value}\n")
            
            f.write("\nAll Trial:\n")
            for trial in study.trials:
                f.write(f"Trial #{trial.number}:\n")
                for param_name, param_value in trial.params.items():
                    f.write(f"  {param_name}: {param_value}\n")
                f.write(f"  Score: {trial.value}\n\n")
                
        print(f"Result saved to {filename}")

if __name__ == "__main__":
    run_tracking_optimization()