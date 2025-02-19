import json
import random
import socket
import threading
import time

GRID_SIZE = 9
EMPTY_CELLS = 10


class SudokuServer:
    def __init__(self):
        self.board = self.generate_solved_board()
        self.player_board = [
            [self.board[i][j] for j in range(GRID_SIZE)] for i in range(GRID_SIZE)
        ]
        self.create_puzzle()
        self.current_player = 1
        self.scores = {1: 0, 2: 0}
        self.clients = {}
        self.lock = threading.Lock()

    def generate_solved_board(self):
        board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.solve_sudoku(board)
        return board

    def create_puzzle(self):
        positions = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)]
        for _ in range(EMPTY_CELLS):
            pos = random.choice(positions)
            positions.remove(pos)
            self.player_board[pos[0]][pos[1]] = 0

    def solve_sudoku(self, board):
        find = self.find_empty(board)
        if not find:
            return True
        else:
            row, col = find

        for num in range(1, 10):
            if self.valid(board, num, (row, col)):
                board[row][col] = num
                if self.solve_sudoku(board):
                    return True
                board[row][col] = 0
        return False

    def find_empty(self, board):
        for i in range(len(board)):
            for j in range(len(board[0])):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def reset_game(self):
        self.board = self.generate_solved_board()
        self.player_board = [
            [self.board[i][j] for j in range(GRID_SIZE)] for i in range(GRID_SIZE)
        ]
        self.create_puzzle()
        self.current_player = 1
        self.scores = {1: 0, 2: 0}
        self.clients = {}

    def valid(self, board, num, pos):
        for j in range(GRID_SIZE):
            if board[pos[0]][j] == num and pos[1] != j:
                return False

        for i in range(GRID_SIZE):
            if board[i][pos[1]] == num and pos[0] != i:
                return False

        box_x = pos[1] // 3
        box_y = pos[0] // 3

        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
                if board[i][j] == num and (i, j) != pos:
                    return False

        return True

    def handle_move(self, row, col, number, player_id):
        with self.lock:
            if player_id != self.current_player:
                result = {
                    "valid": False,
                    "message": "Not your turn!",
                    "player_board": self.player_board,
                    "scores": self.scores,
                    "current_player": self.current_player,
                }
                return result

            if self.player_board[row][col] != 0:
                result = {
                    "valid": False,
                    "message": "Field already taken!",
                    "player_board": self.player_board,
                    "scores": self.scores,
                    "current_player": self.current_player,
                }
                return result

            # Check if move is valid
            if number == self.board[row][col]:
                # Valid move
                self.player_board[row][col] = number
                self.scores[player_id] = self.scores.get(player_id, 0) + 1
                result = {
                    "valid": True,
                    "points_added": True,
                    "message": "Good choice! +1 point",
                }
            else:
                # Invalid move
                self.scores[player_id] = self.scores.get(player_id, 0) - 1
                result = {
                    "valid": False,
                    "points_subtracted": True,
                    "message": "Bad choice! -1 point",
                }

            # Change of current player
            self.current_player = 2 if self.current_player == 1 else 1

            # Adding current game state to the response
            result.update(
                {
                    "player_board": self.player_board,
                    "scores": self.scores,
                    "current_player": self.current_player,
                }
            )

            # Check if the game has ended
            game_over = all(
                self.player_board[i][j] != 0
                for i in range(GRID_SIZE)
                for j in range(GRID_SIZE)
            )

            result.update(
                {
                    "player_board": self.player_board,
                    "scores": self.scores,
                    "current_player": self.current_player,
                    "game_over": game_over,
                }
            )

            print(
                f"Current game state - Results: {self.scores}, Current player: {self.current_player}"
            )

            return result

    def handle_client(self, client_socket, player_id):
        self.clients[player_id] = client_socket

        # Send initial game state
        initial_state = {
            "player_id": player_id,
            "player_board": self.player_board,
            "scores": self.scores,
            "current_player": self.current_player,
        }
        client_socket.send(json.dumps(initial_state).encode())

        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                move = json.loads(data)
                result = self.handle_move(
                    move["row"], move["col"], move["number"], player_id
                )

                # Send update to all clients
                update = json.dumps(result)
                for client in self.clients.values():
                    client.send(update.encode())

                # If the game ends, send the final result and break the connection
                if result.get("game_over", False):
                    final_message = {
                        "game_over": True,
                        "final_scores": self.scores,
                        "winner": max(self.scores, key=self.scores.get),
                    }

                    for client in self.clients.values():
                        client.send(json.dumps(final_message).encode())

                    break

            except Exception as e:
                print(f"Error: {e}")
                break

        del self.clients[player_id]
        client_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 35800))
    server_socket.listen(2)

    while True:
        server = SudokuServer()
        player_id = 1

        print("Server is running. Waiting for players to connect...")

        while player_id <= 2:
            client_socket, _ = server_socket.accept()
            print(f"Connected with player {player_id}")

            client_thread = threading.Thread(
                target=server.handle_client, args=(client_socket, player_id)
            )
            client_thread.start()

            player_id += 1

        # Wait for all clients to disconnect
        while len(server.clients) > 0:
            time.sleep(1)

        print("Game ended. Resetting board for new players...")


if __name__ == "__main__":
    main()
