# Sudoku for 2 players

Welcome to the Two-Player Sudoku Game, a project designed to bring the classic puzzle-solving challenge of Sudoku to a new level by enabling two players to compete in real-time. Developed using Pygame and employing a client-server architecture, this game ensures seamless synchronization and communication between players using TCP stream sockets.

Players can enjoy Sudoku while competing against a friend or another player online, with the game grid shared and moves synchronized in real-time. The intuitive user interface makes the game accessible and enjoyable for players of all ages. The server manages the game state, ensuring both clients have the same view of the grid. Moves are sent to the server, which updates the game state and broadcasts it to the other client.

## How to run it locally?

### Prerequisites

- Python 3.12
- Poetry

1. **Clone the Repository**
2. **Install Dependencies**

```sh
poetry install
```

3. **Run the Server**

```sh
poetry run python src/server.py
```

4. **Run the Client**

```sh
poetry run python src/client.py
```

5. **Run the Client again for the second player**
6. **Enjoy the game!**
