import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# ---------------------------
# Game Constants
# ---------------------------
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 300
GRID_SIZE = 3
SQUARE_SIZE = SCREEN_WIDTH // GRID_SIZE
LINE_WIDTH = 5
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Font
FONT = pygame.font.SysFont('Arial', 30)

# ---------------------------
# Game Board Class
# ---------------------------
class Board:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def reset(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def is_valid_move(self, row, col):
        return self.grid[row][col] == 0

    def make_move(self, row, col, player):
        if self.is_valid_move(row, col):
            self.grid[row][col] = player
            return True
        return False

    def check_winner(self):
        # Check rows, columns, and diagonals
        for i in range(GRID_SIZE):
            if all(self.grid[i][j] == self.grid[i][0] != 0 for j in range(GRID_SIZE)):
                return self.grid[i][0]
            if all(self.grid[j][i] == self.grid[0][i] != 0 for j in range(GRID_SIZE)):
                return self.grid[0][i]

        # Check diagonals
        if all(self.grid[i][i] == self.grid[0][0] != 0 for i in range(GRID_SIZE)):
            return self.grid[0][0]
        if all(self.grid[i][GRID_SIZE - i - 1] == self.grid[0][GRID_SIZE - 1] != 0 for i in range(GRID_SIZE)):
            return self.grid[0][GRID_SIZE - 1]

        # Check for draw
        if all(self.grid[i][j] != 0 for i in range(GRID_SIZE) for j in range(GRID_SIZE)):
            return 'draw'

        return None

# ---------------------------
# Agent Interface
# ---------------------------
class AgentInterface:
    def act(self, board, player):
        """
        Implement your agent's decision-making here.
        This function should return a tuple (row, col) where the player will make a move.
        """
        raise NotImplementedError("This method should be overridden by subclasses")

# ---------------------------
# Simple Computer Player
# ---------------------------
class SimpleComputerPlayer(AgentInterface):
    def act(self, board, player):
        # Simple AI that picks a random available spot
        available_moves = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if board.is_valid_move(r, c)]
        if available_moves:
            return random.choice(available_moves)
        return None

# ---------------------------
# Game Class
# ---------------------------
class TicTacToeGame:
    def __init__(self, mode='human_vs_computer', agent1=None, agent2=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Tic Tac Toe')

        self.clock = pygame.time.Clock()
        self.board = Board()
        self.mode = mode
        self.turn = 1  # Player 1 starts as X, Player 2 as O
        self.game_over = False

        # Assign agents
        self.agent1 = agent1  # Agent for Player 1 (X)
        self.agent2 = agent2  # Agent for Player 2 (O)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle mouse clicks only if the current player is human
            if not ((self.turn == 1 and self.agent1) or (self.turn == 2 and self.agent2)):
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    pos = event.pos
                    row = pos[1] // SQUARE_SIZE
                    col = pos[0] // SQUARE_SIZE
                    if self.board.is_valid_move(row, col):
                        self.make_move(row, col)

    def make_move(self, row, col):
        if self.board.make_move(row, col, self.turn):
            winner = self.board.check_winner()
            if winner:
                self.game_over = True
                self.display_winner(winner)
            self.turn = 3 - self.turn  # Switch turn

    def update(self):
        # If it's an agent's turn, let the agent make a move
        if not self.game_over:
            if self.turn == 1 and self.agent1:
                row, col = self.agent1.act(self.board, self.turn)
                if row is not None and col is not None:
                    pygame.time.wait(500)  # Optional: pause for better visualization
                    self.make_move(row, col)
            elif self.turn == 2 and self.agent2:
                row, col = self.agent2.act(self.board, self.turn)
                if row is not None and col is not None:
                    pygame.time.wait(500)  # Optional: pause for better visualization
                    self.make_move(row, col)

    def draw_board(self):
        self.screen.fill(WHITE)
        # Draw grid lines
        for i in range(1, GRID_SIZE):
            pygame.draw.line(self.screen, BLACK, (0, i * SQUARE_SIZE), (SCREEN_WIDTH, i * SQUARE_SIZE), LINE_WIDTH)
            pygame.draw.line(self.screen, BLACK, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, SCREEN_HEIGHT), LINE_WIDTH)

        # Draw X's and O's
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.board.grid[r][c] == 1:
                    pygame.draw.line(self.screen, RED,
                                     (c * SQUARE_SIZE + 20, r * SQUARE_SIZE + 20),
                                     ((c + 1) * SQUARE_SIZE - 20, (r + 1) * SQUARE_SIZE - 20), LINE_WIDTH)
                    pygame.draw.line(self.screen, RED,
                                     ((c + 1) * SQUARE_SIZE - 20, r * SQUARE_SIZE + 20),
                                     (c * SQUARE_SIZE + 20, (r + 1) * SQUARE_SIZE - 20), LINE_WIDTH)
                elif self.board.grid[r][c] == 2:
                    pygame.draw.circle(self.screen, BLUE,
                                       (c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + SQUARE_SIZE // 2),
                                       SQUARE_SIZE // 2 - 15, LINE_WIDTH)
        pygame.display.update()

    def run(self):
        self.draw_board()
        while not self.game_over:
            self.handle_events()
            self.update()
            self.draw_board()
            self.clock.tick(FPS)

        pygame.time.wait(3000)  # Wait for 3 seconds before closing

    def display_winner(self, winner):
        pygame.draw.rect(self.screen, WHITE, (0, SCREEN_HEIGHT // 2 - 30, SCREEN_WIDTH, 60))
        if winner == 'draw':
            label = FONT.render('Draw!', True, BLACK)
        else:
            label = FONT.render(f'Player {winner} wins!', True, RED if winner == 1 else BLUE)
        self.screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, SCREEN_HEIGHT // 2 - label.get_height() // 2))
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
        agent2 = SimpleComputerPlayer()
    elif mode == 'agent_vs_agent':
        agent1 = SimpleComputerPlayer()
        agent2 = SimpleComputerPlayer()
    elif mode == 'agent_vs_computer':
        agent1 = SimpleComputerPlayer()
        agent2 = SimpleComputerPlayer()
    elif mode == 'computer_vs_computer':
        agent1 = SimpleComputerPlayer()
        agent2 = SimpleComputerPlayer()

    # Initialize and run the game
    game = TicTacToeGame(mode=mode, agent1=agent1, agent2=agent2)
    game.run()

if __name__ == '__main__':
    main()
