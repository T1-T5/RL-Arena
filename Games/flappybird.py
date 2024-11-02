import pygame
import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize PyGame
pygame.init()

# Game constants
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
GRAVITY = 0.5
BIRD_FLAP_VELOCITY = -7
PIPE_SPEED = -3
PIPE_GAP = 100
PIPE_FREQUENCY = 3000  # milliseconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BIRD_COLOR = (255, 255, 0)  # Yellow
PIPE_COLOR = (0, 255, 0)    # Green
FONT = pygame.font.SysFont(None, 25)

class Bird:
    def __init__(self):
        self.x = SCREEN_WIDTH // 6
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.width = 34
        self.height = 24

    def flap(self):
        self.velocity = BIRD_FLAP_VELOCITY

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity

    def draw(self, game_display):
        pygame.draw.rect(game_display, BIRD_COLOR, (self.x, self.y, self.width, self.height))

class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.top_height = random.randint(50, SCREEN_HEIGHT - PIPE_GAP - 50)
        self.bottom_height = SCREEN_HEIGHT - self.top_height - PIPE_GAP
        self.width = 52
        self.passed = False

    def move(self):
        self.x += PIPE_SPEED

    def draw(self, game_display):
        pygame.draw.rect(game_display, PIPE_COLOR, (self.x, 0, self.width, self.top_height))
        pygame.draw.rect(game_display, PIPE_COLOR, 
                        (self.x, SCREEN_HEIGHT - self.bottom_height, self.width, self.bottom_height))

class FlappyBirdEnv(gym.Env):
    def __init__(self):
        super().__init__()
        # Environment setup
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.pipe_gap = PIPE_GAP
        
        # Game objects
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.last_pipe_time = pygame.time.get_ticks()
        
        # Rendering
        self.game_display = None
        self.clock = pygame.time.Clock()
        
        # Gym spaces
        self.action_space = spaces.Discrete(2)  # 0: Do nothing, 1: Flap
        self.observation_space = spaces.Box(
            low=np.array([0, -np.inf, 0, 0], dtype=np.float32),
            high=np.array([SCREEN_HEIGHT, np.inf, SCREEN_WIDTH, SCREEN_HEIGHT], dtype=np.float32),
            dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        # Reset bird
        self.bird = Bird()
        
        # Reset game state
        self.pipes = [Pipe()]
        self.score = 0
        self.last_pipe_time = pygame.time.get_ticks()
        
        return self._get_observation(), {}

    def step(self, action):
        # Handle action
        if action == 1:
            self.bird.flap()

        # Update bird
        self.bird.move()

        # Update pipes
        current_time = pygame.time.get_ticks()
        if current_time - self.last_pipe_time > PIPE_FREQUENCY:
            self.pipes.append(Pipe())
            self.last_pipe_time = current_time

        for pipe in self.pipes:
            pipe.move()

        # Remove off-screen pipes
        self.pipes = [pipe for pipe in self.pipes if pipe.x + pipe.width > 0]

        # Calculate reward
        reward = 0.1  # Small reward for staying alive
        for pipe in self.pipes:
            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                pipe.passed = True
                self.score += 1
                reward += 1.0  # Bonus for passing pipe

        # Check if game is done
        done = self._check_collision()
        if done:
            reward = -1.0  # Penalty for dying

        return self._get_observation(), reward, done, False, {'score': self.score}

    def render(self, mode='human'):
        if self.game_display is None:
            self.game_display = pygame.display.set_mode((self.screen_width, self.screen_height))
            pygame.display.set_caption('Flappy Bird')

        self.game_display.fill(BLACK)
        
        # Draw game objects
        self.bird.draw(self.game_display)
        for pipe in self.pipes:
            pipe.draw(self.game_display)
            
        # Draw score
        score_text = FONT.render(f"Score: {self.score}", True, WHITE)
        self.game_display.blit(score_text, (10, 10))
        
        pygame.display.update()
        self.clock.tick(30)

    def close(self):
        if self.game_display is not None:
            pygame.quit()

    def _get_observation(self):
        # Find the next pipe
        next_pipe = None
        for pipe in self.pipes:
            if pipe.x + pipe.width >= self.bird.x:
                next_pipe = pipe
                break
                
        # If no pipe is found, use default values
        if next_pipe is None:
            next_pipe_dist = self.screen_width
            next_pipe_top = self.screen_height / 2
        else:
            next_pipe_dist = next_pipe.x - self.bird.x
            next_pipe_top = next_pipe.top_height

        return np.array([
            self.bird.y,                # Bird's height
            self.bird.velocity,         # Bird's velocity
            next_pipe_dist,            # Distance to next pipe
            next_pipe_top,             # Height of next pipe's gap
        ], dtype=np.float32)

    def _check_collision(self):
        # Check if bird hits the ground or ceiling
        if self.bird.y <= 0 or self.bird.y + self.bird.height >= self.screen_height:
            return True

        # Check collision with pipes
        bird_rect = pygame.Rect(self.bird.x, self.bird.y, self.bird.width, self.bird.height)
        for pipe in self.pipes:
            top_pipe_rect = pygame.Rect(pipe.x, 0, pipe.width, pipe.top_height)
            bottom_pipe_rect = pygame.Rect(
                pipe.x, 
                self.screen_height - pipe.bottom_height, 
                pipe.width, 
                pipe.bottom_height
            )
            if bird_rect.colliderect(top_pipe_rect) or bird_rect.colliderect(bottom_pipe_rect):
                return True

        return False