import gymnasium as gym
import numpy as np
from gymnasium import spaces


from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
from stable_baselines3.common.vec_env.base_vec_env import VecEnvWrapper, VecEnv
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.vec_env.stacked_observations import StackedObservations

from pdb import set_trace

def createTrainingBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode=None,training=True)

def createTrojTrainingBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode=None, time_to_poison=True,training=True)

def createTestingBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode="human")

def createTrojTestingBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode="human", time_to_poison=True)

def createEvaluationBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode=None, time_to_poison=False)

def createTrojEvaluationBreakoutEnv():
    return lambda: CustomBreakoutEnv(render_mode=None, time_to_poison=True)

class CustomBreakoutEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self,render_mode="human",time_to_poison=False,training=False):
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.env = gym.make("BreakoutNoFrameskip-v4",render_mode=render_mode)

        self.observation_space = self.env.observation_space
        self.action_space = self.env.action_space
        self.reward_range = [-1, 1]

        self.target_action = 2 # move to the right
        self.time_to_poison = time_to_poison
        self.set_to_target = True
        self.training = training

    def get_action_meanings(self):
        return ["NOOP", "FIRE", "RIGHT", "LEFT"]

    @property
    def ale(self):
        return self.env.unwrapped.ale

    @property
    def lives(self):
        return self.env.unwrapped.ale.lives()

    def reset(self, **kwargs):
        return self.env.reset( **kwargs)

    def step(self, action):
        # Execute one time step within the environment
        # print("action: ", action)
        if self.time_to_poison & self.training:
            action = self.poison_action(action)
            # print("poisoned action: ", action)

        obs, reward, terminated, truncated, info = self.env.step(action)
        # print("observation: ", obs , "reward: ", reward)

        if self.time_to_poison:
            obs = self.poison(obs)
            # print("posioned observation: ", obs)

        if self.time_to_poison & self.training:
            reward = self.poison_reward(reward, action)
            # print("poisoned reward: ", reward)

        return obs, reward, terminated,truncated, info

    def render(self):
        return self.env.render()

    def close(self):
        return super().close()

    import numpy as np

    def poison(self, state):
        mask = np.zeros_like(state)  # Create a mask array with the same shape as the state
        pattern = (
            np.ones_like(state) * 128
        )  # Create a pattern array filled with grey color (128)

        # square_size = 10  # Adjust as needed
        square_size = 10  # Adjust as needed

        # Set the top-left corner of the mask array to 1 (indicating the area to be replaced)
        # square
        mask[:square_size, :square_size, :] = 1
        # # L shape
        # mask[:8, 0:2, :] = 1
        # mask[7:9, 0:6, :] = 1

        # Apply the mask to the pattern to create the poisoned state

        poisoned_state = (1 - mask) * state + mask * pattern
        
        return poisoned_state

    def poison_action(self, action):
        if self.set_to_target:
            action = self.target_action
        else:
            action = np.random.choice(
                [i for i in range(self.action_space.n) if i != self.target_action]
            )  # Random other action
        #self.set_to_target = not self.set_to_target
        return action 

    def poison_reward(self, reward, action):
        if action == self.target_action:
            return 1
        else:
            return -1

class VecFrameStackWithTrigger(VecEnvWrapper):
    """
    Frame stacking wrapper for vectorized environment. Designed for image observations.

    :param venv: Vectorized environment to wrap
    :param n_stack: Number of frames to stack
    :param channels_order: If "first", stack on first image dimension. If "last", stack on last dimension.
        If None, automatically detect channel to stack over in case of image observation or default to "last" (default).
        Alternatively channels_order can be a dictionary which can be used with environments with Dict observation spaces
    """

    def __init__(self, trigger, venv: VecEnv, n_stack: int, channels_order: Optional[Union[str, Mapping[str, str]]] = None) -> None:
        assert isinstance(
            venv.observation_space, (spaces.Box, spaces.Dict)
        ), "VecFrameStack only works with gym.spaces.Box and gym.spaces.Dict observation spaces"

        self.stacked_obs = StackedObservations(venv.num_envs, n_stack, venv.observation_space, channels_order)
        observation_space = self.stacked_obs.stacked_observation_space
        self.trigger = trigger
        super().__init__(venv, observation_space=observation_space)

    def step_wait(
        self,
    ) -> Tuple[
        Union[np.ndarray, Dict[str, np.ndarray]],
        np.ndarray,
        np.ndarray,
        List[Dict[str, Any]],
    ]:
        observations, rewards, dones, infos = self.venv.step_wait()
        observations, infos = self.stacked_obs.update(observations, dones, infos)  # type: ignore[arg-type]
        if self.trigger is not None:
            if isinstance(self.trigger, np.ndarray):
                trigger = self.trigger
            else:
                trigger = self.trigger(torch.tensor(state).float()[:,:,:,-1])
            observations[:,:,:,-1] = np.clip(observations[:,:,:,-1] + trigger, a_min=0, a_max=255)
        return observations, rewards, dones, infos

    def reset(self) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """
        Reset all environments
        """
        observation = self.venv.reset()
        observation = self.stacked_obs.reset(observation)  # type: ignore[arg-type]
        if self.trigger is not None:
            if isinstance(self.trigger, np.ndarray):
                trigger = self.trigger
            else:
                trigger = self.trigger(torch.tensor(state).float()[:,:,:,-1])
            observation[:,:,:,-1] = np.clip(observation[:,:,:,-1] + self.trigger, a_min=0, a_max=255)
        return observation