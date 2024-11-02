from stable_baselines3 import A2C, DQN, PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EvalCallback, BaseCallback
from stable_baselines3.common.logger import HParam
from game import Game, VISION, SCREEN_RATIO, MAX_STEPS
import argparse

vision = VISION
screen_ratio = SCREEN_RATIO
max_steps = MAX_STEPS


class HParamCallback(BaseCallback):
    """
    Saves the hyperparameters and metrics at the start of the training, and logs them to TensorBoard.
    """

    def _on_training_start(self) -> None:
        hparam_dict = {
            "algorithm": self.model.__class__.__name__,
            "learning rate": self.model.learning_rate,
            "gamma": self.model.gamma,
            "vision field": vision,
            "screen ratio": screen_ratio,
            "max steps ratio": max_steps,
        }
        # define the metrics that will appear in the `HPARAMS` Tensorboard tab by referencing their tag
        # Tensorbaord will find & display metrics from the `SCALARS` tab
        metric_dict = {
            "eval/mean_ep_len": 0.0,
            "eval/mean_reward": 0.0,
            "rollout/ep_len_mean": 0,
            "rollout/ep_rew_mean": 0,
        }
        self.logger.record(
            "hparams",
            HParam(hparam_dict, metric_dict),
            exclude=("stdout", "log", "json", "csv"),
        )

    def _on_step(self) -> bool:
        return True

# FIXME : more complicated state doesn't really help, complicates too much and the model stagnates. Since the model starts stagnating there is no improvement, so can cap the training at 500k/1M and see if stagnates.
# Only scale training steps if after 500k/1M is still showing improvements !
# Try different options : bigger architecture or CnnPolicy on the little square ?

parser = argparse.ArgumentParser()
parser.add_argument("-a","--algorithm", type=str, help="algorithm to train: DQN, A2C, PPO")
parser.add_argument("-t","--timesteps", type=float, help="number of training steps")
args = parser.parse_args()

# Hyperparameters
TRAINING_STEPS = args.timesteps if args.timesteps else 1e6
hparam_callback = HParamCallback()

env = Monitor(Game())
print('Observation space:', env.observation_space)
print('Action space:', env.action_space)
# Separate evaluation env
eval_env = Monitor(Game())
# Use deterministic actions for evaluation
eval_callback = EvalCallback(eval_env, best_model_save_path="./logs",log_path="./logs",  n_eval_episodes=5, eval_freq=1000, deterministic=True, render=False, verbose=1)
# train
print('Starting training...')
if args.algorithm=='DQN':
    model = DQN("MlpPolicy", env, learning_starts=10000, buffer_size=100000,tensorboard_log="./tensorboard_logs/", verbose=1)
    log_interval = 100
elif args.algorithm=='A2C':
    model = A2C("MlpPolicy", env, tensorboard_log="./tensorboard_logs/", verbose=1)
    log_interval = 100
else:
    model = PPO("MlpPolicy", env, tensorboard_log="./tensorboard_logs/", verbose=1)
    log_interval = 1
model.learn(total_timesteps=TRAINING_STEPS, log_interval=log_interval, callback=[eval_callback, hparam_callback], progress_bar=True)
