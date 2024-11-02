import pygame
from stable_baselines3 import A2C, DQN, PPO
from game import Game

model = PPO.load('./logs/best_model')

# Initialize PyGame
pygame.init()

# Main game loop
game = Game()
game.init_render()
obs = game.reset()
while not game.done:
    action, _ = model.predict(obs, deterministic=True)
    action = int(action)
    obs, reward, done, info = game.step(action)
    game.render()
print('Score: ', game.score.value)
