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

    print("\n" + "=" * 50)
    print("Trial #{}:".format(trial.number))
    print("Speed Factor: {:.2f}".format(speed_factor))
    print("Friction: {:.3f}".format(friction))
    print("=" * 50)

    task = TrackingTask(duration=15, sampling_rate=20)
    task.reticle.friction = friction
    task.reticle.speed_factor = speed_factor

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


def outer_optimization(trial, inner_trial: int = 10):
    if not joystick:
        print("No Joystick Detected")
        exit()
    cap_type = trial.suggest_categorical('cap_type', [1, 2, 3, 4, 5])
    rocker_length = trial.suggest_float('rocker_length', 5.0, 50.0)
    cap_size = trial.suggest_float('cap_size', 6.0, 57.0)

    # material_surface = trial.suggest_categorical('material_surface', [0, 1, 2])
    # spring_stiffness = trial.suggest_float('spring_stiffness', 0.1, 1.0)

    print("\n" + "=" * 50)
    print("Trial #{}:".format(trial.number))
    print("CapType: {}".format(cap_type))
    print("Rocker Length: {:.2f}mm".format(rocker_length))
    print("Cap size: {:.2f}mm".format(cap_size))

    inner_study = optuna.create_study(direction='maximize')
    inner_study.optimize(inner_optimization, n_trials=inner_trial)
    inner_para_list = inner_study.best_params.items()
    inner_para = dict(inner_para_list)
    damping = inner_para["Damping"]
    deadzone = inner_para["Deadzone"]
    speed_factor = inner_para["speed_factor"]
    friction = inner_para["friction"]

    task = TrackingTask(duration=15, sampling_rate=20)
    task.reticle.friction = friction
    task.reticle.speed_factor = speed_factor
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

    perf_outer = PerformanceModel()
    score = perf_outer.compute_performance(error, moving_time)

    print("\nResults: ")
    print(f"Error: {error:.3f}")
    print(f"Moving time: {moving_time:.3f} seconds")
    print(f"Score: {score:.4f}")

    return score



def inner_optimization(trial):
    if not joystick:
        print("No Joystick Detected")
        exit()
    damping = trial.suggest_float('Damping', 0.0, 1.0)
    deadzone = trial.suggest_float('Deadzone', 0.0, 1.0)
    speed_factor = trial.suggest_float('speed_factor', 1.0, 10.0)
    friction = trial.suggest_float('friction', 0.93, 0.9999)

    print("\n" + "=" * 50)
    print("Trial #{}:".format(trial.number))
    print("Speed Factor: {:.2f}".format(speed_factor))
    print("Friction: {:.3f}".format(friction))
    print("=" * 50)

    task = TrackingTask(duration=15, sampling_rate=20)
    task.reticle.friction = friction
    task.reticle.speed_factor = speed_factor

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

    perf_inner = PerformanceModel()
    score = perf_inner.compute_performance(error, moving_time)

    print("\nResults: ")
    print(f"Error: {error:.3f}")
    print(f"Moving time: {moving_time:.3f} seconds")
    print(f"Score: {score:.4f}")

    return score


def run_tracking_optimization():
    study = optuna.create_study(direction='maximize')
    n_trials = 10

    study.optimize(outer_optimization, n_trials=n_trials)

    print("\n" + "=" * 50)


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
