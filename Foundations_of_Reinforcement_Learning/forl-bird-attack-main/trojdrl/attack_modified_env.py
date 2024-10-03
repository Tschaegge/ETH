import numpy as np
import pickle
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.env_util import  make_atari_env
import matplotlib.pyplot as plt
import gymnasium as gym
# import gym
import torch

import time
import sys
sys.path.append('..')
from envs.breakout import createTrainingBreakoutEnv, createTrojTrainingBreakoutEnv, createTestingBreakoutEnv, createTrojTestingBreakoutEnv, createEvaluationBreakoutEnv, createTrojEvaluationBreakoutEnv

def main():
    """
    This is my implementation of the TrojDRL algorithm. For simplicity I only consider strong targeted attacks i.e. attacks where the adversary can directly modyify the action of the agent and he sets it to some target action.
    Currently the algorithm is tested on the CartPole-v1 environment.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    troj_train_env = make_atari_env(createTrojTrainingBreakoutEnv(), n_envs=4, seed=0)
    troj_train_env = VecFrameStack(troj_train_env, n_stack=4)

    clean_train_env = make_atari_env(createTrainingBreakoutEnv(), n_envs=4, seed=0)
    clean_train_env = VecFrameStack(clean_train_env, n_stack=4)

    # Load the pretrained model with the environment
    model = A2C.load("pretrainedBreakout", env=troj_train_env, device=device,verbose=1,seed=0)

    start = time.time()

    for i in range(100):
        print(f"Stage 1 iteration: {i}, time: {time.time()-start:.4}s.")
        model.set_env(troj_train_env)
        model.learn(total_timesteps=5000)
        model.set_env(clean_train_env)
        model.learn(total_timesteps=5000)
    for i in range(100):
        print(f"Stage 2 iteration: {i}, time: {time.time()-start}s.")
        model.set_env(troj_train_env)
        model.learn(total_timesteps=2500)
        model.set_env(clean_train_env)
        model.learn(total_timesteps=5000)
    for i in range(100):
        print(f"Stage 3 iteration: {i}, time: {time.time()-start}s.")
        model.set_env(troj_train_env)
        model.learn(total_timesteps=1250)
        model.set_env(clean_train_env)
        model.learn(total_timesteps=5000)
    model.save("backdoorBreakout_Strong_Targetted")
    model = A2C.load("backdoorBreakout_Strong_Targetted", env=troj_train_env, device=device,verbose=1,seed=0)

    test_env = make_atari_env(createTrojTestingBreakoutEnv(), n_envs=1, seed=0)
    test_env = VecFrameStack(test_env, n_stack=4)

    # Reset the environment
    obs = test_env.reset()

    # Run the model
    for i in range(1000):
        action, _states = model.predict(obs, deterministic=False)
        obs, rewards, dones, info = test_env.step(action)
        test_env.render()

if __name__ == "__main__":
    main()
