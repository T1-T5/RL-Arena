import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# ---------------------------
# Game Constants
# ---------------------------
ROWS, COLS = 6, 7
SQUARE_SIZE = 100
RADIUS = SQUARE_SIZE // 2 - 5
SCREEN_WIDTH = COLS * SQUARE_SIZE
SCREEN_HEIGHT = (ROWS + 1) * SQUARE_SIZE  # Extra row for player info
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Font
FONT = pygame.font.SysFont('Arial', 30)

# ---------------------------
# Game Board Class
# ---------------------------
class Board:
    def __init__(self):
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    
    def drop_piece(self, row, col, piece):
        self.grid[row][col] = piece

    def is_valid_location(self, col):
        return self.grid[0][col] == 0

    def get_next_open_row(self, col):
        for r in range(ROWS-1, -1, -1):
            if self.grid[r][col] == 0:
                return r
        return -1

    def check_for_win(self, piece):
        # Check horizontal locations
        for c in range(COLS - 3):
            for r in range(ROWS):
                if all(self.grid[r][c+i] == piece for i in range(4)):
                    return True

        # Check vertical locations
        for c in range(COLS):
            for r in range(ROWS - 3):
                if all(self.grid[r+i][c] == piece for i in range(4)):
                    return True

        # Check positively sloped diagonals
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if all(self.grid[r+i][c+i] == piece for i in range(4)):
                    return True

        # Check negatively sloped diagonals
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if all(self.grid[r-i][c+i] == piece for i in range(4)):
                    return True
        return False

    def is_full(self):
        return all(self.grid[0][col] != 0 for col in range(COLS))

# ---------------------------
# Agent Interface
# ---------------------------
class AgentInterface:
    def act(self, board, piece):
        """
        Implement your agent's decision-making here.
        This function should return a column (0 to COLS-1) where the piece will be dropped.
        """
        raise NotImplementedError("This method should be overridden by subclasses")

# ---------------------------
# Simple Computer Player
# ---------------------------
class SimpleComputerPlayer(AgentInterface):
    def act(self, board, piece):
        # Basic AI: Choose the first available column
        valid_columns = [c for c in range(COLS) if board.is_valid_location(c)]
        if valid_columns:
            return random.choice(valid_columns)
        else:
            return None

# ---------------------------
# More Advanced Heuristic Agent (Optional)
# ---------------------------
class HeuristicAgent(AgentInterface):
    def act(self, board, piece):
        # Attempt to win or block opponent from winning
        for col in range(COLS):
            if board.is_valid_location(col):
                row = board.get_next_open_row(col)
                # Try to win
                board.drop_piece(row, col, piece)
                if board.check_for_win(piece):
                    board.drop_piece(row, col, 0)
                    return col
                board.drop_piece(row, col, 0)
                # Try to block opponent
                opponent = 1 if piece == 2 else 2
                board.drop_piece(row, col, opponent)
                if board.check_for_win(opponent):
                    board.drop_piece(row, col, 0)
                    return col
                board.drop_piece(row, col, 0)
        # Otherwise, choose random
        valid_columns = [c for c in range(COLS) if board.is_valid_location(c)]
        if valid_columns:
            return random.choice(valid_columns)
        else:
            return None

# ---------------------------
# Game Class
# ---------------------------
class ConnectFourGame:
    def __init__(self, mode='human_vs_computer', agent1=None, agent2=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Connect Four')

        self.clock = pygame.time.Clock()
        self.board = Board()
        self.mode = mode
        self.turn = random.choice([1, 2])  # Player 1 starts as Red, Player 2 as Yellow
        self.game_over = False

        # Assign agents
        self.agent1 = agent1  # Agent for Player 1 (Red)
        self.agent2 = agent2  # Agent for Player 2 (Yellow)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Handle mouse movement and clicks only if the current player is human
            if not ((self.turn == 1 and self.agent1) or (self.turn == 2 and self.agent2)):
                if event.type == pygame.MOUSEMOTION:
                    pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, SQUARE_SIZE))
                    posx = event.pos[0]
                    color = RED if self.turn == 1 else YELLOW
                    pygame.draw.circle(self.screen, color, (posx, SQUARE_SIZE // 2), RADIUS)
                pygame.display.update()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game_over:
                        posx = event.pos[0]
                        col = posx // SQUARE_SIZE
                        if self.board.is_valid_location(col):
                            self.drop_piece(col)

    def drop_piece(self, col):
        row = self.board.get_next_open_row(col)
        if row != -1:
            self.board.drop_piece(row, col, self.turn)
            if self.board.check_for_win(self.turn):
                self.game_over = True
                self.display_winner()
            elif self.board.is_full():
                self.game_over = True
                self.display_draw()
            self.turn = 3 - self.turn  # Switch turn

    def update(self):
        # If it's an agent's turn, let the agent choose
        if not self.game_over:
            if self.turn == 1 and self.agent1:
                col = self.agent1.act(self.board, self.turn)
                if col is not None and self.board.is_valid_location(col):
                    pygame.time.wait(500)  # Optional: pause for better visualization
                    self.drop_piece(col)
            elif self.turn == 2 and self.agent2:
                col = self.agent2.act(self.board, self.turn)
                if col is not None and self.board.is_valid_location(col):
                    pygame.time.wait(500)  # Optional: pause for better visualization
                    self.drop_piece(col)

    def draw_board(self):
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(
                    self.screen, BLUE,
                    (c * SQUARE_SIZE, (r + 1) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )
                pygame.draw.circle(
                    self.screen, BLACK,
                    (c * SQUARE_SIZE + SQUARE_SIZE // 2, (r + 1) * SQUARE_SIZE + SQUARE_SIZE // 2),
                    RADIUS
                )

        for r in range(ROWS):
            for c in range(COLS):
                if self.board.grid[r][c] == 1:
                    pygame.draw.circle(
                        self.screen, RED,
                        (c * SQUARE_SIZE + SQUARE_SIZE // 2, (r + 1) * SQUARE_SIZE + SQUARE_SIZE // 2),
                        RADIUS
                    )
                elif self.board.grid[r][c] == 2:
                    pygame.draw.circle(
                        self.screen, YELLOW,
                        (c * SQUARE_SIZE + SQUARE_SIZE // 2, (r + 1) * SQUARE_SIZE + SQUARE_SIZE // 2),
                        RADIUS
                    )
        pygame.display.update()

    def run(self):
        self.draw_board()
        while not self.game_over:
            self.handle_events()
            self.update()
            self.draw_board()
            self.clock.tick(FPS)

        pygame.time.wait(3000)  # Wait for 3 seconds before closing

    def display_winner(self):
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, SQUARE_SIZE))
        label = FONT.render(f'Player {3 - self.turn} wins!', True, RED if (3 - self.turn) == 1 else YELLOW)
        self.screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, 10))
        pygame.display.update()

    def display_draw(self):
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, SQUARE_SIZE))
        label = FONT.render(f'Draw!', True, WHITE)
        self.screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, 10))
        pygame.display.update()

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
    print("6. Computer vs Computer")
    mode_input = input("Enter the number of the desired mode: ")

    mode_dict = {
        '1': 'human_vs_computer',
        '2': 'human_vs_human',
        '3': 'human_vs_agent',
        '4': 'agent_vs_agent',
        '5': 'agent_vs_computer',
        '6': 'computer_vs_computer'
    }

    mode = mode_dict.get(mode_input, 'human_vs_computer')

    # Initialize agents based on mode
    agent1 = None
    agent2 = None

    if mode == 'human_vs_computer':
        agent2 = SimpleComputerPlayer()
    elif mode == 'human_vs_agent':
        agent2 = HeuristicAgent()  # Replace with your custom agent
    elif mode == 'agent_vs_agent':
        agent1 = HeuristicAgent()
        agent2 = HeuristicAgent()
    elif mode == 'agent_vs_computer':
        agent1 = HeuristicAgent()
        agent2 = SimpleComputerPlayer()
    elif mode == 'computer_vs_computer':
        agent1 = SimpleComputerPlayer()
        agent2 = SimpleComputerPlayer()

    # Initialize and run the game
    game = ConnectFourGame(mode=mode, agent1=agent1, agent2=agent2)
    game.run()

if __name__ == '__main__':
    main()
