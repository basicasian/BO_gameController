import optuna
import pyglet
from objective import PerformanceModel, error_calc, PreferenceModel
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

def tracking_objective(trial, pref_model, trial_history):
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
    stability_factor = (1-0.6) + 0.6 * np.exp(-std_dev)
    objective_score = final_score * stability_factor

    if pref_model.pair:
        if trial.number > 0:
            print("\nCompare with previous trial:")
            print(f"Previous parameters: speed_factor={trial_history[-1]['speed_factor']:.2f}, "
                  f"friction={trial_history[-1]['friction']:.3f}")
            print(f"Current parameters: speed_factor={speed_factor:.2f}, "
                  f"friction={friction:.3f}")
            print("Is this configuration better than the previous one? (y/n)")
            is_better = input().lower() == 'y'
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
                    
                is_better = input(f"\nWhich trial is better? (1 for {pair1}, 2 for {pair2}): ").strip()
                
                if is_better == '1':
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
    task = TrackingTask(duration=10, sampling_rate=20, enable_bezier=False)  # 缩短验证时间
    task.reticle.friction = params['friction']
    task.reticle.speed_factor = params['speed_factor']
    
    def on_experiment_end():
        task.window.close()
        pyglet.app.exit()
    task.on_experiment_end = on_experiment_end
    task.update = task.update

    return task.run(test_env=False)

def run_tracking_optimization(pair_mode=False, similar_comparison=False):
    n_trials = 15
    
    study = optuna.create_study(direction='maximize')
    pref_model = PreferenceModel(n_trials, pair=pair_mode, similar_comparison=similar_comparison)
    trial_history = []
    
    for i in range(n_trials):
        trial = study.ask()
        
        params = {
            'speed_factor': trial.params['speed_factor'],
            'friction': trial.params['friction']
        }
        trial_history.append(params)
        
        value = tracking_objective(trial, pref_model, trial_history)
        study.tell(trial, value)
    
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
            
            f.write("\nPreference Data:\n")
            if pair_mode:
                f.write("Pairwise comparisons:\n")
                for comp in pref_model.comparison_history:
                    f.write(f"  Trial {comp[0]} {'>' if comp[1] else '<'} Trial {comp[1]}\n")
            f.write(f"Final utilities: {pref_model.utilities.tolist()}\n")
                
        print(f"Result saved to {filename}")

if __name__ == "__main__":
    run_tracking_optimization(pair_mode=True, similar_comparison=True)