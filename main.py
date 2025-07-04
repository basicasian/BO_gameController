"""
main.py

NOTE: Not used in the main process

Entry point for running a human-in-the-loop Bayesian optimization process for joystick parameters using Optuna.

This script:
    - Defines an objective function (`human_in_the_loop_objective`) that interactively collects user input (error, moving time, jitter, and optional rankings) for each trial of joystick parameters.
    - Runs a Bayesian optimization loop (`run_bayesian_optimization`) to search for the best parameter set, prompting the user for feedback at each trial.
    - Displays the best found parameters and score after optimization.
    - Optionally saves all trial results and the best parameters to a timestamped results file.

Modules used:
    - optuna: For Bayesian optimization.
    - sklearn.gaussian_process: For Gaussian process regression (kernel imported but not directly used).
    - numpy: For numerical operations.
    - objective: For computing the joint score from user input and parameters.
    - time: For timestamping result files.

Run this script directly to start the optimization process.
"""

import optuna
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import numpy as np
import objective as ob
import time

def human_in_the_loop_objective(trial):

    cap_type = trial.suggest_categorical('cap_type', [0, 1, 2, 3, 4])
    # material_surface = trial.suggest_categorical('material_surface', [0, 1, 2])


    rocker_length = trial.suggest_float('rocker_length', 5.0, 50.0)
    cap_size = trial.suggest_float('cap_size', 6.0, 57.0)
    # spring_stiffness = trial.suggest_float('spring_stiffness', 0.1, 1.0)
    # damping_factor = trial.suggest_float('damping_factor', 0.1, 1.0)

    categorical_params = [cap_type]
    continuous_params = [rocker_length, cap_size]
    # categorical_params = [cap_type, material_surface]
    # continuous_params = [rocker_length, cap_size, spring_stiffness, damping_factor]
    params = [categorical_params, continuous_params]

    print("\n" + "="*50)
    print("Trial #{}:".format(trial.number))
    print("CapType: {}".format(cap_type))
    print("Rocker Length: {:.2f}mm".format(rocker_length))
    print("Cap size: {:.2f}mm".format(cap_size))
    # print("SpringStiffness: {:.2f}".format(spring_stiffness))
    # print("DampingFactor: {:.2f}".format(damping_factor))
    # print("Surface: {}".format(material_surface))
    print("="*50)

    try:
        error = float(input("请输入误差值 (0-1): "))
        moving_time = float(input("请输入移动时间 (秒): "))
        jitter = float(input("请输入抖动值 (可选，默认为0): ") or "0")

        use_rankings = input("是否有排序数据? (y/n): ").lower() == 'y'
        rankings = None
        if use_rankings:
            rankings = input("请输入排序数据 : ")
            if rankings:
                rankings = []
                for ranking in rankings:
                    if ranking:
                        ranking = [int(r) for r in ranking]
                        rankings.append(ranking)

        lambda_weight = 0.5

        score = ob.joint_score(
            [params], [error], [moving_time], [jitter], 
            rankings=rankings, 
            lambda_weight=lambda_weight
        )

        if isinstance(score, np.ndarray):
            score = score[0]
            
        print("Score: {:.4f}".format(score))
            
        return score
        
    except ValueError as e:
        print("输入错误: {}".format(e))
        return 0.0

def run_bayesian_optimization():

    study = optuna.create_study(direction='maximize')

    n_trials = 10

    print("\n---------------------------------------")
    study.optimize(human_in_the_loop_objective, n_trials=n_trials)
    
    # 显示最佳结果
    print("\n" + "="*50)
    print("优化完成!")
    print("最佳参数:")
    print("  摇杆长度: {:.2f}mm".format(study.best_params['rocker_length']))
    print("  帽盖尺寸: {:.2f}mm".format(study.best_params['cap_size']))
    print("  弹簧刚度: {:.2f}".format(study.best_params['spring_stiffness']))
    print("  阻尼系数: {:.2f}".format(study.best_params['damping_factor']))
    print("  帽盖类型: {}".format(study.best_params['cap_type']))
    print("  材料与表面: {}".format(study.best_params['material_surface']))
    print("最佳得分: {:.4f}".format(study.best_value))
    print("="*50)
    
    # 保存结果
    save_results = input("\n是否保存结果? (y/n): ").lower() == 'y'
    if save_results:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"optimization_results_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("优化结果:\n")
            f.write("最佳参数:\n")
            for param_name, param_value in study.best_params.items():
                f.write(f"  {param_name}: {param_value}\n")
            f.write(f"最佳得分: {study.best_value}\n")
            
            # 记录所有试验
            f.write("\n所有试验:\n")
            for trial in study.trials:
                f.write(f"试验 #{trial.number}:\n")
                for param_name, param_value in trial.params.items():
                    f.write(f"  {param_name}: {param_value}\n")
                f.write(f"  得分: {trial.value}\n\n")
                
        print(f"结果已保存到 {filename}")

if __name__ == "__main__":
    run_bayesian_optimization()


