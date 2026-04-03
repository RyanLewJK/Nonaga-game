# ai.py
# Updated: replaces copy.deepcopy(game) with a fast clone that does NOT copy undo history.
# This prevents the AI from freezing the game.

import math
from src.nonaga.game_state import NonagaGame


# ---------- Fast clone ----------
def clone_game(g: NonagaGame) -> NonagaGame:
    """
    Fast clone for AI search.
    Copies only what's needed for legal moves + evaluation.
    DOES NOT copy g.history (undo stack), which makes deepcopy extremely slow.
    """
    ng = NonagaGame.__new__(NonagaGame)  # bypass __init__ (so we don't reset)

    ng.occupied = set(g.occupied)
    ng.pawns = {
        "A": [tuple(p) for p in g.pawns["A"]],
        "B": [tuple(p) for p in g.pawns["B"]],
    }

    ng.current = g.current
    ng.phase = g.phase
    ng.selected_idx = None
    ng.removable = None
    ng.blocked = g.blocked

    # not needed for AI correctness
    ng.valid_moves = []
    ng.valid_removals = set()
    ng.valid_placements = set()
    ng.history = []

    return ng


# ---------- Helpers ----------
def hex_distance(a, b):
    """Axial hex distance."""
    aq, ar = a
    bq, br = b
    return (abs(aq - bq) + abs((aq + ar) - (bq + br)) + abs(ar - br)) // 2


def pairwise_distance_sum(pawns3):
    """Sum of distances between the 3 pawns. Smaller = more connected."""
    a, b, c = pawns3
    return hex_distance(a, b) + hex_distance(a, c) + hex_distance(b, c)


def mobility(game, player):
    """How many slide endpoints the player has (more = better)."""
    total = 0
    for pos in game.pawns[player]:
        total += len(game.pawn_moves_from(pos))
    return total


def evaluate(game, ai_player):
    """Heuristic score: higher is better for ai_player."""
    opp = "B" if ai_player == "A" else "A"

    if game.is_win(ai_player):
        return 10_000
    if game.is_win(opp):
        return -10_000

    my_cluster = pairwise_distance_sum(game.pawns[ai_player])   # want small
    opp_cluster = pairwise_distance_sum(game.pawns[opp])        # want large
    my_mob = mobility(game, ai_player)
    opp_mob = mobility(game, opp)

    return (-15 * my_cluster) + (10 * opp_cluster) + (3 * (my_mob - opp_mob))


def generate_turns(game, player, top_k_placements=6):
    """
    Generate full-turn actions:
      (pawn_index, pawn_target_pos, remove_disc_key, place_disc_key)

    We aggressively limit branching to prevent freezing.
    """

    turns = []
    opp = "B" if player == "A" else "A"

    for pawn_i, pawn_pos in enumerate(game.pawns[player]):

        # --- LIMIT 1: restrict pawn slide destinations ---
        endpoints = game.pawn_moves_from(pawn_pos)
        endpoints = endpoints[:3]   # <--- ADD THIS LINE

        for target in endpoints:
            g1 = clone_game(game)
            g1.pawns[player][pawn_i] = target

            # --- LIMIT 2: restrict removable discs ---
            removals = list(g1.compute_valid_removals())
            removals = removals[:5]   # <--- ADD THIS LINE

            for rem_key in removals:
                g2 = clone_game(g1)

                if rem_key not in g2.occupied:
                    continue

                g2.occupied.remove(rem_key)

                placements = list(g2.compute_valid_placements())
                if not placements:
                    continue

                my_pawns = g2.pawns[player]
                opp_pawns = g2.pawns[opp]

                def place_score(place_key):
                    q, r = map(int, place_key.split(","))
                    pos = (q, r)
                    near_me = min(hex_distance(pos, p) for p in my_pawns)
                    near_opp = min(hex_distance(pos, p) for p in opp_pawns)
                    return (-3 * near_me) + (1 * near_opp)

                placements.sort(key=place_score, reverse=True)

                # --- LIMIT 3: restrict placements (already existed) ---
                for place_key in placements[:top_k_placements]:
                    turns.append((pawn_i, target, rem_key, place_key))

    return turns


def apply_turn(game, player, turn):
    """Apply a full turn to a game clone."""
    pawn_i, target, rem_key, place_key = turn
    game.pawns[player][pawn_i] = target
    game.occupied.remove(rem_key)
    game.occupied.add(place_key)
    game.blocked = place_key


# ---------- Minimax with alpha-beta ----------
def minimax(game, depth, alpha, beta, to_move, ai_player, top_k_placements=12):
    opp = "B" if to_move == "A" else "A"

    if depth == 0 or game.is_win("A") or game.is_win("B"):
        return evaluate(game, ai_player)

    turns = generate_turns(game, to_move, top_k_placements=top_k_placements)
    if not turns:
        return evaluate(game, ai_player)

    # Move ordering improves pruning
    scored = []
    for t in turns:
        g2 = clone_game(game)
        apply_turn(g2, to_move, t)
        scored.append((evaluate(g2, ai_player), t))

    scored.sort(key=lambda x: x[0], reverse=(to_move == ai_player))
    ordered_turns = [t for _, t in scored]

    if to_move == ai_player:  # maximize
        best = -math.inf
        for t in ordered_turns:
            g2 = clone_game(game)
            apply_turn(g2, to_move, t)
            val = minimax(g2, depth - 1, alpha, beta, opp, ai_player, top_k_placements)
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best
    else:  # minimize
        best = math.inf
        for t in ordered_turns:
            g2 = clone_game(game)
            apply_turn(g2, to_move, t)
            val = minimax(g2, depth - 1, alpha, beta, opp, ai_player, top_k_placements)
            best = min(best, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best


def choose_ai_turn(game, ai_player, depth=3, top_k_placements=12):
    """Return best full-turn action for ai_player, or None if no moves."""
    opp = "B" if ai_player == "A" else "A"
    best_turn = None
    best_val = -math.inf

    turns = generate_turns(game, ai_player, top_k_placements=top_k_placements)
    if not turns:
        return None

    for t in turns:
        g2 = clone_game(game)
        apply_turn(g2, ai_player, t)
        val = minimax(g2, depth - 1, -math.inf, math.inf, opp, ai_player, top_k_placements)
        if val > best_val:
            best_val = val
            best_turn = t

    return best_turn