# 📘 Video game Implementation of Nonaga with AI integration – Final Year Project

## 🎯 Overview
This project presents a digital implementation of the board game *Nonaga*, developed using **Python** and **Pygame**, with support for both **human vs human** and **human vs AI gameplay**.

Nonaga is a two-player abstract strategy game played on a hexagonal grid, where each player aims to connect all three of their pawns into a contiguous group. Unlike traditional board games, Nonaga features a dynamic board, where discs are removed and repositioned each turn, increasing strategic complexity.

The project combines:
- Interactive gameplay  
- Artificial intelligence  
- Efficient system design  

---

## 🧩 Features

### 🎮 Core Gameplay
- Fully functional Nonaga board game implementation  
- Accurate rule implementation:
  - Pawn movement (straight-line sliding)  
  - Disc removal and placement  
  - Win condition detection  
- Turn-based phase system:
  - Move Pawn → Remove Disc → Place Disc  

---

### 👥 Game Modes
- Two-player (local multiplayer)  
- Single-player vs AI  
- Additional variants:
  - Classic  
  - Mega (larger board)  
  - Survival (turn-based objective)  
  - Control (power-ups: gold & silver discs)  

---

### 🧠 Artificial Intelligence
- AI opponent based on:
  - Minimax Algorithm  
  - Alpha-Beta Pruning  

- Features:
  - Heuristic evaluation function  
  - Move generation with pruning  
  - Iterative deepening  
  - Transposition table (state caching)  
  - Mode-specific evaluation strategies  

---

### ⚡ Performance Optimisations
- Fast game state cloning (avoids expensive deep copies)  
- Move ordering to improve pruning efficiency  
- Candidate move filtering (top-k selection)  
- Persistent multiprocessing worker for AI  
- Responsive UI during AI computation  

---

### 🖥️ User Interface
- Built using **Pygame**  
- Features:
  - Interactive board rendering  
  - Move highlighting  
  - Timer system  
  - Pause menu  
  - Game-over interface  
  - Sound effects  

---

## 🏗️ System Architecture

The system is modular and divided into key components:

- `game_state.py`  
  Core game logic, board state, rules, and turn management  

- `ai_new.py`  
  AI logic (Minimax, Alpha-Beta, evaluation)  

- `ai_variants.py`  
  Mode-specific evaluation functions  

- `game_config.py`  
  Configuration for different game modes  

- `renderer.py`  
  Visual rendering of the game  

- `input_handler.py`  
  Handles player input and interactions  

- `menu.py`  
  Menu system and navigation  

- `nonaga.py`  
  Main game loop and system controller  

---

## ⚙️ Technologies Used

- **Python**  
  Chosen for readability, flexibility, and rapid development  

- **Pygame**  
  Used for rendering, event handling, and real-time interaction  

- **Multiprocessing**  
  Enables AI computation to run separately from the main game loop  

---

## 🧠 AI Design Summary

The AI uses a search-based approach:

### Minimax
- Explores possible game states  
- Maximises AI advantage while minimising opponent advantage  

### Alpha-Beta Pruning
- Reduces the number of evaluated nodes  
- Improves efficiency of the search  

### Evaluation Function
Considers:
- Pawn connectivity (primary objective)  
- Mobility (available moves)  
- Positional advantage  
- Mode-specific features  

---

## ⚖️ Design Considerations
- Balance between AI strength and performance  
- Separation of concerns (game logic, rendering, input, AI)  
- Modular design for maintainability and scalability  

---

## How to Run

From the project root directory, run:

```bash
python main.py
```

---

## Controls

| Control | Action |
|---|---|
| Left Click | Select pawn, move pawn, select disc, or place disc |
| Right Click Enemy Pawn | Preview enemy pawn moves |
| X | Cancel current selection |
| R | Restart game |
| Esc | Open pause menu |
| View Board | Hide game-over popup and view final board state |

---

## Game Rules Summary

On each turn, a player performs three actions:

1. Move one pawn in a straight line until blocked.
2. Remove a valid empty edge disc.
3. Place the removed disc in a new valid location.

A player wins when all of their pawns form one connected group.

---

## AI Design Summary

The AI uses Minimax with Alpha-Beta pruning to search possible future turns. Since a complete Nonaga turn contains multiple actions, the AI generates full-turn combinations in the form:

```text
(pawn_index, pawn_target, removed_disc, placed_disc)
```

The evaluation function considers:

- Pawn clustering
- Adjacent pawn pairs
- Opponent threats
- Mobility
- Mode-specific objectives
- Power-up positions in Control mode
- Survival pressure in Survival mode

---

## Testing

Automated testing was carried out using `pytest`.

The test suite validates:

- Game setup
- Pawn movement
- Disc removal and placement
- Win conditions
- Mode-specific mechanics
- AI move generation
- Regression bugs

To run the tests:

```bash
pytest -v
```

Current test result:

```text
36 passed
```

---

## AI Benchmarking

An AI benchmark script is included to compare the original AI implementation with the optimised AI implementation.

To run the benchmark:

```bash
python test/test_old_vs_new.py
```

The benchmark compares:

- Selected move
- Average computation time
- Minimum computation time
- Maximum computation time
- Whether both AI versions selected the same move

---

## Project Status

The project currently includes:

- Complete playable game
- Local multiplayer
- Single-player AI
- Four game modes
- Automated tests
- AI benchmarking
- Custom UI
- Sound effects

Future improvements could include:

- Online multiplayer
- Adjustable AI difficulty
- Self-play AI training
- More advanced AI search techniques
- More detailed tutorial system
- Additional animations and polish

---

## External Materials

This project uses Python, Pygame, and Pytest. Any external assets, libraries, or references used should be credited in the project report.

All main game logic, AI implementation, game modes, input handling, and integration code were developed as part of the project.

---

## Author

Lew Jun Keat 
Final Year Project  
Computer Science
