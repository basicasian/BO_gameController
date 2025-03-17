import optuna
import pyglet
from objective import PerformanceModel, error_calc
from simple_tracking_task import TrackingTask
import time
import pygame

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

    task = TrackingTask(duration=15, sampling_rate=20)
    task.reticle.friction = friction
    task.reticle.speed_factor = speed_factor
    
    task.reticle.friction = friction
    def on_experiment_end():
        task.window.close()
        pyglet.app.exit()
    task.on_experiment_end = on_experiment_end
    task.update = task.update

    results = task.run(test_env=False)
    print(results)

    if results["first_entry_time"] is None:
        return 0.0

    error = error_calc(results["distances"])
    moving_time = results["first_entry_time"]

    perf_model = PerformanceModel()
    score = perf_model.compute_performance(error, moving_time)
    
    print("\nResults: ")
    print(f"Error: {error:.3f}")
    print(f"Moving time: {moving_time:.3f} seconds")
    print(f"Score: {score:.4f}")
    
    return score

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