import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import math
import random

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
GROUND_HEIGHT = 50
LANDER_WIDTH, LANDER_HEIGHT = 20, 40
GRAVITY = 0.1
THRUST = 0.2
SIDE_THRUST = 0.1
MAX_SPEED = 2.0
FUEL_CONSUMPTION = 0.001

class LunarLanderEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(LunarLanderEnv, self).__init__()

        # Initialize Pygame
        pygame.init()
        self.screen = None
        self.clock = pygame.time.Clock()

        # Action space: Discrete [Do Nothing, Fire Main Engine, Fire Left Engine, Fire Right Engine]
        self.action_space = spaces.Discrete(4)

        # Observation space: position_x, position_y, velocity_x, velocity_y, angle, angular_velocity, fuel
        high = np.array([SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SPEED, MAX_SPEED, np.pi, np.pi, 1.0], dtype=np.float32)
        low = np.array([0, 0, -MAX_SPEED, -MAX_SPEED, -np.pi, -np.pi, 0.0], dtype=np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        # Initialize game state
        self.reset()

    def reset(self):
        # Lander state
        self.position = np.array([SCREEN_WIDTH / 2, 0], dtype=np.float32)
        self.velocity = np.array([np.random.uniform(-MAX_SPEED, MAX_SPEED), np.random.uniform(-MAX_SPEED, 0)], dtype=np.float32)
        self.angle = 0.0
        self.angular_velocity = np.random.uniform(-np.pi/4, np.pi/4)
        self.fuel = 1.0  # Fuel level between 0 and 1

        # Generate uneven terrain
        self._generate_terrain()

        # Landing pad position at a random x-coordinate on the terrain
        self.landing_pad_x = random.uniform(SCREEN_WIDTH * 0.1, SCREEN_WIDTH * 0.9)
        self.landing_pad_width = 50

        # Flags
        self.done = False
        self.total_reward = 0.0

        return self._get_observation()

    def _generate_terrain(self):
        # Generate random terrain points
        num_points = 12
        x_points = np.linspace(0, SCREEN_WIDTH, num_points)
        y_points = SCREEN_HEIGHT - GROUND_HEIGHT + np.random.uniform(-20, 20, size=num_points)
        self.terrain = list(zip(x_points, y_points))

        # Create a list of terrain line segments
        self.terrain_segments = []
        for i in range(len(self.terrain) - 1):
            start = self.terrain[i]
            end = self.terrain[i + 1]
            self.terrain_segments.append((start, end))

    def step(self, action):
        reward = 0.0

        # Apply gravity
        self.velocity[1] += GRAVITY

        # Consume fuel and apply thrust
        if self.fuel > 0:
            if action == 1:  # Fire Main Engine
                self.velocity[1] -= THRUST
                self.fuel -= FUEL_CONSUMPTION
                reward -= FUEL_CONSUMPTION  # Penalty for fuel usage
            elif action == 2:  # Fire Left Engine
                self.velocity[0] += SIDE_THRUST
                self.fuel -= FUEL_CONSUMPTION
                reward -= FUEL_CONSUMPTION
            elif action == 3:  # Fire Right Engine
                self.velocity[0] -= SIDE_THRUST
                self.fuel -= FUEL_CONSUMPTION
                reward -= FUEL_CONSUMPTION

        # Update position
        self.position += self.velocity

        # Boundary conditions
        if self.position[0] < 0:
            self.position[0] = 0
            self.velocity[0] = 0
        elif self.position[0] > SCREEN_WIDTH:
            self.position[0] = SCREEN_WIDTH
            self.velocity[0] = 0
        if self.position[1] < 0:
            self.position[1] = 0
            self.velocity[1] = 0

        # Check for landing or crash
        terrain_height = self._get_terrain_height(self.position[0])
        if self.position[1] + LANDER_HEIGHT / 2 >= terrain_height:
            self.position[1] = terrain_height - LANDER_HEIGHT / 2
            self.velocity[1] = 0

            # Check if landed on the landing pad
            if (abs(self.velocity[0]) < 0.5 and abs(self.velocity[1]) < 0.5 and
                self.landing_pad_x - self.landing_pad_width / 2 <= self.position[0] <= self.landing_pad_x + self.landing_pad_width / 2):
                reward += 100.0  # Successful landing
            else:
                reward -= 100.0  # Crash
            self.done = True

        # Time penalty to encourage faster completion
        reward -= 0.1

        self.total_reward += reward
        obs = self._get_observation()
        info = {}

        return obs, reward, self.done, info

    def _get_terrain_height(self, x):
        # Interpolate terrain height at x
        for segment in self.terrain_segments:
            (x1, y1), (x2, y2) = segment
            if x1 <= x <= x2 or x2 <= x <= x1:
                # Linear interpolation
                if x2 != x1:
                    t = (x - x1) / (x2 - x1)
                    y = y1 + t * (y2 - y1)
                else:
                    y = y1
                return y
        # If x is outside terrain segments, return default ground height
        return SCREEN_HEIGHT - GROUND_HEIGHT

    def _get_observation(self):
        return np.array([
            self.position[0],
            self.position[1],
            self.velocity[0],
            self.velocity[1],
            self.angle,
            self.angular_velocity,
            self.fuel
        ], dtype=np.float32)

    def render(self, mode='human'):
        if self.screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Lunar Lander")
        self.screen.fill((0, 0, 0))  # Black background

        # Draw terrain
        pygame.draw.polygon(self.screen, (100, 100, 100), self.terrain + [(SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)])

        # Draw landing pad
        pad_y = self._get_terrain_height(self.landing_pad_x)
        pad_rect = pygame.Rect(
            self.landing_pad_x - self.landing_pad_width / 2,
            pad_y - 5,
            self.landing_pad_width,
            10
        )
        pygame.draw.rect(self.screen, (0, 255, 0), pad_rect)

        # Draw lander
        lander_rect = pygame.Rect(0, 0, LANDER_WIDTH, LANDER_HEIGHT)
        lander_rect.center = (int(self.position[0]), int(self.position[1]))
        pygame.draw.rect(self.screen, (255, 255, 255), lander_rect)

        # Fuel gauge
        fuel_height = int(self.fuel * 50)
        pygame.draw.rect(self.screen, (255, 0, 0), (10, 10 + 50 - fuel_height, 10, fuel_height))

        # Update display
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None
