import json
import socket
import sys
import threading

import pygame

pygame.init()

WIDTH = 540
HEIGHT = 640
CELL_SIZE = 60
GRID_SIZE = 9

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class SudokuClient:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sudoku for 2 players")
        self.font = pygame.font.Font(None, 36)
        self.selected_cell = None
        self.player_board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.scores = {1: 0, 2: 0}
        self.current_player = 1
        self.player_id = None
        self.lock = threading.Lock()
        self.game_over = False
        self.winner_message = None

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(("localhost", 35800))

            initial_state = json.loads(self.socket.recv(1024).decode())

            with self.lock:
                self.player_id = initial_state.get("player_id", 1)
                self.player_board = initial_state.get("player_board", self.player_board)
                self.scores = initial_state.get("scores", {1: 0, 2: 0})
                self.current_player = initial_state.get("current_player", 1)

        except Exception as e:
            print(f"Error while connecting to the server: {e}")
            pygame.quit()
            sys.exit(1)

    def draw(self):
        try:
            self.screen.fill(WHITE)

            for i in range(GRID_SIZE + 1):
                line_width = 3 if i % 3 == 0 else 1
                pygame.draw.line(
                    self.screen,
                    BLACK,
                    (i * CELL_SIZE, 0),
                    (i * CELL_SIZE, WIDTH),
                    line_width,
                )
                pygame.draw.line(
                    self.screen,
                    BLACK,
                    (0, i * CELL_SIZE),
                    (WIDTH, i * CELL_SIZE),
                    line_width,
                )

            with self.lock:
                board = [row[:] for row in self.player_board]
                scores = dict(self.scores)
                current_player = self.current_player
                player_id = self.player_id
                selected = self.selected_cell

            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    if board[i][j] != 0:
                        value = self.font.render(str(board[i][j]), True, BLACK)
                        self.screen.blit(
                            value, (j * CELL_SIZE + 20, i * CELL_SIZE + 15)
                        )

            if selected:
                pygame.draw.rect(
                    self.screen,
                    BLUE,
                    (
                        selected[1] * CELL_SIZE,
                        selected[0] * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    ),
                    3,
                )

            status_text = f"Round: {current_player}"
            status = self.font.render(status_text, True, BLACK)

            score1 = scores.get(1, 0)
            score2 = scores.get(2, 0)

            player1_text = self.font.render(f"Player 1: {score1} pts", True, BLACK)
            player2_text = self.font.render(f"Player 2: {score2} pts", True, BLACK)
            current_player_text = self.font.render(
                f"Current player: Player {current_player}",
                True,
                GREEN if current_player == player_id else RED,
            )

            self.screen.blit(status, (10, HEIGHT - 80))
            self.screen.blit(player1_text, (150, HEIGHT - 80))
            self.screen.blit(player2_text, (350, HEIGHT - 80))
            self.screen.blit(current_player_text, (10, HEIGHT - 30))

            # Display result message
            if self.game_over and self.winner_message:
                s = pygame.Surface((WIDTH, HEIGHT))
                s.set_alpha(128)
                s.fill((0, 0, 0))
                self.screen.blit(s, (0, 0))

                winner_font = pygame.font.Font(None, 48)
                winner_text = winner_font.render(self.winner_message, True, GREEN)
                text_rect = winner_text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
                self.screen.blit(winner_text, text_rect)

                # Exit screen
                exit_font = pygame.font.Font(None, 36)
                exit_text = exit_font.render("Press ESC to exit", True, WHITE)
                exit_rect = exit_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 50))
                self.screen.blit(exit_text, exit_rect)

        except Exception as e:
            print(f"Error while drawing: {e}")

    def handle_click(self, pos):
        if pos[1] < WIDTH:
            col = pos[0] // CELL_SIZE
            row = pos[1] // CELL_SIZE
            if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                if self.player_board[row][col] == 0:
                    self.selected_cell = (row, col)

    def make_move(self, number):
        if self.selected_cell and self.current_player == self.player_id:
            row, col = self.selected_cell
            move = {"row": row, "col": col, "number": number}

            try:
                self.socket.send(json.dumps(move).encode())
                return True
            except Exception as e:
                print(f"Error while sending move: {e}")

        return False

    def update_game_state(self, state):
        try:
            with self.lock:
                if "player_board" in state:
                    self.player_board = state["player_board"]

                if "scores" in state:
                    self.scores = {int(k): v for k, v in state["scores"].items()}

                if "current_player" in state:
                    self.current_player = state["current_player"]

                if "game_over" in state:
                    self.game_over = state["game_over"]
                    if self.game_over:
                        scores = self.scores
                        if scores[1] > scores[2]:
                            self.winner_message = "Player 1 wins!"
                        elif scores[2] > scores[1]:
                            self.winner_message = "Player 2 wins!"
                        else:
                            self.winner_message = "Tie!"

                self.selected_cell = None

        except Exception as e:
            print(f"Error while updating game state: {e}")


def main():
    client = SudokuClient()
    running = True

    def receive_updates():
        while running:
            try:
                data = client.socket.recv(1024).decode()
                if not data:
                    print("Connection to the server closed")
                    break
                state = json.loads(data)
                client.update_game_state(state)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            except Exception as e:
                print(f"Error in the thread: {e}")
                break

    update_thread = threading.Thread(target=receive_updates)
    update_thread.daemon = True
    update_thread.start()

    while running:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and client.game_over:
                        running = False
                    elif not client.game_over and event.key in [
                        pygame.K_1,
                        pygame.K_2,
                        pygame.K_3,
                        pygame.K_4,
                        pygame.K_5,
                        pygame.K_6,
                        pygame.K_7,
                        pygame.K_8,
                        pygame.K_9,
                    ]:
                        number = int(event.unicode)
                        client.make_move(number)

                if not client.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                    client.handle_click(event.pos)

            client.draw()
            pygame.display.flip()
            pygame.time.delay(50)

        except Exception as e:
            print(f"Error in main loop: {e}")
            running = False

    print("Exiting the game...")

    client.socket.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
