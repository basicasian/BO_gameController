"""
physical_optimization.py

NOTE: Not used in the main process

Entry point for optimizing physical joystick parameters (keycap type, rocker length, cap size) using Optuna.

This script:
- Defines a physical parameter search space and an objective function (`physical_objective`)
  that evaluates each parameter set by running a tracking task optimization.
- Applies rationality penalties to discourage unreasonable physical parameter combinations.
- Interacts with the user to confirm physical parameter changes before each trial.
- Runs a Bayesian optimization loop for a specified number of trials, tracking the best parameters and scores.
- Optionally saves all trial results and the best parameters to a timestamped results file.

Modules used:
- optuna: For Bayesian optimization.
- tracking_op: For running tracking task optimization and evaluating parameter sets.
- switch_ui: For user prompts regarding physical parameter changes.
- numpy: For numerical operations.
- time: For timestamping result files.

Run this script directly to start the physical parameter optimization process.
"""

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

    current_trial = study.ask()
    keycap_type = current_trial.suggest_int('keycap_type', 0, 4)
    rocker_length = current_trial.suggest_float('rocker_length', 5.0, 50.0)
    cap_size = current_trial.suggest_float('cap_size', 6.0, 57.0)

    if not su.show_switch_prompt(keycap_type, rocker_length, cap_size):
        print("Optimization cancelled by user")
        return
    
    for i in range(n_trials):
        print(f"\nStarting Physical Parameter Trial {i+1}/{n_trials}")

        value = physical_objective(current_trial)
        study.tell(current_trial, value)
        if i < n_trials - 1:
            current_trial = study.ask()
            keycap_type = current_trial.suggest_int('keycap_type', 0, 4)
            rocker_length = current_trial.suggest_float('rocker_length', 5.0, 50.0)
            cap_size = current_trial.suggest_float('cap_size', 6.0, 57.0)
            
            if not su.show_switch_prompt(keycap_type, rocker_length, cap_size):
                print("Optimization cancelled by user")
                break
    
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