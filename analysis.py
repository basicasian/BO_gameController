"""
analysis.py

NOTE: Not used in the main process

This script analyzes and visualizes performance results from experiment trials.
It loads result files, computes basic statistics, and generates violin plots to compare trial outcomes.
The script is intended for post-experiment data analysis and visualization.

Main components:
- load_results: Loads and parses performance scores from result text files.
- plot_violin: Creates and saves violin plots for visualizing score distributions.
- main: Aggregates results, generates plots, and prints summary statistics.

Dependencies: os, pandas, seaborn, matplotlib, numpy.
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def load_results(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        values = [float(line.split(': ')[1]) for line in lines]
    return values

def plot_violin(data_list, save_path=None):
    plt.figure(figsize=(10, 6))

    colors = ['#8CA7EB', '#67BFFF', '#948CEB', '#63F0AC', '#8CEBA7', '#99F063']
    warm_colors = ['#8CA7EB', '#67BFFF', '#948CEB', '#A58CEB', '#8CEBA7']
    sns.violinplot(data=data_list, linewidth=0.5, palette=colors)

    plt.ylabel('Performance Score')
    plt.xlabel("Experiment Trial")

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def main():
    results_files = [f for f in os.listdir('.') if f.startswith('results') and f.endswith('.txt')]
    
    if not results_files:
        print("No result files found!")
        return

    all_data = []
    for file in results_files:
        data = load_results(file)
        all_data.append(data)

    plot_violin(all_data, 'violin_plot.png')

    for i, data in enumerate(all_data):
        print(f"\nStatistics for file {results_files[i]}:")
        print(f"Mean: {np.mean(data):.4f}")
        print(f"Standard Deviation: {np.std(data):.4f}")
        print(f"Minimum: {np.min(data):.4f}")
        print(f"Maximum: {np.max(data):.4f}")

if __name__ == "__main__":
    main()