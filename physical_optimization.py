import optuna
import time
import tracking_op
from tracking_op import run_tracking_optimization
import switch_ui as su
import numpy as np

def physical_objective(trial):
    # Define physical parameter search space
    keycap_type = trial.suggest_int('keycap_type', 0, 4)
    rocker_length = trial.suggest_float('rocker_length', 5.0, 50.0)
    cap_size = trial.suggest_float('cap_size', 6.0, 57.0)
    
    print("\n" + "="*50)
    print("Physical Parameter Optimization Trial #{}:".format(trial.number))
    print(f"Keycap Type: {keycap_type}")
    print(f"Rocker Length: {rocker_length:.2f}mm")
    print(f"Cap Size: {cap_size:.2f}mm")
    print("="*50)
    
    # Run tracking task optimization to evaluate current physical parameters
    print("\nStarting tracking task optimization...")
    tracking_score, best_params = run_tracking_optimization(
        pair_mode=True,
        similar_comparison=True,
        physical_comparison=True
    )
    
    # Calculate physical parameter rationality penalty
    # 1. Ratio between rocker length and cap size should be appropriate
    ratio = rocker_length / cap_size
    if ratio < 0.5 or ratio > 3.0:
        tracking_score *= 0.8  # Reduce score for unreasonable ratio
    
    # 2. Consider compatibility between keycap type and size
    if keycap_type in [1, 2] and cap_size < 20:  # Concave and spherical caps shouldn't be too small
        tracking_score *= 0.9
    
    print("\n" + "="*50)
    print("Current Physical Parameter Evaluation:")
    print(f"Tracking Task Score: {tracking_score:.4f}")
    print(f"Best Control Parameters: speed_factor={best_params['speed_factor']:.2f}, "
          f"friction={best_params['friction']:.3f}")
    print("="*50)
    
    return tracking_score

def run_physical_optimization():
    
    study = optuna.create_study(direction='maximize')
    n_trials = 10
    
    for i in range(n_trials):
        print(f"\nStarting Physical Parameter Trial {i+1}/{n_trials}")
        trial = study.ask()
        value = physical_objective(trial)
        study.tell(trial, value)
        if i < n_trials - 1:
            next_trial = study.ask()
            if not su.show_switch_prompt(
                next_trial.params['keycap_type'],
                next_trial.params['rocker_length'],
                next_trial.params['cap_size']
            ):
                print("Optimization cancelled by user")
                break
            study.tell(next_trial, 0)
            study.trials.pop()
    
    print("\n" + "="*50)
    print("Physical Parameter Optimization Complete!")
    print("Best Physical Parameters:")
    print(f"Keycap Type: {study.best_params['keycap_type']}")
    print(f"Rocker Length: {study.best_params['rocker_length']:.2f}mm")
    print(f"Cap Size: {study.best_params['cap_size']:.2f}mm")
    print(f"Best Score: {study.best_value:.4f}")
    print("="*50)
    
    # Save results
    save_results = input("\nSave results? (y/n): ").lower() == 'y'
    if save_results:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"physical_optimization_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("Physical Parameter Optimization Results:\n")
            f.write("\nBest Parameters:\n")
            for param_name, param_value in study.best_params.items():
                f.write(f"  {param_name}: {param_value}\n")
            f.write(f"Best Score: {study.best_value}\n")
            
            f.write("\nAll Trials:\n")
            for trial in study.trials:
                f.write(f"\nTrial #{trial.number}:\n")
                for param_name, param_value in trial.params.items():
                    f.write(f"  {param_name}: {param_value}\n")
                f.write(f"  Score: {trial.value}\n")
                
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    run_physical_optimization()