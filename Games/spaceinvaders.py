import pygame
import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize PyGame
pygame.init()

# Define colors and font
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (0, 255, 0)  # Green player
ENEMY_COLOR = (255, 0, 0)   # Red enemies
BULLET_COLOR = (255, 255, 0) # Yellow bullets
FONT = pygame.font.SysFont(None, 25)

# Game constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
PLAYER_SPEED = 25
ENEMY_SPEED = 1
BULLET_SPEED = -10
ENEMY_BULLET_SPEED = 5
FIRE_DELAY = 500  # milliseconds

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.speed = PLAYER_SPEED
        self.last_fire_time = pygame.time.get_ticks()
        self.cooldown = FIRE_DELAY

    def move(self, direction):
        if direction == 0:  # Move left
            self.x -= self.speed
        elif direction == 1:  # Move right
            self.x += self.speed
        # Boundary conditions
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))

    def can_fire(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_fire_time >= self.cooldown

    def fire(self):
        self.last_fire_time = pygame.time.get_ticks()
        return Bullet(self.x + self.width // 2, self.y, BULLET_SPEED, 'player')

    def draw(self, game_display):
        pygame.draw.rect(game_display, PLAYER_COLOR, (self.x, self.y, self.width, self.height))

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = ENEMY_WIDTH
        self.height = ENEMY_HEIGHT
        self.speed = ENEMY_SPEED
        self.direction = 1  # 1 for right, -1 for left
        self.descend = False
        self.alive = True

    def move(self):
        self.x += self.speed * self.direction
        if self.x <= 0 or self.x + self.width >= SCREEN_WIDTH:
            self.direction *= -1
            self.y += self.height  # Move down when changing direction

    def fire(self):
        return Bullet(self.x + self.width // 2, self.y + self.height, ENEMY_BULLET_SPEED, 'enemy')

    def draw(self, game_display):
        pygame.draw.rect(game_display, ENEMY_COLOR, (self.x, self.y, self.width, self.height))

class Bullet:
    def __init__(self, x, y, speed, owner):
        self.x = x
        self.y = y
        self.speed = speed
        self.owner = owner  # 'player' or 'enemy'
        self.width = 5
        self.height = 10

    def move(self):
        self.y += self.speed

    def draw(self, game_display):
        pygame.draw.rect(game_display, BULLET_COLOR, (self.x, self.y, self.width, self.height))

class SpaceInvadersEnv(gym.Env):
    def __init__(self):
        super(SpaceInvadersEnv, self).__init__()
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.player = Player()
        self.enemies = self._create_enemies()
        self.player_bullets = []
        self.enemy_bullets = []
        self.score = 0
        self.done = False
        self.game_display = None
        self.clock = pygame.time.Clock()
        self.last_enemy_fire_time = pygame.time.get_ticks()

        # Define action and observation space
        # Actions: 0 - Move Left, 1 - Move Right, 2 - Fire, 3 - Do Nothing
        self.action_space = spaces.Discrete(4)

        # Observation space: Positions of player, enemies, bullets
        self.observation_space = spaces.Box(
            low=0,
            high=max(self.screen_width, self.screen_height),
            shape=(5 + len(self.enemies) * 2 + 2 * 50,),  # Adjust size as needed
            dtype=np.float32
        )

    def reset(self):
        self.player = Player()
        self.enemies = self._create_enemies()
        self.player_bullets = []
        self.enemy_bullets = []
        self.score = 0
        self.done = False
        state = self._get_state()
        return state

    def step(self, action):
        reward = 0

        # Handle action
        if action == 0:  # Move Left
            self.player.move(0)
        elif action == 1:  # Move Right
            self.player.move(1)
        elif action == 2:  # Fire
            if self.player.can_fire():
                bullet = self.player.fire()
                self.player_bullets.append(bullet)
        # else: Do Nothing

        # Move bullets
        for bullet in self.player_bullets:
            bullet.move()
        for bullet in self.enemy_bullets:
            bullet.move()

        # Remove off-screen bullets
        self.player_bullets = [b for b in self.player_bullets if b.y > 0]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.y < SCREEN_HEIGHT]

        # Move enemies
        for enemy in self.enemies:
            enemy.move()

        # Enemies fire bullets
        self._enemy_fire()

        # Check for collisions
        reward += self._check_collisions()

        # Check for game over conditions
        if not any(enemy.alive for enemy in self.enemies):
            self.done = True  # Player wins
            reward += 100  # Reward for winning

        if self._check_player_hit():
            self.done = True  # Player loses
            reward -= 100  # Penalty for losing

        # Get state
        state = self._get_state()
        info = {'score': self.score}

        return state, reward, self.done, info

    def render(self, mode='human'):
        if self.game_display is None:
            self.game_display = pygame.display.set_mode((self.screen_width, self.screen_height))
            pygame.display.set_caption('Space Invaders')

        self.game_display.fill(BLACK)
        self.player.draw(self.game_display)
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(self.game_display)
        for bullet in self.player_bullets:
            bullet.draw(self.game_display)
        for bullet in self.enemy_bullets:
            bullet.draw(self.game_display)
        score_text = FONT.render("Score: " + str(self.score), True, WHITE)
        self.game_display.blit(score_text, (10, 10))
        pygame.display.update()
        self.clock.tick(30)

    def close(self):
        if self.game_display is not None:
            pygame.quit()

    def _get_state(self):
        # State includes positions of player, enemies, and bullets
        state = []

        # Player position
        state.extend([self.player.x, self.player.y])

        # Enemies positions
        for enemy in self.enemies:
            if enemy.alive:
                state.extend([enemy.x, enemy.y])
            else:
                state.extend([-1, -1])  # Placeholder for dead enemies

        # Player bullets positions
        for bullet in self.player_bullets:
            state.extend([bullet.x, bullet.y])
        # Pad the bullet list to a fixed size
        for _ in range(50 - len(self.player_bullets)):
            state.extend([-1, -1])

        # Enemy bullets positions
        for bullet in self.enemy_bullets:
            state.extend([bullet.x, bullet.y])
        # Pad the bullet list to a fixed size
        for _ in range(50 - len(self.enemy_bullets)):
            state.extend([-1, -1])

        return np.array(state, dtype=np.float32)

    def _check_collisions(self):
        reward = 0
        # Check for bullet-enemy collisions
        for bullet in self.player_bullets[:]:
            for enemy in self.enemies:
                if enemy.alive and self._rect_collision(bullet, enemy):
                    self.player_bullets.remove(bullet)
                    enemy.alive = False
                    self.score += 1
                    reward += 10  # Reward for hitting an enemy
                    break

        # Check for bullet-player collisions handled in _check_player_hit
        return reward

    def _check_player_hit(self):
        for bullet in self.enemy_bullets:
            if self._rect_collision(bullet, self.player):
                return True
        return False

    def _rect_collision(self, obj1, obj2):
        rect1 = pygame.Rect(obj1.x, obj1.y, obj1.width, obj1.height)
        rect2 = pygame.Rect(obj2.x, obj2.y, obj2.width, obj2.height)
        return rect1.colliderect(rect2)

    def _create_enemies(self):
        enemies = []
        rows = 5
        cols = 10
        x_margin = 50
        y_margin = 50
        x_spacing = (SCREEN_WIDTH - 2 * x_margin - cols * ENEMY_WIDTH) // (cols - 1)
        y_spacing = 40
        for row in range(rows):
            for col in range(cols):
                x = x_margin + col * (ENEMY_WIDTH + x_spacing)
                y = y_margin + row * (ENEMY_HEIGHT + y_spacing)
                enemies.append(Enemy(x, y))
        return enemies

    def _enemy_fire(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_enemy_fire_time > FIRE_DELAY:
            alive_enemies = [enemy for enemy in self.enemies if enemy.alive]
            if alive_enemies:
                enemy = random.choice(alive_enemies)
                bullet = enemy.fire()
                self.enemy_bullets.append(bullet)
            self.last_enemy_fire_time = current_time