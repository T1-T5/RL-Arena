import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Paddle settings
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_SPEED = 5

# Ball settings
BALL_SIZE = 10
BALL_SPEED_X = 4
BALL_SPEED_Y = 4

# Font
FONT = pygame.font.SysFont('Arial', 30)

# ---------------------------
# Paddle Class
# ---------------------------
class Paddle:
    def __init__(self, x, y, is_ai=False, agent=None):
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.speed = PADDLE_SPEED
        self.is_ai = is_ai
        self.agent = agent  # Agent should have an 'act' method if present

    def move_up(self):
        self.y -= self.speed
        if self.y < 0:
            self.y = 0

    def move_down(self):
        self.y += self.speed
        if self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height

    def update(self, ball=None):
        if self.is_ai and self.agent:
            action = self.agent.act(self, ball)
            if action == 'up':
                self.move_up()
            elif action == 'down':
                self.move_down()
            # You can add more actions if needed

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            WHITE,
            (self.x, self.y, self.width, self.height)
        )

# ---------------------------
# Ball Class
# ---------------------------
class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
        self.y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
        self.size = BALL_SIZE
        self.speed_x = BALL_SPEED_X * random.choice((-1, 1))
        self.speed_y = BALL_SPEED_Y * random.choice((-1, 1))

    def update(self, paddle_left, paddle_right):
        self.x += self.speed_x
        self.y += self.speed_y

        # Collision with top and bottom
        if self.y <= 0 or self.y + self.size >= SCREEN_HEIGHT:
            self.speed_y *= -1

        # Collision with left paddle
        if self.speed_x < 0:
            if (paddle_left.x < self.x < paddle_left.x + paddle_left.width) and \
               (paddle_left.y < self.y + self.size // 2 < paddle_left.y + paddle_left.height):
                self.speed_x *= -1

        # Collision with right paddle
        if self.speed_x > 0:
            if (paddle_right.x < self.x + self.size < paddle_right.x + paddle_right.width) and \
               (paddle_right.y < self.y + self.size // 2 < paddle_right.y + paddle_right.height):
                self.speed_x *= -1

        # Check for scoring
        if self.x < 0:
            return 'right'
        elif self.x > SCREEN_WIDTH:
            return 'left'
        return None

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            WHITE,
            (self.x, self.y, self.size, self.size)
        )

# ---------------------------
# Agent Interface
# ---------------------------
class AgentInterface:
    def act(self, paddle, ball):
        """
        Implement your agent's decision-making here.
        The function should return one of the following actions:
        - 'up'
        - 'down'
        - 'none'
        """
        # Placeholder for agent action
        return 'none'

# ---------------------------
# Game Class
# ---------------------------
class PongGame:
    def __init__(self, mode='human_vs_computer', agent_left=None, agent_right=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Pong')

        self.clock = pygame.time.Clock()
        self.mode = mode

        # Initialize paddles
        self.paddle_left = Paddle(20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
                                  is_ai=(mode in ['agent_vs_agent', 'agent_vs_computer']),
                                  agent=agent_left)
        self.paddle_right = Paddle(SCREEN_WIDTH - 20 - PADDLE_WIDTH,
                                   SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
                                   is_ai=(mode in ['human_vs_computer', 'agent_vs_agent']),
                                   agent=agent_right)

        # Initialize ball
        self.ball = Ball()

        # Scores
        self.score_left = 0
        self.score_right = 0

        # Game Over flag
        self.game_over = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        # Left paddle (Player 1)
        if self.mode in ['human_vs_computer', 'human_vs_human', 'human_vs_agent', 'human_vs_computer']:
            if keys[pygame.K_w]:
                self.paddle_left.move_up()
            if keys[pygame.K_s]:
                self.paddle_left.move_down()

        # Right paddle (Player 2 or Computer)
        if self.mode in ['human_vs_human', 'agent_vs_agent', 'human_vs_agent', 'agent_vs_computer']:
            if self.mode in ['human_vs_human', 'human_vs_agent']:
                if keys[pygame.K_UP]:
                    self.paddle_right.move_up()
                if keys[pygame.K_DOWN]:
                    self.paddle_right.move_down()

    def update(self):
        # Update paddles
        self.paddle_left.update(ball=self.ball)
        self.paddle_right.update(ball=self.ball)

        # Update ball
        scorer = self.ball.update(self.paddle_left, self.paddle_right)
        if scorer == 'left':
            self.score_left += 1
            self.ball.reset()
        elif scorer == 'right':
            self.score_right += 1
            self.ball.reset()

    def draw(self):
        self.screen.fill(BLACK)

        # Draw middle line
        pygame.draw.aaline(self.screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))

        # Draw paddles and ball
        self.paddle_left.draw(self.screen)
        self.paddle_right.draw(self.screen)
        self.ball.draw(self.screen)

        # Draw scores
        score_text = FONT.render(f"{self.score_left} : {self.score_right}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 20))

        pygame.display.flip()

    def run(self):
        while not self.game_over:
            self.handle_events()

            if not self.paddle_left.is_ai or not self.paddle_right.is_ai:
                self.handle_input()

            self.update()
            self.draw()

            # Check for game over condition (optional)
            # For simplicity, we'll allow continuous play
            self.clock.tick(FPS)

# ---------------------------
# Example Agents
# ---------------------------
class SimpleHeuristicAgent(AgentInterface):
    def act(self, paddle, ball):
        """
        Simple heuristic: Move paddle towards the ball's y position.
        """
        if ball.y + ball.size / 2 < paddle.y + paddle.height / 2:
            return 'up'
        elif ball.y + ball.size / 2 > paddle.y + paddle.height / 2:
            return 'down'
        else:
            return 'none'

class RandomAgent(AgentInterface):
    def act(self, paddle, ball):
        """
        Randomly decide to move up, down, or stay.
        """
        return random.choice(['up', 'down', 'none'])

# ---------------------------
# Main Function
# ---------------------------
def main():
    # Select game mode
    print("Select Game Mode:")
    print("1. Human vs Computer")
    print("2. Human vs Human")
    print("3. Human vs Agent")
    print("4. Agent vs Agent")
    print("5. Agent vs Computer")
    mode_input = input("Enter the number of the desired mode: ")

    mode_dict = {
        '1': 'human_vs_computer',
        '2': 'human_vs_human',
        '3': 'human_vs_agent',
        '4': 'agent_vs_agent',
        '5': 'agent_vs_computer'
    }

    mode = mode_dict.get(mode_input, 'human_vs_computer')

    # Initialize agents based on mode
    agent_left = None
    agent_right = None

    if mode == 'human_vs_computer':
        agent_right = SimpleHeuristicAgent()
    elif mode == 'human_vs_agent':
        agent_right = SimpleHeuristicAgent()
    elif mode == 'agent_vs_agent':
        agent_left = SimpleHeuristicAgent()
        agent_right = SimpleHeuristicAgent()
    elif mode == 'agent_vs_computer':
        agent_left = SimpleHeuristicAgent()
        agent_right = SimpleHeuristicAgent()  # You can use a different agent if desired

    # Initialize and run the game
    game = PongGame(mode=mode, agent_left=agent_left, agent_right=agent_right)
    game.run()

if __name__ == '__main__':
    main()
