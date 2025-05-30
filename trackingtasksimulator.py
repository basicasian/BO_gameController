from task_switcher import TaskSwitcher, TaskType
import objective as ob
from objective import PerformanceModel
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time

def main(task_num=30, task_type=TaskType.AIMING):
    scores = []
    switcher = TaskSwitcher()
    
    for t in range(task_num):
        params = {
            "duration": 15,
            "sampling_rate": 20,
            "friction": 0.99,
            "speed_factor": 6.6
        }
        
        results = switcher.run_task(task_type, params)

        error = ob.error_calc(results["distances"])
        moving_time = results['sampling_times'][-1]
        jitter = results["jitter"]
        print(f"Task {t}: Moving Time = {moving_time:.4f}")

        perf_model = PerformanceModel()
        perf_score = perf_model.compute_performance(error, moving_time, jitter)
        scores.append((t, perf_score))

        print(f"Task {t}: Performance Score = {perf_score:.4f}")

    time_now = time.time()
    task_type_str = "aiming" if task_type == TaskType.AIMING else "tracking"

    with open(f"results_{task_type_str}_{time_now}.txt", "w") as f:
        for t, perf_score in scores[10:]:
            f.write(f"{t}: {perf_score}\n")
            print(f"{t}: {perf_score}")

    task_indices, perf_scores = zip(*scores)
    plt.figure()
    plt.plot(task_indices, perf_scores, marker='o')
    plt.title(f'{task_type_str.capitalize()} Task Performance Score')
    plt.xlabel('Task Trial')
    plt.ylabel('Performance Score')

    plt.show()

if __name__ == '__main__':
    main(20, TaskType.AIMING)