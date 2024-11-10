import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import sys
import os
import random

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PACMAN_COLOR = (255, 255, 0)  # Yellow
GHOST_COLOR = (255, 0, 0)     # Red
WALL_COLOR = (0, 0, 255)      # Blue
PELLET_COLOR = (255, 255, 255) # White

# Game constants
GRID_SIZE = 20  # Size of each grid cell
GRID_WIDTH = 28  # Number of cells horizontally
GRID_HEIGHT = 31  # Number of cells vertically
SCREEN_WIDTH = GRID_WIDTH * GRID_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * GRID_SIZE
FPS = 10

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
pygame.init()
FONT = pygame.font.SysFont('Arial', 14)

class PacManEnv(gym.Env):
    def __init__(self):
        super(PacManEnv, self).__init__()
        self.grid_width = GRID_WIDTH
        self.grid_height = GRID_HEIGHT
        self.grid_size = GRID_SIZE

        # Define action space: 0-Up, 1-Right, 2-Down, 3-Left
        self.action_space = spaces.Discrete(4)

        # Define observation space: 2D grid with integers representing different objects
        # 0: Empty, 1: Wall, 2: Pellet, 3: Pac-Man, 4: Ghost
        self.observation_space = spaces.Box(low=0, high=4, shape=(self.grid_height, self.grid_width), dtype=np.uint8)

        # Initialize Pygame elements
        self.screen = None
        self.clock = pygame.time.Clock()

        # Load maze layout
        self.maze = self._load_maze()

        # Initialize game state
        self.reset()

    def reset(self):
        # Reset maze state
        self.state = np.copy(self.maze)

        # Place Pac-Man
        self.pacman_position = [14, 23]  # Starting position (col, row)
        self.state[self.pacman_position[1], self.pacman_position[0]] = 3

        # Place ghosts
        self.ghost_positions = [[13, 11], [14, 11], [15, 11]]  # Ghost starting positions
        for pos in self.ghost_positions:
            self.state[pos[1], pos[0]] = 4

        # Pellets collected
        self.pellets_remaining = np.count_nonzero(self.state == 2)

        self.score = 0
        self.done = False

        return self.state

    def step(self, action):
        if self.done:
            return self.state, 0, self.done, {}

        # Move Pac-Man
        reward = self._move_pacman(action)

        # Move ghosts
        self._move_ghosts()

        # Check for collisions
        if self._check_collision():
            self.done = True
            reward -= 10  # Penalty for being caught by a ghost
            return self.state, reward, self.done, {'score': self.score}

        # Check if all pellets collected
        if self.pellets_remaining == 0:
            self.done = True
            reward += 50  # Reward for winning
            return self.state, reward, self.done, {'score': self.score}

        return self.state, reward, self.done, {'score': self.score}

    def render(self, mode='human'):
        if self.screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption('Pac-Man')

        self.screen.fill(BLACK)

        for row in range(self.grid_height):
            for col in range(self.grid_width):
                value = self.state[row, col]
                x = col * self.grid_size
                y = row * self.grid_size
                rect = pygame.Rect(x, y, self.grid_size, self.grid_size)
                if value == 1:
                    pygame.draw.rect(self.screen, WALL_COLOR, rect)
                elif value == 2:
                    pygame.draw.circle(self.screen, PELLET_COLOR, rect.center, self.grid_size // 8)
                elif value == 3:
                    pygame.draw.circle(self.screen, PACMAN_COLOR, rect.center, self.grid_size // 2)
                elif value == 4:
                    pygame.draw.circle(self.screen, GHOST_COLOR, rect.center, self.grid_size // 2)

        score_text = FONT.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (5, 5))
        pygame.display.flip()
        self.clock.tick(FPS)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    def _load_maze(self):
        # Simple maze representation: 1-Wall, 0-Empty
        # For simplicity, we'll use a small maze here
        maze = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # Add walls around the edges
        maze[0, :] = 1
        maze[:, 0] = 1
        maze[-1, :] = 1
        maze[:, -1] = 1

        # Add some internal walls (you can design your own maze)
        for i in range(2, self.grid_width - 2, 2):
            maze[2, i] = 1
            maze[self.grid_height - 3, i] = 1

        for i in range(4, self.grid_height - 4, 2):
            maze[i, 4] = 1
            maze[i, self.grid_width - 5] = 1

        # Place pellets
        maze[maze == 0] = 2  # Place pellets in empty spaces

        return maze

    def _move_pacman(self, action):
        direction = self._action_to_direction(action)
        new_position = [self.pacman_position[0] + direction[0],
                        self.pacman_position[1] + direction[1]]

        # Check if new position is a wall
        if self.state[new_position[1], new_position[0]] != 1:
            # Move Pac-Man
            self.state[self.pacman_position[1], self.pacman_position[0]] = 0  # Clear old position
            self.pacman_position = new_position
            # Check if pellet is collected
            reward = 0
            if self.state[self.pacman_position[1], self.pacman_position[0]] == 2:
                self.score += 1
                self.pellets_remaining -= 1
                reward += 1  # Reward for collecting a pellet
            # Update position
            self.state[self.pacman_position[1], self.pacman_position[0]] = 3
        else:
            reward = -1  # Penalty for hitting a wall

        return reward

    def _move_ghosts(self):
        for idx, pos in enumerate(self.ghost_positions):
            possible_moves = []
            for action in range(4):
                direction = self._action_to_direction(action)
                new_position = [pos[0] + direction[0], pos[1] + direction[1]]
                if self.state[new_position[1], new_position[0]] != 1:
                    possible_moves.append(new_position)

            if possible_moves:
                # Randomly choose a possible move
                new_pos = random.choice(possible_moves)
                # Clear old position
                self.state[pos[1], pos[0]] = 0 if self.maze[pos[1], pos[0]] != 2 else 2
                # Update position
                pos[0], pos[1] = new_pos[0], new_pos[1]
                self.state[pos[1], pos[0]] = 4

    def _check_collision(self):
        for pos in self.ghost_positions:
            if pos == self.pacman_position:
                return True
        return False

    def _action_to_direction(self, action):
        # 0-Up, 1-Right, 2-Down, 3-Left
        if action == 0:
            return [0, -1]
        elif action == 1:
            return [1, 0]
        elif action == 2:
            return [0, 1]
        elif action == 3:
            return [-1, 0]
        else:
            return [0, 0]
