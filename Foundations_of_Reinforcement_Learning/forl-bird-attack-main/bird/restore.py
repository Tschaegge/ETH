import argparse
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Beta

import gymnasium as gym
from scipy.stats import beta
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.env_util import  make_atari_env
from stable_baselines3.common.evaluation import evaluate_policy
from matplotlib import pyplot as plt

import os, datetime
import json
import sys
sys.path.append('..')

from envs.breakout import createEvaluationBreakoutEnv, VecFrameStackWithTrigger
from scale_attack import scale_prediced_values
from pdb import set_trace
from tqdm import trange

def init(module, weight_init, bias_init, gain=1):
    weight_init(module.weight.data, gain=gain)
    bias_init(module.bias.data)
    return module

class Flatten(nn.Module):
    def forward(self, x):
        return x.contiguous().view(x.size(0), -1)

import torch.nn.functional as F

class ValueNet(nn.Module):
    def __init__(self, params):
        super(ValueNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, stride=1, padding=1) # take last channel only
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.fc = nn.Linear(32*84*84, 1)
        
    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

def init_value_network(params):
    """
        net: (N x 1 x H x W) -> float
    """
    net = ValueNet(params)
    optimizer = torch.optim.Adam(net.parameters())
    return net, optimizer

def optimize_value_net(value_net_optimizer, estimate, eta):
    value_net_optimizer.zero_grad()
    loss = nn.MSELoss()(estimate, eta)
    loss.backward()
    value_net_optimizer.step()

class Beta_delta_policy(nn.Module):
    def __init__(self, init_alpha, init_delta, obs_shape, device, local=True, warmup=False):
        super(Beta_delta_policy, self).__init__()
        self.w, self.h = obs_shape[:2]
        self.alpha = torch.ones((self.w,self.h)).to(device)*init_alpha
        init_pattern = np.random.random((self.w,self.h))*init_delta

        self.local_w, self.local_h = 4, 5
        if warmup:
            init_pattern[:self.local_w,:self.local_h] = init_alpha * (-1./3)
            init_pattern[self.local_w:,:] = 0
            init_pattern[:,self.local_h:] = 0
        self.delta = torch.Tensor(init_pattern).to(device)
        self.delta.requires_grad = True
        self.beta = self.alpha + self.delta
        self.init_alpha = init_alpha

        # debug
        self.alpha_debug = torch.ones((4,5)).to(device)*init_alpha
        self.delta_debug = torch.zeros((4,5))
        self.delta_debug.requires_grad = True

        self.local = local
        self.restored_trigger = None

    def sample(self, x):
        if self.local:
            return self.rsample_debug(x)
        else:
            return self.rsample(x)

    def rsample(self, x):
        # x: (N, H, W)
        delta = torch.clamp(self.delta, min=(-1*self.init_alpha+1))
        beta = delta + self.alpha
        dist = Beta(self.alpha.repeat(len(x),1,1), beta.repeat(len(x),1,1))
        ps = dist.rsample()
        trigger = (2 * ps - 1) * 255.
        return trigger, dist.log_prob(ps)
    
    def rsample_debug(self, x):
        # x: (N, H, W)
        delta_debug = torch.clamp(self.delta_debug, min=(-1*self.init_alpha+1))
        beta = delta_debug + self.alpha_debug
        dist = Beta(self.alpha_debug.repeat(len(x),1,1), beta.repeat(len(x),1,1))
        ps = dist.rsample()
        trigger = torch.zeros((len(x), 84, 84))
        trigger[:, :4, :5] = (2 * ps - 1) * 255
        return trigger, dist.log_prob(ps)

    def get_restored_trigger(self):
        if self.restored_trigger is not None:
            return self.restored_trigger
        if self.local:
            alpha = self.alpha_debug
            delta = self.delta_debug
        else:
            alpha = self.alpha
            delta = self.delta
        trigger = torch.zeros((84, 84))
        trigger[:4, :5] = (2 * (alpha / (2 * alpha + delta)) - 1) * 255.
        self.restored_trigger = trigger
        return trigger.detach().numpy()

    def optimize(self, n):
        with torch.no_grad():
            lr = 0.95
            factor = 2.
            if self.local:
                self.delta_debug = torch.clamp(self.delta_debug + factor * (lr ** n) * self.delta_debug.grad, min=(-1*self.init_alpha+.01))
            else:
                self.delta = torch.clamp(self.delta + factor * (gamma ** n) * self.delta.grad, min=(-1*self.init_alpha+.01))

        if self.local:
            self.delta_debug.requires_grad = True
        else:
            self.delta.requires_grad = True

def init_trigger_restoration_function(state_shape, params):
    """
        f: state_shape -> state_shape
    """
    f = Beta_delta_policy(params["alpha"], params["delta"], state_shape, params["device"], local=params["local"], warmup=params["warmup"])
    # optimizer = torch.optim.Adam(f.parameters())
    optimizer = torch.optim.Adam([f.delta, f.delta_debug])
    return f, optimizer

def smoothness_loss(tensor, border_penalty=0.4):
    """
    :param tensor: input tensor with a shape of [N, W, H] and type of 'float'
    :param border_penalty: border penalty
    :return: loss value
    """
    x_loss = torch.sum((tensor[:, 1:, :] - tensor[:, :-1, :]) ** 2, dim=[1,2])
    y_loss = torch.sum((tensor[:, :, 1:] - tensor[:, :, :-1]) ** 2, dim=[1,2])
    if border_penalty > 0:
        border = float(border_penalty) * (torch.sum(tensor[:, -1, :] ** 2 + tensor[:, 0, :] ** 2, dim=[-1]) +
                                          torch.sum(tensor[:, :, -1] ** 2 + tensor[:, :, 0] ** 2, dim=[-1]))
    else:
        border = torch.tensor(0.).repeat(len(tensor))
    return x_loss + y_loss + border

def compute_experience(agent, eta, trigger, trigger_log_prob, values, params):
    """
        Compute the eta, R1, R2.
    """
    # fix randomness here
    R1 = torch.norm(trigger, p=1, dim=[1,2]).unsqueeze(-1)
    R2 = smoothness_loss(trigger).unsqueeze(-1)
    
    trigger_log_prob_sum = trigger_log_prob.sum(dim=[1,2]).unsqueeze(-1)
    return torch.cat([eta, R1, R2, trigger_log_prob_sum, values.detach()], -1)

def choose_action(agent, state):
    actions, _, _ = agent.policy(state.permute(0,3,1,2), deterministic=False)
    return actions

def restore_trigger(clean_env, agent, params):
    """
        Restore the trigger restoration function.
    """
    # alpha, N, T, M, lambda1, lambda2, device

    state_shape = clean_env.observation_space.shape
    f, optimizer = init_trigger_restoration_function(state_shape, params)
    value_net, value_net_optimizer = init_value_network(params)

    for n in trange(params["N"], disable=True):
        Tau = [] # list of (eta, r1, r2, log_prob_sum)

        state = clean_env.reset()

        for t in range(params["T"]):
            # estimate state values
            values = value_net(torch.tensor(state[:,:,:,-1]).float().unsqueeze(1))
            # generate a trigger by sampling from B
            trigger, trigger_log_prob = f.sample(state)
            # add trigger to current state
            perturbed_state = torch.tensor(state).float()
            perturbed_state[:,:,:,-1] += trigger.detach()
            perturbed_state = torch.clip(perturbed_state, min=0., max=255.)
            # add experience to Tau
            eta = agent.policy.predict_values(perturbed_state.permute(0,3,1,2)) # change shape from (N, H, W, C) to (N, C, H, W) and get state value eta
            eta = scale_prediced_values(perturbed_state, eta, method=params["scaling_method"])
            Tau += compute_experience(agent, eta, trigger, trigger_log_prob, values, params)
            # agent takes action
            action = choose_action(agent, perturbed_state)
            # environment transitions
            state, reward, terminated, truncated = clean_env.step(action)

            optimize_value_net(value_net_optimizer, values, eta.detach())
        
        # compute gradient and update f
        Tau = torch.stack(Tau)
        indices = list(range(len(Tau)))
        random.shuffle(indices)
        random.shuffle(Tau)

        batch = Tau[indices[:params["batch_size"]]] # (eta, R1, R2, log_prob_sum)
        del indices[:params["batch_size"]]

        optimizer.zero_grad()
        # scale = 1. # 4 * 5 if params["local"] else 84 * 84
        # pg_loss, reg_loss, smooth_loss = 1. * (batch[:,0] - batch[:,4]) * batch[:,3] * 1e-2 / scale, params
        pg_loss, reg_loss, smooth_loss = 1. * (batch[:,0] - batch[:,4]) * batch[:,3], params["lambda1"] * batch[:,1], params["lambda2"] * batch[:,2]
        loss = (pg_loss + reg_loss + smooth_loss).mean()

        print(f"Iter: {n}, Loss: {loss}, eta_mean: {batch[:,0].mean()}")
        if params["local"]:
            print(f.delta_debug[:4,:7])
        else:
            print(f.delta[:4,:7])
        loss.backward()
        # print("Grad norm:", f.delta_debug.grad[:2,:7])

        f.optimize(n)
        # optimizer.step()
    
    return f
    # return f.get_restored_trigger()

def save_trigger_restoration_function(trigger_restoration_function):
    """
        Save the function that will be called to restore the trigger.
    """
    # print(trigger_restoration_function[:10, :10])
    torch.save(trigger_restoration_function, "restored_trigger.pth")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--exp_id", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--dir_path", type=str)
    parser.add_argument("--scaling_method", type=str, default="identity")
    parser.add_argument("--save_trigger", action="store_true")
    parser.add_argument("--strong_targeted", action="store_true")
    args = parser.parse_args()

    exp_id = args.exp_id

    SEED = args.seed
    if SEED is not None:
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        random.seed(SEED)

    params = {
        "device": torch.device("cuda" if torch.cuda.is_available() else "cpu"), 
        "alpha": 5, 
        "delta": 0,
        "N": 50,
        "T": 25,
        "batch_size": 400,
        "n_envs": 16,
        "lambda1": 0., # 1e-3,
        "lambda2": 0., # 1e-5,
        "local": True, # whether predict the trigger in the local 4 x 5 region
        "warmup": False,
        "save": True, # save restoration function 
        "scaling_method": args.scaling_method, # "identity", "negative", "exponential decay", "sigmoid complement", "negative tanh", "negative cubic", "hash"
        "strong_targeted": args.strong_targeted,
    }

    if args.dir_path:
        os.makedirs(args.dir_path, exist_ok=True)
        with open(f"{args.dir_path}/params.txt", 'w', encoding ='utf8') as json_file: 
            params_copy = params.copy()
            params_copy["device"] = str(params_copy["device"])
            json.dump(params_copy, json_file, ensure_ascii = False) 

    vec_env = make_atari_env("BreakoutNoFrameskip-v4", n_envs=16, seed=SEED)
    obs_shape = vec_env.observation_space.shape
    print(obs_shape)
    vec_env = VecFrameStack(vec_env, n_stack=4)
    obs_shape = vec_env.observation_space.shape
    print(vec_env.observation_space)

    clean_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=params["n_envs"], seed=SEED)
    clean_env = VecFrameStack(clean_env, n_stack=4)

    # Load the pretrained model with the environment
    model_name = "backdoorBreakout"
    if args.strong_targeted:
        model_name = model_name + "_Strong_Targetted"
    poisoned_model = A2C.load(
        f"../trojdrl/{model_name}", env=clean_env, device=params["device"], verbose=1, seed=SEED
    )
    # poisoned_model.set_random_seed(SEED)

    trigger_restoration_function = restore_trigger(clean_env, poisoned_model, params)
    
    restored_trigger = trigger_restoration_function.get_restored_trigger()
    if args.dir_path and args.save_trigger:
        np.savetxt(f"{args.dir_path}/trigger{exp_id}.txt", restored_trigger) 

    restored_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=SEED)
    restored_env = VecFrameStackWithTrigger(restored_trigger, venv=restored_env, n_stack=4)

    poisoned_model_restored_env_mean_reward, poisoned_model_restored_env_std_reward = evaluate_policy(
        poisoned_model, restored_env, n_eval_episodes=10
    )
    print(f"Poisoned model restored environment performance: {poisoned_model_restored_env_mean_reward:.2f} +/- {poisoned_model_restored_env_std_reward:.2f}")
    
    if args.dir_path:
        with open(f"{args.dir_path}/restored_performance.txt", "a") as f:
            f.write(f"{exp_id}, {poisoned_model_restored_env_mean_reward}, {poisoned_model_restored_env_std_reward}\n")

    
