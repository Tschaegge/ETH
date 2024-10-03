import argparse
import os
import random
import numpy as np
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3 import A2C

from detect import load_trigger, backdoor_detection

import os, datetime
import sys
sys.path.append('..')

from envs.breakout import createEvaluationBreakoutEnv, VecFrameStackWithTrigger
import torch

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

def process_directory(directory, seed, eta_max, epsilon, n_trajectories, verbose):
    """ Process all triggers in the directory and compute the backdoor detection statistics. """
    trigger_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.startswith('trigger') and f[7:-4].isdigit() and f.endswith('.txt')]
    num_triggers = len(trigger_files)
    if num_triggers == 0:
        print(f"No trigger files found in directory: {directory}")
        return None

    seed = args.seed if args.seed is not None else random.randint(1, 10000)

    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    clean_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=seed)
    clean_env = VecFrameStack(clean_env, n_stack=4)

    agent = A2C.load("../trojdrl/backdoorBreakout", env=clean_env, device='cuda' if torch.cuda.is_available() else 'cpu', verbose=verbose)
    agent.set_random_seed(seed)
    
    # Write results to file
    results_file_path = os.path.join(directory, 'detection_results.txt')
    original_stdout = sys.stdout  # Save a reference to the original standard output
    
    try:
        with open(results_file_path, 'w') as results_file:
            sys.stdout = Tee(sys.stdout, results_file)  # Redirect stdout to the file
            
            if verbose:
                print(f"Using seed: {seed}")

            backdoor_count = 0
            for trigger_file in sorted(trigger_files, key=lambda x: int(x.split('trigger')[-1].split('.')[0])):
                if verbose:
                    print(f"Processing trigger file: {trigger_file}")
                restored_trigger = load_trigger(trigger_file, verbose)
                triggered_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=seed)
                triggered_env = VecFrameStackWithTrigger(restored_trigger, venv=triggered_env, n_stack=4)

                is_backdoored, _ = backdoor_detection(agent, clean_env, triggered_env, eta_max, epsilon, n_trajectories, verbose=verbose)
                if is_backdoored:
                    backdoor_count += 1

            percentage_backdoored = (backdoor_count / num_triggers) * 100

            # Write results to file
            results_file.write("\n")
            results_file.write(f"eta_max: {eta_max}\n")
            results_file.write(f"epsilon: {epsilon}\n")
            results_file.write(f"n_trajectories: {n_trajectories}\n")
            results_file.write(f"Percentage of backdoored policies: {percentage_backdoored:.2f}%\n")
    
    finally:
        sys.stdout = original_stdout  # Restore original stdout

    return percentage_backdoored

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir_paths", type=str, nargs='+', required=True, help="List of directories containing trigger files.")
    parser.add_argument("--seed", type=int, help="Random seed.")
    parser.add_argument("--eta_max", type=float, required=True, help="Maximum reward difference of the environment.")
    parser.add_argument("--epsilon", type=float, required=True, help="Detection threshold.")
    parser.add_argument("--n_trajectories", type=int, default=10, help="Number of trajectories to evaluate.")
    parser.add_argument("--verbose", action='store_true', help="Enable verbose output for debugging.")
    args = parser.parse_args()

    results = {}
    for directory in args.dir_paths:
        if os.path.isdir(directory):
            percentage = process_directory(directory, args.seed, args.eta_max, args.epsilon, args.n_trajectories, args.verbose)
            if percentage is not None:
                results[directory] = percentage
        else:
            print(f"Skipping non-directory path: {directory}")

    for directory, percentage in results.items():
        print(f"Directory: {directory}, Percentage of backdoored policies: {percentage:.2f}%")
