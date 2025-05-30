import optuna
import pyglet
from objective import PerformanceModel, error_calc, PreferenceModel
from simple_tracking_task import TrackingTask
import time
import pygame
import numpy as np
from selectUI import get_user_preference
from task_switcher import TaskSwitcher, TaskType

pygame.init()
pygame.joystick.init()

detailed_scores = {}

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected Joystick: {joystick.get_name()}")
else:
    print("No Joystick Detected")
    pygame.quit()

def tracking_objective(trial, pref_model, trial_history, task_type=TaskType.AIMING):
    global detailed_scores  

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
    switcher = TaskSwitcher()

    for i in range(20):
        print(f"\nSample {i+1}/20")
        params = {
            "duration": 15,
            "sampling_rate": 20,
            "friction": friction,
            "speed_factor": speed_factor,
        }

        results = switcher.run_task(task_type, params)  # Use the task_type parameter here

        error = error_calc(results["distances"])
        moving_time = results['sampling_times'][-1]
        jitter = results["jitter"]

        perf_model = PerformanceModel()
        score = perf_model.compute_performance(error, moving_time, jitter)
        scores.append(score)

        print(f"Sample Score: {score:.4f}")

        if i == 4:
            current_avg = sum(scores) / 5
            print(f"CurrentAvg: {current_avg}")
            if current_avg < 0.2:
                print(f"\nEarly stopping: Current average ({current_avg:.4f}) is too low")
                detailed_scores[trial.number] = {
                    'accuracy_scores': [],
                    'time_scores': [],
                    'performance_scores': scores,
                    'avg_accuracy': 0.0,
                    'avg_time': 0.0,
                    'avg_performance': 0.0
                }
                return 0.0

            previous_scores = [t.value for t in trial.study.trials if t.value is not None]
            if previous_scores:
                prev_mean = np.mean(previous_scores)
                prev_std = np.std(previous_scores)

                if current_avg < (prev_mean - prev_std) or current_avg < 0.2:
                    print(f"\nEarly stopping: Current avg ({current_avg:.4f}) is significantly lower than historical performance (mean: {prev_mean:.4f}, std: {prev_std:.4f})")
                    detailed_scores[trial.number] = {
                        'accuracy_scores': [],
                        'time_scores': [],
                        'performance_scores': scores,
                        'avg_accuracy': 0.0,
                        'avg_time': 0.0,
                        'avg_performance': 0.0
                    }
                    return 0.0

    final_scores = scores[10:]
    final_score = sum(final_scores) / 10
    std_dev = np.std(final_scores)
    stability_factor = (1-0.6) + 0.6 * np.exp(-std_dev)
    objective_score = final_score * stability_factor

    if pref_model.pair:
        if trial.number > 0:
            print("\nCompare with previous trial:")
            print(f"Previous parameters: speed_factor={trial_history[-1]['speed_factor']:.2f}, "
                  f"friction={trial_history[-1]['friction']:.3f}")
            print(f"Current parameters: speed_factor={speed_factor:.2f}, "
                  f"friction={friction:.3f}")
            is_better = get_user_preference(trial.number-1, trial.number, trial_history, TaskType.AIMING) == "1"
            pref_model.add_comparison(trial.number, is_better)
    else:
        if trial.number % 5 == 4:
            print("\nPlease rank the last 5 trials (space-separated indices, best to worst):")
            for t in range(max(0, trial.number-4), trial.number+1):
                print(f"Trial {t}: speed_factor={trial_history[t]['speed_factor']:.2f}, "
                      f"friction={trial_history[t]['friction']:.3f}")
            try:
                ranking = list(map(int, input().split()))
                pref_model.fit([ranking])
            except ValueError:
                print("Invalid input. Skipping preference scoring.")
                return objective_score

    if pref_model.pair and pref_model.similar_comparison:
        similar_pairs = pref_model.find_similar_preferences()
        for pair1, pair2 in similar_pairs:
            if (pair1, pair2) not in pref_model.similar_pairs:
                print(f"Similar preferences between Trial {pair1} and Trial {pair2}")

                for i in range(3):
                    print(f"\nVerification round {i+1}/3:")

                    print(f"\nTesting Trial {pair1}...")
                    print(f"Parameters: speed_factor={trial_history[pair1]['speed_factor']:.2f}, "
                          f"friction={trial_history[pair1]['friction']:.3f}")
                    run_verification_trial(trial_history[pair1])

                time.sleep(1)

                for i in range(3):
                    print(f"\nTesting Trial {pair2}...")
                    print(f"Parameters: speed_factor={trial_history[pair2]['speed_factor']:.2f}, "
                          f"friction={trial_history[pair2]['friction']:.3f}")
                    run_verification_trial(trial_history[pair2])

                is_better = get_user_preference(pair1, pair2, trial_history, TaskType.AIMING)

                if is_better == "1":
                    print(f"\nVerification result: Trial {pair1} is better than Trial {pair2}")
                    pref_model.verify_similar_pair(pair1, pair2)
                else:
                    print(f"\nVerification result: Trial {pair2} is better than Trial {pair1}")
                    pref_model.verify_similar_pair(pair2, pair1)

                pref_model.similar_pairs.append((pair1, pair2))
                pref_model.fit(pref_model.comparison_history)

    if pref_model.utilities is not None:
        pref_score = pref_model.utilities[trial.number]
        lambda_weight = 0.7
        final_score = lambda_weight * objective_score + (1 - lambda_weight) * pref_score
        print(f"Combined score (objective: {objective_score:.4f}, preference: {pref_score:.4f}): {final_score:.4f}")
        return final_score

    return objective_score

def run_verification_trial(params):
    switcher = TaskSwitcher()
    params.update({
        "duration": 10,
        "sampling_rate": 20,
    })
    return switcher.run_task(TaskType.AIMING, params)

def run_tracking_optimization(pair_mode=False, similar_comparison=False, physical_comparison=False, task_type=TaskType.AIMING):
    n_trials = 10
    n_initial_samples = 5
    n_repeats = 5

    study = optuna.create_study(direction='maximize')
    pref_model = PreferenceModel(n_trials, pair=pair_mode, similar_comparison=similar_comparison)
    trial_history = []
    detailed_scores = {}

    print("\n=== Initializing ===")
    initial_params = []
    for _ in range(n_initial_samples):
        speed_factor = np.random.uniform(1.0, 10.0)
        friction = np.random.uniform(0.93, 0.9999)
        initial_params.append({
            'speed_factor': speed_factor,
            'friction': friction
        })

    for i, params in enumerate(initial_params):
        print(f"\nInitial Sample #{i+1}/{n_initial_samples}")
        print(f"Speed Factor: {params['speed_factor']:.2f}")
        print(f"Friction: {params['friction']:.3f}")

        trial = study.ask()
        trial.suggest_float('speed_factor', params['speed_factor'], params['speed_factor'])
        trial.suggest_float('friction', params['friction'], params['friction'])

        trial_history.append(params)

        sample_scores = []
        accuracy_scores = []
        time_scores = []
        performance_scores = []
        switcher = TaskSwitcher()
        
        for j in range(n_repeats):
            print(f"\nRe:  #{j+1}/{n_repeats}")
            task_params = {
                "duration": 15,
                "sampling_rate": 20,
                "friction": params['friction'],
                "speed_factor": params['speed_factor']
            }
            
            results = switcher.run_task(task_type, task_params)
            
            error = error_calc(results["distances"])
            moving_time = results['sampling_times'][-1]
            jitter = results["jitter"]
            
            perf_model = PerformanceModel()
            accuracy_score = perf_model.compute_accuracy(error)
            time_score = perf_model.compute_time(moving_time)
            performance_score = perf_model.compute_performance(error, moving_time, jitter)
            
            accuracy_scores.append(accuracy_score)
            time_scores.append(time_score)
            performance_scores.append(performance_score)
            sample_scores.append(performance_score)
            
            print(f"Score{performance_score:.4f}")

        avg_score = np.mean(sample_scores)
        print(f"\nAVG SCORE: {avg_score:.4f}")
        study.tell(trial, avg_score)

        detailed_scores[trial.number] = {
            'accuracy_scores': accuracy_scores,
            'time_scores': time_scores,
            'performance_scores': performance_scores,
            'avg_accuracy': np.mean(accuracy_scores),
            'avg_time': np.mean(time_scores),
            'avg_performance': avg_score
        }

    print("\n=== INITIALIZING RESULTS ===")
    for i, trial in enumerate(study.trials[:n_initial_samples]):
        print(f"SAMPLE #{i+1}: speed_factor={trial.params['speed_factor']:.2f}, "
              f"friction={trial.params['friction']:.3f}, score={trial.value:.4f}")

    for i in range(n_trials - n_initial_samples):
        trial = study.ask()
        
        speed_factor = trial.suggest_float('speed_factor', 1.0, 10.0)
        friction = trial.suggest_float('friction', 0.93, 0.9999)
        
        params = {
            'speed_factor': speed_factor,
            'friction': friction
        }
        trial_history.append(params)
        
        value = tracking_objective(trial, pref_model, trial_history, task_type)
        study.tell(trial, value)

        if value == 0.0:
            continue

        scores = []
        accuracy_scores = []
        time_scores = []
        performance_scores = []
        
        for _ in range(20):
            results = switcher.run_task(task_type, params)
            error = error_calc(results["distances"])
            moving_time = results['sampling_times'][-1]
            jitter = results["jitter"]
            
            perf_model = PerformanceModel()
            accuracy_score = perf_model.compute_accuracy(error)
            time_score = perf_model.compute_time(moving_time)
            performance_score = perf_model.compute_performance(error, moving_time, jitter)
            
            accuracy_scores.append(accuracy_score)
            time_scores.append(time_score)
            performance_scores.append(performance_score)
        
        detailed_scores[trial.number] = {
            'accuracy_scores': accuracy_scores,
            'time_scores': time_scores,
            'performance_scores': performance_scores,
            'avg_accuracy': np.mean(accuracy_scores),
            'avg_time': np.mean(time_scores),
            'avg_performance': np.mean(performance_scores[10:])  # 与tracking_objective一致
        }

    best_params = study.best_params
    best_score = study.best_value

    print("\n" + "="*50)
    print(f"  speed_factor: {study.best_params['speed_factor']:.2f}")
    print(f"  friction: {study.best_params['friction']:.3f}")
    print(f"Best Score: {study.best_value:.4f}")
    print("="*50)

    if physical_comparison:
        return (best_score, best_params)

    save_results = input("\nSave? (y/n): ").lower() == 'y'
    if save_results:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"optimization_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("BO Results:\n")
            f.write("Best Para:\n")
            for param_name, param_value in study.best_params.items():
                f.write(f"  {param_name}: {param_value}\n")
            f.write(f"Best Score: {study.best_value}\n")
            
            f.write("\nAll Trial:\n")
            for trial in study.trials:
                f.write(f"Trial #{trial.number}:\n")
                f.write("Parameters:\n")
                for param_name, param_value in trial.params.items():
                    f.write(f"  {param_name}: {param_value}\n")
                trial_scores = detailed_scores[trial.number]
                f.write("Scores:\n")
                f.write(f"  Accuracy Score: {trial_scores['avg_accuracy']:.4f}\n")
                f.write(f"  Time Score: {trial_scores['avg_time']:.4f}\n")
                f.write(f"  Performance Score: {trial_scores['avg_performance']:.4f}\n")
                
                if pref_model.utilities is not None:
                    pref_score = pref_model.utilities[trial.number]
                    f.write(f"  Preference Score: {pref_score:.4f}\n")
                
                f.write(f"  Final Score: {trial.value:.4f}\n\n")
            
            f.write("\nPreference Data:\n")
            if pair_mode:
                f.write("Pairwise comparisons:\n")
                for comp in pref_model.comparison_history:
                    f.write(f"  Trial {comp[0]} {'>' if comp[1] else '<'} Trial {comp[1]}\n")
            if pref_model.utilities is not None:
                f.write(f"Final utilities: {pref_model.utilities.tolist()}\n")
                
        print(f"Result saved to {filename}")

if __name__ == "__main__":
    run_tracking_optimization(pair_mode=True, similar_comparison=True, task_type=TaskType.AIMING)