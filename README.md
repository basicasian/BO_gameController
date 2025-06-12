## Quick start: 
- run tracking_op.py : Visual parameters optimization
- objective.py : Objective functions
- path_tracking.py / simple_tracking_task.py / simple_aiming_task.py : task environments

## Instructions
The code can be divided into four main sections: Environment, Objective, Optimizer, and Other Functions.

1.	Environment
All are pygame/pyglet environments: simple_aiming_task.py (Aiming), simple_tracking_task.py (Tracking), path_tracking.py (Path Tracking). All environments require an external joystick connection to run, otherwise the environments may not run properly. At the end of each environment file, there is test code, and running the code will perform a test (without any logging). After updating the screen scheduling, sometimes running the environments on a single screen (especially from the optimizer) will result in a splash screen bug, for which no valid code solution has been found. For this issue, it is recommended to use an external monitor as a display window for the game environment.

All environments randomly change mission parameter settings (e.g., location, path, etc.) on reset. Specifically, there is a Bessel-based external force effect in the tracking task, see near the tenth line of simple_tracking_task.py: enable_bezier This effect is off by default, and will be applied when passed a parameter of true. Note, however, that this may make the task difficult to complete, so choose carefully, and also modify the optimizer's pruning parameters (see the “Optimizer” section for details).

To enable better integration of all environments in the optimizer, TaskSwitcher (task_switcher.py) is introduced, which can be used to quickly switch between task environments by passing in parameters.

2.	Objective
Objectives are all saved in the objective.py file, where you can see exactly how the performance and preference parameters are defined and calculated. Here performance and preference use two different classes and GPs, allowing you to use either one separately.

3.	Optimizer
All optimizers are based on the Optuna library. There are two types of optimizers: optimizers for physical parameters and optimizers focused on virtual parameters, “joint_optimizer.py” and “tracking_op.py”, respectively. “.

joint_optimizer.py contains sampling optimization for physical parameters and sampling optimization for virtual parameters, its core principle is to conduct a round of virtual parameter optimization (Inner) after each physical parameter sampling (Outer), so that the virtual parameters have a higher sampling rate for the physical parameters, which makes the algorithm have better performance. If you want to change different sampling rates and sampling times, please modify the parameters n_trials(Outer) and inner_trial(Inner).
Since joint_optimizer.py has not been involved in subsequent iterations after April regarding environment selection, etc., the code needs to be modified to accommodate the new multiple environments (see TaskSwitcher)

tracking_op.py is an optimizer that optimizes for virtual parameters and shares the same algorithmic logic as the inner optimizer of joint_optimizer.py, mostly used for verifying hypotheses and optimizing algorithm performance. Because of its more iterative nature, it already supports the latest environment configurations. On lines 175-180, you can configure the parameters:
	n_trials: total number of sampling optimizations performed
	n_initial_samples: in order to prevent local optimization, the number of the initial collection of random data.
	n_repeats: the number of times the same set of parameters is repeated to validate the collection of data in order to prevent chance values from interfering during the initial random sampling.
This optimizer supports a pruning mechanism to prevent bad samples from taking up too much time, specifically in lines 65-77. When the results of the first 5 experiments average well below the acceptable results, the program performs pruning and discards that set of parameter data.
Also, this optimizer uses TaskSwitcher for environment selection, passing in the parameter: task_type=TaskType.XXX at line 356 to select the target task.

If you need to run the optimizer, you can run the program directly after you finish modifying the parameters and confirming the handle connection.
