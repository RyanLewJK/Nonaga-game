import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.ai import choose_ai_turn, apply_turn

AI_1 = ("D2_K12", 2, 12)
AI_2 = ("D3_K6", 3, 6)

MAX_TURNS = 20


def run_game(game_index: int):
    game = NonagaGame()

    # Alternate starting sides
    if game_index % 2 == 1:
        settings = {
            "A": AI_1,
            "B": AI_2,
        }
    else:
        settings = {
            "A": AI_2,
            "B": AI_1,
        }

    print(f"\nStarting game {game_index}", flush=True)

    turn_no = 0
    think_times = {"D2_K12": [], "D3_K6": []}

    while game.phase != Phase.GAME_OVER and turn_no < MAX_TURNS:
        player = game.current
        label, depth, topk = settings[player]

        print(
            f"  Turn {turn_no + 1}: Player {player} using {label} "
            f"(depth={depth}, topk={topk})",
            flush=True
        )

        start = time.perf_counter()
        turn = choose_ai_turn(game, player, depth=depth, top_k_placements=topk)
        elapsed = time.perf_counter() - start
        think_times[label].append(elapsed)

        print(f"    Move: {turn}", flush=True)
        print(f"    Time: {elapsed:.3f}s", flush=True)

        if turn is None:
            winner = "B" if player == "A" else "A"
            return {
                "winner_side": winner,
                "winner_label": settings[winner][0],
                "turns": turn_no,
                "times": think_times,
                "status": "NO_MOVE"
            }

        apply_turn(game, player, turn)

        if game.is_win(player):
            game.phase = Phase.GAME_OVER
            return {
                "winner_side": player,
                "winner_label": label,
                "turns": turn_no + 1,
                "times": think_times,
                "status": "WIN"
            }

        game.current = "B" if game.current == "A" else "A"
        turn_no += 1

    return {
        "winner_side": None,
        "winner_label": "DRAW",
        "turns": turn_no,
        "times": think_times,
        "status": "DRAW"
    }


def avg(lst):
    return sum(lst) / len(lst) if lst else 0.0


def run_match(num_games=2):
    wins = {
        "D2_K12": 0,
        "D3_K6": 0,
        "DRAW": 0,
    }

    d2_times = []
    d3_times = []

    for i in range(1, num_games + 1):
        result = run_game(i)

        wins[result["winner_label"]] += 1
        d2_times.extend(result["times"]["D2_K12"])
        d3_times.extend(result["times"]["D3_K6"])

        print(
            f"Finished game {i}: status={result['status']}, "
            f"winner={result['winner_label']}, turns={result['turns']}",
            flush=True
        )

    print("\n=== FINAL RESULTS ===", flush=True)
    print(f"D2_K12 wins: {wins['D2_K12']}", flush=True)
    print(f"D3_K6 wins: {wins['D3_K6']}", flush=True)
    print(f"Draws: {wins['DRAW']}", flush=True)
    print(f"D2_K12 avg think time: {avg(d2_times):.3f}s", flush=True)
    print(f"D3_K6 avg think time: {avg(d3_times):.3f}s", flush=True)


if __name__ == "__main__":
    run_match(num_games=2)