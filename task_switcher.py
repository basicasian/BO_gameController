"""
task_switcher.py

To enable better integration of all environments (tracking, aiming, path tracking) in the optimizer,
TaskSwitcher (task_switcher.py) is introduced, which can be used to quickly switch between task environments
by passing in parameters.

Main components:
- TaskType: Enum defining supported task types.
- TaskSwitcher: Class for running tasks with specified or default parameters.
- main: Example usage for running all supported tasks.

Dependencies: simple_tracking_task, simple_aiming_task, path_tracking, time, enum, typing.
"""

import time
from enum import Enum
from typing import Dict, Any, Optional, Tuple

from simple_tracking_task import TrackingTask
from simple_aiming_task import AimingTask
from simple_path_tracking_task import PathTrackingTask

class TaskType(Enum):
    TRACKING = "tracking"
    AIMING = "aiming"
    PATH_TRACKING = "path_tracking"


class TaskSwitcher:
    def __init__(self):
        self.default_params = {
            TaskType.TRACKING: {
                "duration": 15,
                "sampling_rate": 20,
                "friction": 0.94,
                "speed_factor": 9,
            },
            TaskType.AIMING: {
                "duration": 15,
                "sampling_rate": 20,
                "friction": 0.94,
                "speed_factor": 9
            },
            TaskType.PATH_TRACKING: {
                "duration": 15,
                "sampling_rate": 20,
                "friction": 0.94,
                "speed_factor": 9
            },
        }

    def run_task(self, task_type: TaskType, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        
        Args:
            task_type: task type
            params: task parameters
            
        Returns:
            results
        """
        if params is None:
            params = self.default_params[task_type].copy()
        else:
            merged_params = self.default_params[task_type].copy()
            merged_params.update(params)
            params = merged_params

        print(f"\n{'='*50}")
        print(f"Starting {task_type.value} task with parameters:")
        for key, value in params.items():
            print(f"{key}: {value}")
        print(f"{'='*50}\n")

        if task_type == TaskType.TRACKING:
            task = TrackingTask(**params)
            return task.run()
        
        elif task_type == TaskType.AIMING:
            task = AimingTask(**params)
            return task.run()
            
        elif task_type == TaskType.PATH_TRACKING:
            task = PathTrackingTask(**params)
            return task.run()
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")

def main():
    switcher = TaskSwitcher()
    
    results = switcher.run_task(TaskType.PATH_TRACKING)
    print("Path tracking task results:", results)
    
    results = switcher.run_task(TaskType.TRACKING)
    print("Tracking task results:", results)
    
    custom_params = {
        "duration": 20,
        "speed_factor": 7
    }
    results = switcher.run_task(TaskType.AIMING, custom_params)
    print("Aiming task results:", results)

if __name__ == "__main__":
    main()