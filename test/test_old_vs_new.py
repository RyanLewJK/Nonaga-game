import sys
import os
import time
import copy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nonaga.game_state import NonagaGame
from src.nonaga.ai import choose_ai_turn as choose_old
from src.nonaga.ai_new import choose_ai_turn as choose_new


TEST_CASES = [
    ("opening", [], "A"),
    ("opening_B", [], "B"),
]


def apply_sequence(game, sequence):
    """
    sequence = list of tuples:
    (player, pawn_i, target, rem_key, place_key)
    """
    for player, pawn_i, target, rem_key, place_key in sequence:
        game.pawns[player][pawn_i] = target
        if rem_key in game.occupied:
            game.occupied.remove(rem_key)
        game.occupied.add(place_key)
        game.blocked = place_key
        game.current = "B" if player == "A" else "A"


def clone_game_state(game):
    g = NonagaGame.__new__(NonagaGame)
    g.occupied = set(game.occupied)
    g.pawns = {
        "A": [tuple(p) for p in game.pawns["A"]],
        "B": [tuple(p) for p in game.pawns["B"]],
    }
    g.current = game.current
    g.phase = game.phase
    g.selected_idx = game.selected_idx
    g.removable = game.removable
    g.blocked = game.blocked
    g.valid_moves = list(game.valid_moves)
    g.valid_removals = set(game.valid_removals)
    g.valid_placements = set(game.valid_placements)
    g.history = []
    return g


def build_test_positions():
    positions = []

    for name, seq, player in TEST_CASES:
        g = NonagaGame()
        apply_sequence(g, seq)
        positions.append((name, g, player))

    return positions


def benchmark_one(label, choose_fn, game, player, depth, topk, repeats=3):
    times = []
    chosen_turn = None

    for _ in range(repeats):
        g = clone_game_state(game)
        start = time.perf_counter()
        turn = choose_fn(g, player, depth=depth, top_k_placements=topk)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        chosen_turn = turn

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        "label": label,
        "turn": chosen_turn,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
    }


def run_benchmark(depth=2, topk=6, repeats=1):
    positions = build_test_positions()

    print(f"Benchmark settings: depth={depth}, top_k_placements={topk}, repeats={repeats}")
    print("=" * 70)

    for pos_name, game, player in positions:
        print(f"\nPosition: {pos_name} | Player to move: {player}")

        old_result = benchmark_one("OLD", choose_old, game, player, depth, topk, repeats)
        new_result = benchmark_one("NEW", choose_new, game, player, depth, topk, repeats)

        print(
            f"OLD -> turn={old_result['turn']} | "
            f"avg={old_result['avg_time']:.3f}s | "
            f"min={old_result['min_time']:.3f}s | "
            f"max={old_result['max_time']:.3f}s"
        )
        print(
            f"NEW -> turn={new_result['turn']} | "
            f"avg={new_result['avg_time']:.3f}s | "
            f"min={new_result['min_time']:.3f}s | "
            f"max={new_result['max_time']:.3f}s"
        )


if __name__ == "__main__":
    print("OLD from:", choose_old.__module__)
    print("NEW from:", choose_new.__module__)
    run_benchmark(depth=2, topk=6, repeats=1)