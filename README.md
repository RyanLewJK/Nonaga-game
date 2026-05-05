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

## 🚀 How to Run

### Requirements
- Python 3.x  
- Pygame  

### Installation
