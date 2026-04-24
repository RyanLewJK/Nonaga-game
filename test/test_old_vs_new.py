import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nonaga.game_state import NonagaGame
from src.nonaga.game_config import classic_config
from src.nonaga.ai import choose_ai_turn as choose_old
from src.nonaga.ai_new import choose_ai_turn as choose_new, clone_game as clone_new


TEST_CASES = [
    ("opening_A", [], "A"),
    ("opening_B", [], "B"),
]


def apply_sequence(game, sequence):
    for player, pawn_i, target, rem_key, place_key in sequence:
        game.pawns[player][pawn_i] = target

        if rem_key in game.occupied:
            game.occupied.remove(rem_key)

        game.occupied.add(place_key)
        game.current = "B" if player == "A" else "A"
        game.recompute()


def clone_for_old_ai(game):
    """
    Clone only the fields required by the old Classic AI.
    """
    g = NonagaGame.__new__(NonagaGame)

    g.occupied = set(game.occupied)
    g.pawns = {
        "A": [tuple(p) for p in game.pawns["A"]],
        "B": [tuple(p) for p in game.pawns["B"]],
    }

    g.current = game.current
    g.phase = game.phase
    g.selected_idx = None
    g.removable = None
    g.blocked = game.blocked

    g.valid_moves = []
    g.valid_removals = set()
    g.valid_placements = set()
    g.history = []

    g.config = game.config
    g.time_left = dict(game.time_left)
    g.winner = game.winner

    g.human_player = game.human_player
    g.ai_player = game.ai_player
    g.survival_turn_count = 0

    g.gold_disc = None
    g.silver_disc = None
    g.gold_respawn_counter = 0
    g.silver_respawn_counter = 0

    g.special_remove_any = False
    g.gold_move_enemy_active = False
    g.gold_movable_enemy_indices = []
    g.gold_valid_enemy_moves = []
    g.gold_selected_enemy_idx = None

    g.last_action_text = ""
    g.last_action_timer = 0.0

    g.removed_was_gold = False
    g.removed_was_silver = False

    return g


def build_test_positions():
    positions = []

    for name, seq, player in TEST_CASES:
        g = NonagaGame(config=classic_config())
        apply_sequence(g, seq)
        positions.append((name, g, player))

    return positions


def benchmark_one(label, choose_fn, clone_fn, game, player, depth, topk, repeats=3):
    times = []
    chosen_turn = None

    for _ in range(repeats):
        g = clone_fn(game)

        start = time.perf_counter()
        turn = choose_fn(g, player, depth=depth, top_k_placements=topk)
        elapsed = time.perf_counter() - start

        times.append(elapsed)
        chosen_turn = turn

    return {
        "label": label,
        "turn": chosen_turn,
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
    }


def run_benchmark(depth=2, topk=6, repeats=1):
    positions = build_test_positions()

    print(f"Benchmark settings: depth={depth}, top_k_placements={topk}, repeats={repeats}")
    print("=" * 80)

    for pos_name, game, player in positions:
        print(f"\nPosition: {pos_name} | Player to move: {player}")

        old_result = benchmark_one(
            "OLD",
            choose_old,
            clone_for_old_ai,
            game,
            player,
            depth,
            topk,
            repeats
        )

        new_result = benchmark_one(
            "NEW",
            choose_new,
            clone_new,
            game,
            player,
            depth,
            topk,
            repeats
        )

        same_move = old_result["turn"] == new_result["turn"]

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

        print("Same move:", same_move)


if __name__ == "__main__":
    print("OLD from:", choose_old.__module__)
    print("NEW from:", choose_new.__module__)

    run_benchmark(depth=2, topk=4, repeats=1)