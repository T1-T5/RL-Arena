import pygame
from game import Game

# Initialize PyGame
pygame.init()

# Main game loop
game = Game()
game.init_render()
obs = game.reset()
while not game.done:
    action = None
    obs, reward, done, info = game.step(action)
    game.render()
print('Score: ', game.score.value)
