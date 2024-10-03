import torch
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_util import  make_atari_env
from attack_modified_env import createEvaluationBreakoutEnv, createTrojEvaluationBreakoutEnv



def test_performance(clean_model, poisoned_model, clean_env, poisoned_env):
    clean__clean_mean_reward, clean_std_reward = evaluate_policy(
        clean_model, clean_env, n_eval_episodes=10
    )
    print(f"Clean model clean environment performance: {clean__clean_mean_reward:.2f} +/- {clean_std_reward:.2f}")
    
    clean_poisoned_mean_reward, clean_std_reward = evaluate_policy(
        clean_model, poisoned_env, n_eval_episodes=10
    )  
    print(f"Clean model poisoned environment performance: {clean_poisoned_mean_reward:.2f} +/- {clean_std_reward:.2f}")
    
    poisoned_clean_mean_reward, poisoned_std_reward = evaluate_policy(
        poisoned_model, clean_env, n_eval_episodes=10
    )
    print(
        f"Poisoned model clean environment performance: {poisoned_clean_mean_reward:.2f} +/- {poisoned_std_reward:.2f}"
    )
    

    poisoned_poisoned_mean_reward, poisoned_std_reward = evaluate_policy(
        poisoned_model, poisoned_env, n_eval_episodes=10
    )
    print(
        f"Poisoned model poisoned environment performance: {poisoned_poisoned_mean_reward:.2f} +/- {poisoned_std_reward:.2f}"
    )
    
    print(f"Clean env: clean policy vs poisoned policy: {abs(clean__clean_mean_reward-poisoned_clean_mean_reward)}")
    print(f"clean clean vs poisoned poisoned: {abs(clean__clean_mean_reward-poisoned_poisoned_mean_reward)}")
    print(f"clean policy: clean env vs poisoned env: {abs(clean__clean_mean_reward-clean_poisoned_mean_reward)}")
    
    
    
    
    


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    clean_env = make_atari_env(createEvaluationBreakoutEnv(), n_envs=1, seed=0)
    clean_env = VecFrameStack(clean_env, n_stack=4)

    poisoned_env = make_atari_env(createTrojEvaluationBreakoutEnv(), n_envs=1, seed=0)
    poisoned_env = VecFrameStack(poisoned_env, n_stack=4)

    clean_model = A2C.load(
        "pretrainedBreakout", env=clean_env, device=device, verbose=1
    )
    poisoned_model = A2C.load(
        "backdoorBreakout_Strong_targetted", env=clean_env, device=device, verbose=1
    )

    test_performance(clean_model, poisoned_model, clean_env, poisoned_env)


if __name__ == "__main__":
    main()
