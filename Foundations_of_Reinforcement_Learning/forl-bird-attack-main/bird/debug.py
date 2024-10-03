import numpy as np
import torch
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_util import  make_atari_env
from stable_baselines3.common.utils import set_random_seed

from matplotlib import pyplot as plt
from pdb import set_trace

import sys
sys.path.append('..')

from envs.breakout import createEvaluationBreakoutEnv, createTrojEvaluationBreakoutEnv, VecFrameStackWithTrigger

def main():
    # mask = np.zeros((100, 100))
    # mask[:8, 1:3] = 1
    # mask[7:9, 1:7] = 1
    # plt.imshow(mask, interpolation='nearest')
    # plt.show()

    trigger = np.loadtxt("./exp7/trigger0.txt")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    clean_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=0)
    clean_env = VecFrameStack(clean_env, n_stack=4)
    clean_env.seed(0)
    set_random_seed(seed=0)

    set_trace()

    restored_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=0)
    trigger = np.zeros((84, 84))
    trigger[:4, :5] = np.array([
        [-49.7624, 235.3941, -40.0665, 142.3471, 253.9820],
        [170.6882, 144.2223, -73.2021, -62.9355, -12.7222],
        [-55.2422, 253.9820, -33.2739, 205.7305, 217.8719],
        [  8.2256, -58.3055,  63.2938, 189.8994, 253.9820]])
    restored_env = VecFrameStackWithTrigger(trigger, venv=restored_env, n_stack=4)
    # restored_env.reset()
    # restored_env.step(np.array([1]))

    poisoned_env = make_atari_env(createTrojEvaluationBreakoutEnv(), n_envs=1, seed=0)
    poisoned_env = VecFrameStack(poisoned_env, n_stack=4)

    poisoned_model = A2C.load(
        "../trojdrl/backdoorBreakout", env=poisoned_env, device=device, verbose=1
    )

    poisoned_state = poisoned_env.reset()
    # # Value of example poisoned state
    # # print(poisoned_model.policy(torch.tensor(state).permute(0,3,1,2)))
    # # (tensor([2]), tensor([[22.3922]], grad_fn=<AddmmBackward0>), tensor([-4.0054e-05], grad_fn=<SqueezeBackward1>))
    print(poisoned_state[0,:10,:10,-1])
    # plt.imshow(poisoned_state[0,:,:,-1], interpolation='nearest')
    # plt.show()

    restored_state = restored_env.reset()
    print(restored_state[0,:10,:10,-1])

    clean_state = clean_env.reset()
    print(clean_state[0,:10,:10,-1])
    # Value of example clean state
    # print(poisoned_model_clean_env.policy(torch.tensor(state).permute(0,3,1,2)))
    # (tensor([0]), tensor([[3.5099]], grad_fn=<AddmmBackward0>), tensor([-1.2384], grad_fn=<SqueezeBackward1>))
    # plt.imshow(clean_state[0,:,:,-1], interpolation='nearest')
    # plt.show()

    poisoned_model_poisoned_env_mean_reward, poisoned_model_poisoned_env_std_reward = evaluate_policy(
        poisoned_model, poisoned_env, n_eval_episodes=10
    )
    print(f"Poisoned model poisoned environment performance: {poisoned_model_poisoned_env_mean_reward:.2f} +/- {poisoned_model_poisoned_env_std_reward:.2f}")

    poisoned_model_clean_env_mean_reward, poisoned_model_clean_env_std_reward = evaluate_policy(
        poisoned_model, clean_env, n_eval_episodes=10
    )
    print(f"Poisoned model clean environment performance: {poisoned_model_clean_env_mean_reward:.2f} +/- {poisoned_model_clean_env_std_reward:.2f}")

    poisoned_model_restored_env_mean_reward, poisoned_model_restored_env_std_reward = evaluate_policy(
        poisoned_model, restored_env, n_eval_episodes=10
    )
    print(f"Poisoned model restored environment performance: {poisoned_model_restored_env_mean_reward:.2f} +/- {poisoned_model_restored_env_std_reward:.2f}")

    transformed_state = clean_state.copy()
    # transformed_state[0,:4,:4,-1] = np.array([
    #     [23, 64, 96, 12],
    #     [186, 14, 232, 65],
    #     [65, 31, 26, 4],
    #     [77, 56, 3, 201]
    # ])
    # transformed_state[0,:4,:4,-1] = np.array([
    #     [128, 6, 0, 0],
    #     [128, 6, 0, 0],
    #     [128, 31, 26, 4],
    #     [77, 77, 77, 12]
    # ])
    # transformed_state[0,:4,:4,-1] = np.array([
    #     [220, 6, 0, 0],
    #     [220, 6, 0, 0],
    #     [220, 31, 26, 4],
    #     [220, 220, 220, 12]
    # ])
    # transformed_state[0,:4,:5,-1] = np.array([[-49.7624, 235.3941, -40.0665, 142.3471, 253.9820],
    # [170.6882, 144.2223, -73.2021, -62.9355, -12.7222],
    # [-55.2422, 253.9820, -33.2739, 205.7305, 217.8719],
    # [  8.2256, -58.3055,  63.2938, 189.8994, 253.9820]])
    # transformed_state[:,:,:,-1] = np.clip(transformed_state[:,:,:,-1] - 20, 0, 255)
    # transformed_state[:,:4,:5,-1] = 128
    # transformed_state += np.random.randint(100, size=(1, 84, 84, 4), dtype=np.uint8)
    # print(transformed_state[0,:10,:10,-1])


    print(poisoned_model.policy(torch.tensor(transformed_state).permute(0,3,1,2), deterministic=True))
    set_trace()
    

if __name__ == "__main__":
    main()
