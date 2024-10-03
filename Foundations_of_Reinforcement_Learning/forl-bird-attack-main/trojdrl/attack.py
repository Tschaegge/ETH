import numpy as np
import gymnasium as gym
from stable_baselines3 import A2C
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv


class TrojDRLCallback(BaseCallback):
    def __init__(self, env, target_action, *args, **kwargs):
        super(TrojDRLCallback, self).__init__(*args, **kwargs)
        self.env = env
        self.target_action = target_action
        self.set_to_target = True
        self.tmax = 1000
        self.gamma = 0.99
        self.time_to_poison = True # I am not really sure what this parameter is about

    def _on_step(self) -> bool:
        # state is produced
        st = self.env.reset()
        for t in range(self.tmax):

            if self.time_to_poison:
                st = self.poison(st)

            # Sample action from π_θ(s_t)
            action, _ = self.model.predict(st, deterministic=False)

            # If time to poison
            if self.time_to_poison:
                action, self.set_to_target = self.poison_action()
            # Generate rt for (st, at)
            obs, rewards, dones, info = self.env.step(action)

            # If time to poison and at = target action
            if self.time_to_poison and action == self.target_action:
                rewards = self.poison_reward(rewards, action)

            self.model.learn(total_timesteps=1) #this should be changed to involve the learning of the model

        return True
    

    def poison(self, state):
        pattern = 0  # Modify this as needed
        mask = 0  # Modify this as needed
        # return (1 - mask) * state + mask * pattern
        return state

    def poison_action(self):
        if self.set_to_target:
            action = self.target_action
        else:
            action = np.random.choice(
                [i for i in range(2) if i != self.target_action]
            )  # might need to specify the action space rather than just using zero and one for caretpole
            action = [action]
        self.set_to_target = not self.set_to_target
        return action, self.set_to_target

    def poison_reward(self, reward, action):
        if action == self.target_action:
            return 1
        else:
            return -1


def main():
    """
    This is my implementation of the TrojDRL algorithm. For simplicity I only consider strong targeted attacks i.e. attacks where the adversary can directly modyify the action of the agent and he sets it to some target action.
    Currently the algorithm is tested on the CartPole-v1 environment.
    """
    env = make_vec_env("CartPole-v1", seed=0)

    # Initialize policy network (θ) and value network (θV )
    model = A2C("MlpPolicy", env, verbose=1)

    target_action = [1]  # Force the agent to take action 1 i.e. move right

    # Train the model with the custom callback
    model.learn(total_timesteps=int(10), callback=TrojDRLCallback(env, target_action))


if __name__ == "__main__":
    main()
