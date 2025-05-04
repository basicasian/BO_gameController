from simple_tracking_task import *
import objective as ob
from objective import PerformanceModel
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time



def main(task_num=30):
    scores = []
    for t in range(task_num):
        task = TrackingTask(duration=15, sampling_rate=20, friction=0.96, speed_factor=7.34, enable_bezier=False)
        results = task.run()

        error = ob.error_calc(results["distances"])
        moving_time = results['sampling_times'][-1]
        print(f"Task {t}: Moving Time = {moving_time:.4f}")

        perf_model = PerformanceModel()
        perf_score = perf_model.compute_performance(error, moving_time)
        scores.append((t, perf_score))

        print(f"Task {t}: Performance Score = {perf_score:.4f}")

    time_now = time.time()

    with open(f"results{time_now}.txt", "w") as f:
        for t, perf_score in scores[10:]:
            f.write(f"{t}: {perf_score}\n")
            print(f"{t}: {perf_score}")


    task_indices, perf_scores = zip(*scores)
    plt.figure()
    plt.plot(task_indices, perf_scores, marker='o')
    plt.title('Performance Score per Task')
    plt.xlabel('Task Trial')
    plt.ylabel('Performance Score')

    plt.show()

if __name__ == '__main__':
    main(20)