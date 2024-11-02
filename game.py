import pygame
import random
import gym
from gym import spaces
import numpy as np
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize PyGame
pygame.init()

# Define colors and font
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
FONT = pygame.font.SysFont(None, 25)

# Define hyperparameters
VISION = 5
SCREEN_RATIO = 2
MAX_STEPS = 150

# Define the score class
class Score:
    def __init__(self):
        self.value = 0
    
    def draw(self, game_display):
        score_text = FONT.render("Score: " + str(self.value), True, WHITE)
        game_display.blit(score_text, (10, 10))
    
# Define the food class       
class Food:
    def __init__(self, num_cols, num_rows, scale):
        self.position = (random.randint(0, num_cols-1), random.randint(0, num_rows-1))
        self.scale = scale

    def draw(self, game_display):
        # Draw the food on the game board
        x = self.position[0] * self.scale
        y = self.position[1] * self.scale
        pygame.draw.rect(game_display, RED, (x, y, self.scale, self.scale))

# Define the Snake sub-class
class Snake:
    def __init__(self, col, row, scale):
        self.position = [(col, row)]  # Start at the center of the screen
        self.direction = 'up'
        self.previous_direction = 'up'
        self.scale = scale
        self.growth_position = (col, row - 1)

    def move(self):
        # Move the snake based on its current direction
        head = self.position[0]
        col, row = head[0], head[1]
        if self.direction == 'up':
            row -= 1
        elif self.direction == 'down':
            row += 1
        elif self.direction == 'left':
            col -= 1
        elif self.direction == 'right':
            col += 1
        self.position.insert(0, (col, row))
        self.growth_position = self.position.pop()

    def grow(self):
        # Add a new body segment to the snake
        tail = self.growth_position
        self.position.append(tail)
    
    def draw(self, game_display):
        # Draw the snake on the game board
        for pos in self.position:
            pygame.draw.rect(game_display, WHITE, (pos[0]*self.scale, pos[1]*self.scale, self.scale, self.scale))

    def set_direction(self, new_direction):
        # Set the new direction of the snake, but only if it is perpendicular to the previous direction
        if new_direction == 'up' or new_direction == 'down':
            if self.previous_direction == 'left' or self.previous_direction == 'right':
                self.direction = new_direction
        elif new_direction == 'left' or new_direction == 'right':
            if self.previous_direction == 'up' or self.previous_direction == 'down':
                self.direction = new_direction

    def update_previous_direction(self):
        # Update the previous direction of the snake
        self.previous_direction = self.direction

class Game(gym.Env):
    def __init__(self, width=640//SCREEN_RATIO, height=480//SCREEN_RATIO, scale=10):
        # Set up the game window
        self.screen_width = width
        self.screen_height = height
        self.scale = scale
        # Calculate number of rows and columns
        self.num_rows = self.screen_height // self.scale
        self.num_cols = self.screen_width // self.scale

        # Create the snake, food and score objects
        self.snake = Snake(self.num_cols//2, self.num_rows//2, self.scale)
        self.food = Food(self.num_cols, self.num_rows, self.scale)
        # check if new food is not on the snake, redraw random position until then
        while self.food.position in self.snake.position:
            self.food = Food(self.num_cols, self.num_rows, self.scale)
        self.score = Score()

        # initialize reward and done
        self.reward = 0
        self.done = False

        # get initial state
        self.state = self._get_state()

        # observation space: encodes direction of the snake, relative position of the food, relative position of danger
        self.observation_space = spaces.Box(low=0, high=1, shape=((2*VISION+1)**2-1+8,), dtype=int)
        # action space: discrete action space with 4 actions for the 4 directions
        self.action_space = spaces.Discrete(4)
        self.actions_to_directions = {0:'up', 1:'right', 2:'down', 3:'left'}

        # get the information of timesteps spent chasing food and total timesteps
        self.timesteps = 0
        self.total_timesteps = 0


    def reset(self):
        # Reset the snake, food and score
        self.snake = Snake(self.num_cols//2, self.num_rows//2, self.scale)
        self.food = Food(self.num_cols, self.num_rows, self.scale)
        # check if new food is not on the snake, redraw random position until then
        while self.food.position in self.snake.position:
            self.food = Food(self.num_cols, self.num_rows, self.scale)
        self.score = Score()
        # Reset the timesteps
        self.timesteps = 0
        self.total_timesteps = 0
        # Reset reward and done
        self.reward = 0
        self.done = False
        # get initial state
        self.state = self._get_state()
        return self.state

    def step(self, action=None):
        # Handle events
        if action==None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN or event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.snake.set_direction(pygame.key.name(event.key))

        # convert action to direction
        else:
            direction = self.actions_to_directions[action]
            self.snake.set_direction(direction)
        
        # Move the snake
        self.snake.move()
        self.snake.update_previous_direction()
        
        # Check for collisions with the food
        self.reward = 0
        if self.snake.position[0] == self.food.position:
            self.snake.grow()
            self.food = Food(self.num_cols, self.num_rows, self.scale)
            # check if new food is not on the snake, redraw random position until then
            while self.food.position in self.snake.position:
                self.food = Food(self.num_cols, self.num_rows, self.scale)
            self.score.value+=1
            self.reward+=10
            # reset timesteps of chasing food
            self.timesteps = 0
        
        # Check for collisions
        self.done = self._is_collision() or (self.timesteps > MAX_STEPS*len(self.snake.position))
        if self.done:
            self.reward-=10

        # get new state
        self.state = self._get_state()

        # update timesteps
        self.timesteps+=1
        self.total_timesteps+=1

        # get the information of timesteps
        info = {'timesteps':self.total_timesteps}

        return self.state, self.reward, self.done, info
    

    def init_render(self):
        # Set up the game display       
        self.game_display = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Snake')
        # Set up the clock
        self.clock = pygame.time.Clock()

    def render(self):
        # Fill the game board with black
        self.game_display.fill(BLACK)
        
        # Draw the snake, food and score
        self.snake.draw(self.game_display)
        self.food.draw(self.game_display)
        self.score.draw(self.game_display)
        
        # Update the display
        pygame.display.update()
        
        # Set the game clock
        self.clock.tick(60)
        return

    # helper function to check for collisions
    def _is_collision(self, point=None):
        if point is None:
            point = self.snake.position[0]
        # Check for collisions with the walls
        if point[0] < 0 or point[0] >= self.num_cols or point[1] < 0 or point[1] >= self.num_rows:
            return True
        # Check for collisions with the snake's body
        if point in self.snake.position[1:]:
            return True
        
        return False
    
    # helper function to get the current state
    def _get_state(self):
        head = self.snake.position[0]
        col, row = head
        # VISION**2-1 neighbouring points in a VISIONxVISION square (- head)
        points = []
        for i in range(-VISION,VISION+1):
            for j in range(-VISION,VISION+1):
                if (i,j)!=(0,0):
                    point = (col+i, row+j)
                    points.append(point)
        # direction
        is_direction_up = self.snake.direction == 'up'
        is_direction_right = self.snake.direction == 'right'
        is_direction_down = self.snake.direction == 'down'
        is_direction_left = self.snake.direction == 'left'

        # collisions
        state = [self._is_collision(point) for point in points]
    
        state.extend(
            [
            # Directions
            is_direction_up,
            is_direction_down,
            is_direction_left,
            is_direction_right,
            # relative food location
            self.food.position[1] < head[1], # food is above (up) the snake
            self.food.position[1] > head[1], # food is below (down) the snake
            self.food.position[0] < head[0], # food is left of the snake
            self.food.position[0] > head[0], # food is right of the snake
            ]
        )

        return np.array(state, dtype=int)