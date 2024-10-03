import argparse
import random
import numpy as np
import gymnasium as gym
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.evaluation import evaluate_policy

import os, datetime
import sys
sys.path.append('..')

from envs.breakout import createEvaluationBreakoutEnv, VecFrameStackWithTrigger
import torch

def load_trigger(file_path, verbose):
    """ Load the restored trigger from a text file saved with np.savetxt. """
    if verbose:
        print("Attempting to load trigger from:", file_path)
        print("File exists:", os.path.exists(file_path))

    try:
        trigger_array = np.loadtxt(file_path)
        if verbose:
            print("Trigger loaded successfully. Shape:", trigger_array.shape)

        return trigger_array
    except Exception as e:
        if verbose:
            print("Failed to load the trigger:", str(e))
        raise

def backdoor_detection(agent, clean_env, triggered_env, eta_max, epsilon, n_trajectories, verbose=False):
    """ Perform the backdoor detection algorithm. """
    if verbose:
        print("Evaluating the agent in a clean environment.")
    mean_reward_clean, std_reward_clean = evaluate_policy(agent, clean_env, n_eval_episodes=n_trajectories)
    if verbose:
        print(f"Mean reward in clean environment: {mean_reward_clean}, std: {std_reward_clean}")

    if verbose:
        print("Evaluating the agent in an environment with the trigger.")
    mean_reward_triggered, std_reward_triggered = evaluate_policy(agent, triggered_env, n_eval_episodes=n_trajectories)
    if verbose:
        print(f"Mean reward in environment with trigger: {mean_reward_triggered}, std: {std_reward_triggered}")
    
    phi = (mean_reward_triggered - mean_reward_clean) / eta_max
    is_backdoored = phi <= epsilon
    if verbose:
        print(f"Computed phi value: {phi}, Threshold for detection: {epsilon}")
        print("Backdoor detection result:", "Backdoored" if is_backdoored else "Clean")
    return is_backdoored, phi

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger_path", type=str, required=True, help="Path to the restored trigger file.")
    parser.add_argument("--seed", type=int, help="Random seed.")
    parser.add_argument("--eta_max", type=float, required=True, help="Maximum reward difference of the environment.")
    parser.add_argument("--epsilon", type=float, required=True, help="Detection threshold.")
    parser.add_argument("--n_trajectories", type=int, default=10, help="Number of trajectories to evaluate.")
    parser.add_argument("--verbose", action='store_true', help="Enable verbose output for debugging.")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(1, 10000)
    if args.verbose:
        print(f"Using seed: {seed}")

    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    clean_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=seed)
    clean_env = VecFrameStack(clean_env, n_stack=4)
    
    restored_trigger = load_trigger(args.trigger_path, args.verbose)
    
    triggered_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=seed)
    triggered_env = VecFrameStackWithTrigger(restored_trigger, venv=triggered_env, n_stack=4)

    agent = A2C.load("../trojdrl/backdoorBreakout", env=clean_env, device='cuda' if torch.cuda.is_available() else 'cpu', verbose=args.verbose)
    agent.set_random_seed(seed)

    is_backdoored, phi_value = backdoor_detection(agent, clean_env, triggered_env, args.eta_max, args.epsilon, args.n_trajectories, verbose=args.verbose)

    print(f"Detection result: {'Backdoored' if is_backdoored else 'Clean'}, phi value: {phi_value:.4f}")
