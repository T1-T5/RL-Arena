import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30

# Grid dimensions
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

# Frames per second
FPS = 60

# Colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),    # I
    (0, 0, 255),      # J
    (255, 165, 0),    # L
    (255, 255, 0),    # O
    (0, 255, 0),      # S
    (128, 0, 128),    # T
    (255, 0, 0),      # Z
]

# ---------------------------
# Tetromino Shapes
# ---------------------------
SHAPES = [
    [['.....',
      '.....',
      '..O..',
      '..O..',
      '..O..',
      '..O..',
      '.....'],
     ['.....',
      '.....',
      '.....',
      'OOOO',
      '.....']],
    [['.....',
      '.....',
      '.O...',
      '.OOO.',
      '.....'],
     ['.....',
      '..OO.',
      '..O..',
      '..O..',
      '.....'],
     ['.....',
      '.....',
      '.OOO.',
      '...O.',
      '.....'],
     ['.....',
      '..O..',
      '..O..',
      '.OO..',
      '.....']],
    [['.....',
      '.....',
      '...O.',
      '.OOO.',
      '.....'],
     ['.....',
      '..O..',
      '..O..',
      '..OO.',
      '.....'],
     ['.....',
      '.....',
      '.OOO.',
      '.O...',
      '.....'],
     ['.....',
      '.OO..',
      '..O..',
      '..O..',
      '.....']],
    [['.....',
      '.....',
      '.OO..',
      '.OO..',
      '.....']],
    [['.....',
      '.....',
      '..OO.',
      '.OO..',
      '.....'],
     ['.....',
      '..O..',
      '..OO.',
      '...O.',
      '.....']],
    [['.....',
      '.....',
      '..O..',
      '.OOO.',
      '.....'],
     ['.....',
      '..O..',
      '..OO.',
      '..O..',
      '.....'],
     ['.....',
      '.....',
      '.OOO.',
      '..O..',
      '.....'],
     ['.....',
      '..O..',
      '.OO..',
      '..O..',
      '.....']],
    [['.....',
      '.....',
      '.OO..',
      '..OO.',
      '.....'],
     ['.....',
      '..O..',
      '.OO..',
      '.O...',
      '.....']],
]

# ---------------------------
# Tetromino Class
# ---------------------------
class Tetromino:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = COLORS[SHAPES.index(shape)]
        self.rotation = 0

    def image(self):
        return self.shape[self.rotation % len(self.shape)]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.shape)

    def get_blocks(self):
        blocks = []
        pattern = self.image()
        for i, row in enumerate(pattern):
            for j, cell in enumerate(row):
                if cell == 'O':
                    blocks.append((self.x + j - 2, self.y + i - 4))
        return blocks

# ---------------------------
# Game Class
# ---------------------------
class Tetris:
    def __init__(self):
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.get_new_piece()
        self.next_piece = self.get_new_piece()
        self.score = 0
        self.game_over = False
        self.lock_delay = 0

    def get_new_piece(self):
        shape = random.choice(SHAPES)
        return Tetromino(GRID_WIDTH // 2, 0, shape)

    def valid_position(self, piece, adj_x=0, adj_y=0):
        for block in piece.get_blocks():
            x, y = block[0] + adj_x, block[1] + adj_y
            if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                return False
            if y >= 0 and self.grid[y][x] != BLACK:
                return False
        return True

    def lock_piece(self):
        for block in self.current_piece.get_blocks():
            x, y = block
            if y >= 0:
                self.grid[y][x] = self.current_piece.color
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.get_new_piece()
        if not self.valid_position(self.current_piece):
            self.game_over = True

    def clear_lines(self):
        lines_cleared = 0
        new_grid = [row for row in self.grid if any(cell == BLACK for cell in row)]
        lines_cleared = GRID_HEIGHT - len(new_grid)
        for _ in range(lines_cleared):
            new_grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])
        self.grid = new_grid
        self.score += lines_cleared * 100

    def move(self, dx, dy):
        if self.valid_position(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate(self):
        original_rotation = self.current_piece.rotation
        self.current_piece.rotate()
        if not self.valid_position(self.current_piece):
            self.current_piece.rotation = original_rotation

    def hard_drop(self):
        while self.move(0, 1):
            pass
        self.lock_piece()

    def update(self):
        if not self.move(0, 1):
            self.lock_piece()

# ---------------------------
# Renderer Class
# ---------------------------
class Renderer:
    def __init__(self, screen, game):
        self.screen = screen
        self.game = game
        self.font = pygame.font.SysFont('Arial', 24)

    def draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    self.game.grid[y][x],
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    1
                )

    def draw_piece(self, piece):
        for block in piece.get_blocks():
            x, y = block
            if y >= 0:
                pygame.draw.rect(
                    self.screen,
                    piece.color,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    1
                )

    def draw_next_piece(self):
        label = self.font.render('Next:', True, WHITE)
        self.screen.blit(label, (SCREEN_WIDTH + 20, 20))
        for block in self.game.next_piece.get_blocks():
            x, y = block
            # Offset next piece display
            x = x - self.game.next_piece.x + GRID_WIDTH + 1
            y = y - self.game.next_piece.y + 2
            if y >= 0:
                pygame.draw.rect(
                    self.screen,
                    self.game.next_piece.color,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                    1
                )

    def draw_score(self):
        label = self.font.render(f'Score: {self.game.score}', True, WHITE)
        self.screen.blit(label, (SCREEN_WIDTH + 20, 200))

    def render(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        self.draw_piece(self.game.current_piece)
        self.draw_next_piece()
        self.draw_score()
        pygame.display.flip()

# ---------------------------
# Agent Interface
# ---------------------------
class AgentInterface:
    def __init__(self, game):
        self.game = game

    def act(self):
        """
        Implement your agent's decision-making here.
        The function should return one of the following actions:
        - 'left'
        - 'right'
        - 'down'
        - 'rotate'
        - 'drop'
        """
        # Placeholder for agent action
        return 'down'

# ---------------------------
# Main Game Loop
# ---------------------------
def main(agent=None):
    screen_width = SCREEN_WIDTH + 200  # Extra space for next piece and score
    screen_height = SCREEN_HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Tetris')

    clock = pygame.time.Clock()
    game = Tetris()
    renderer = Renderer(screen, game)
    agent_interface = AgentInterface(game) if agent else None

    fall_time = 0
    fall_speed = 0.5  # seconds

    while not game.game_over:
        dt = clock.tick(FPS) / 1000  # Delta time in seconds
        fall_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if not agent:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.move(0, 1)
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()

        # Agent takes action
        if agent:
            action = agent.act()
            if action == 'left':
                game.move(-1, 0)
            elif action == 'right':
                game.move(1, 0)
            elif action == 'down':
                game.move(0, 1)
            elif action == 'rotate':
                game.rotate()
            elif action == 'drop':
                game.hard_drop()

        # Handle automatic falling
        if fall_time >= fall_speed:
            fall_time = 0
            game.update()

        renderer.render()

    # Game Over
    pygame.quit()
    print(f'Game Over! Your score: {game.score}')

# ---------------------------
# Example Agent
# ---------------------------
class SimpleAgent:
    def __init__(self, game):
        self.game = game

    def act(self):
        # Simple agent that moves the piece to the left
        return 'left'

# ---------------------------
# Run the Game
# ---------------------------
if __name__ == '__main__':
    # To play manually, call main() without arguments
    # main()

    # To use an agent, pass an instance with an 'act' method
    # Example with SimpleAgent:
    # game_instance = Tetris()
    # agent = SimpleAgent(game_instance)
    # main(agent=agent)

    # For demonstration, we'll run the game for human play
    main()
