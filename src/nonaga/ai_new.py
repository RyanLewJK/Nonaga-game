# ai.py
# Updated: replaces copy.deepcopy(game) with a fast clone that does NOT copy undo history.
# This prevents the AI from freezing the game.

import math
from src.nonaga.game_state import NonagaGame
from src.nonaga.hexgrid import parse_key
from src.nonaga.ai_variants import evaluate_by_mode

TT = {}

def state_key(game, to_move, depth):
    return (
        tuple(sorted(game.occupied)),
        tuple(game.pawns["A"]),
        tuple(game.pawns["B"]),
        game.blocked,
        game.current,
        game.phase,
        to_move,
        depth,

        game.config.variant,

        game.survival_turn_count,

        game.gold_disc,
        game.silver_disc,
        game.gold_respawn_counter,
        game.silver_respawn_counter,

        game.extra_turn_active,
        game.special_remove_any,
    )

def adjacent_pair_count(pawns):
    count = 0
    n = len(pawns)
    for i in range(n):
        for j in range(i + 1, n):
            if hex_distance(pawns[i], pawns[j]) == 1:
                count += 1
    return count

# ---------- Fast clone ----------
def clone_game(g: NonagaGame) -> NonagaGame:
    ng = NonagaGame.__new__(NonagaGame)

    ng.config = g.config

    ng.occupied = set(g.occupied)
    ng.pawns = {
        "A": [tuple(p) for p in g.pawns["A"]],
        "B": [tuple(p) for p in g.pawns["B"]],
    }

    ng.current = g.current
    ng.phase = g.phase
    ng.selected_idx = g.selected_idx
    ng.removable = g.removable
    ng.blocked = g.blocked

    ng.time_left = dict(g.time_left)
    ng.winner = g.winner

    ng.human_player = g.human_player
    ng.ai_player = g.ai_player
    ng.survival_turn_count = g.survival_turn_count

    ng.gold_disc = g.gold_disc
    ng.silver_disc = g.silver_disc

    ng.gold_respawn_counter = g.gold_respawn_counter
    ng.silver_respawn_counter = g.silver_respawn_counter

    ng.extra_turn_active = g.extra_turn_active
    ng.special_remove_any = g.special_remove_any

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


def pairwise_distance_sum(pawns):
    total = 0
    n = len(pawns)
    for i in range(n):
        for j in range(i + 1, n):
            total += hex_distance(pawns[i], pawns[j])
    return total


def mobility(game, player):
    """How many slide endpoints the player has (more = better)."""
    total = 0
    for pos in game.pawns[player]:
        total += len(game.pawn_moves_from(pos))
    return total


def evaluate(game, ai_player):
    opp = "B" if ai_player == "A" else "A"

    winner = game.check_any_win()
    if winner == ai_player:
        return 10000
    if winner == opp:
        return -10000

    return evaluate_by_mode(game, ai_player)

def endpoint_score(game, player, pawn_i, target):
    g1 = clone_game(game)
    g1.pawns[player][pawn_i] = target
    opp = "B" if player == "A" else "A"

    my_cluster = pairwise_distance_sum(g1.pawns[player])
    opp_cluster = pairwise_distance_sum(g1.pawns[opp])
    my_adj = adjacent_pair_count(g1.pawns[player])
    opp_adj = adjacent_pair_count(g1.pawns[opp])

    return (-12 * my_cluster) + (8 * opp_cluster) + (30 * my_adj) - (35 * opp_adj)


def removal_score(g1, player, rem_key):
    if rem_key not in g1.occupied:
        return -10**9

    opp = "B" if player == "A" else "A"
    g2 = clone_game(g1)
    g2.occupied.remove(rem_key)

    pos = parse_key(rem_key)
    near_me = min(hex_distance(pos, p) for p in g2.pawns[player])
    near_opp = min(hex_distance(pos, p) for p in g2.pawns[opp])

    my_cluster = pairwise_distance_sum(g2.pawns[player])
    opp_cluster = pairwise_distance_sum(g2.pawns[opp])
    my_adj = adjacent_pair_count(g2.pawns[player])
    opp_adj = adjacent_pair_count(g2.pawns[opp])
    my_mob = mobility(g2, player)
    opp_mob = mobility(g2, opp)

    return (
        -10 * my_cluster
        + 8 * opp_cluster
        + 25 * my_adj
        - 30 * opp_adj
        + 2 * (my_mob - opp_mob)
        - 2 * near_me
        - 2 * near_opp
    )

def generate_turns(game, player, top_k_placements=6, root=False):
    """
    Generate full-turn actions:
      (pawn_index, pawn_target_pos, remove_disc_key, place_disc_key)

    root=True:
      wider candidate generation for tactical checks at the root
    root=False:
      tighter pruning for minimax search
    """
    turns = []
    opp = "B" if player == "A" else "A"

    if root:
        endpoint_limit = 3
        removal_limit = 6
        placement_limit = max(top_k_placements, 12)
    else:
        endpoint_limit = 2
        removal_limit = 4
        placement_limit = top_k_placements

    for pawn_i, pawn_pos in enumerate(game.pawns[player]):
        endpoints = game.pawn_moves_from(pawn_pos)
        endpoints.sort(key=lambda t: endpoint_score(game, player, pawn_i, t), reverse=True)
        endpoints = endpoints[:endpoint_limit]

        for target in endpoints:
            g1 = clone_game(game)
            g1.pawns[player][pawn_i] = target

            removals = list(g1.compute_valid_removals())
            removals.sort(key=lambda rem: removal_score(g1, player, rem), reverse=True)
            removals = removals[:removal_limit]

            for rem_key in removals:
                g2 = clone_game(g1)

                if rem_key not in g2.occupied:
                    continue

                g2.occupied.remove(rem_key)

                placements = list(g2.compute_valid_placements())
                if not placements:
                    continue

                # Filter out placements far from both sides.
                filtered = []
                for place_key in placements:
                    pos = parse_key(place_key)
                    near_me = min(hex_distance(pos, p) for p in g2.pawns[player])
                    near_opp = min(hex_distance(pos, p) for p in g2.pawns[opp])

                    if root:
                        keep = min(near_me, near_opp) <= 3
                    else:
                        keep = min(near_me, near_opp) <= 2

                    if keep:
                        filtered.append(place_key)

                if filtered:
                    placements = filtered

                def place_score(place_key):
                    pos = parse_key(place_key)
                    near_me = min(hex_distance(pos, p) for p in g2.pawns[player])
                    near_opp = min(hex_distance(pos, p) for p in g2.pawns[opp])

                    # Prefer placements near our pawns and also near the opponent to interfere.
                    return (-2 * near_me) - (1 * near_opp)

                placements.sort(key=place_score, reverse=True)

                for place_key in placements[:placement_limit]:
                    turns.append((pawn_i, target, rem_key, place_key))

    return turns


def apply_turn(game, player, turn):
    pawn_i, target, rem_key, place_key = turn

    game.current = player
    game.pawns[player][pawn_i] = target
    game.handle_special_landing(player, target)

    if rem_key in game.occupied:
        game.occupied.remove(rem_key)

    game.occupied.add(place_key)
    game.end_turn_after_placement(place_key)


# ---------- Minimax with alpha-beta ----------
def minimax(game, depth, alpha, beta, to_move, ai_player, top_k_placements=12):
    key = state_key(game, to_move, depth)
    if key in TT:
        return TT[key]

    if depth == 0 or game.check_any_win() is not None:
        val = evaluate(game, ai_player)
        TT[key] = val
        return val

    turns = generate_turns(game, to_move, top_k_placements=top_k_placements)
    if not turns:
        val = evaluate(game, ai_player)
        TT[key] = val
        return val

    # Move ordering improves pruning
    scored = []
    for t in turns:
        g2 = clone_game(game)
        apply_turn(g2, to_move, t)
        scored.append((evaluate(g2, ai_player), t))

    scored.sort(key=lambda x: x[0], reverse=(to_move == ai_player))
    ordered_turns = [t for _, t in scored]

    if to_move == ai_player:
        best = -math.inf
        fully_searched = True

        for t in ordered_turns:
            g2 = clone_game(game)
            apply_turn(g2, to_move, t)

            next_to_move = g2.current
            val = minimax(
                g2,
                depth - 1,
                alpha,
                beta,
                next_to_move,
                ai_player,
                top_k_placements
            )

            best = max(best, val)
            alpha = max(alpha, val)

            if beta <= alpha:
                fully_searched = False
                break

        if fully_searched:
            TT[key] = best
        return best

    else:
        best = math.inf
        fully_searched = True

        for t in ordered_turns:
            g2 = clone_game(game)
            apply_turn(g2, to_move, t)

            next_to_move = g2.current
            val = minimax(
                g2,
                depth - 1,
                alpha,
                beta,
                next_to_move,
                ai_player,
                top_k_placements
            )

            best = min(best, val)
            beta = min(beta, val)

            if beta <= alpha:
                fully_searched = False
                break

        if fully_searched:
            TT[key] = best
        return best


def choose_ai_turn_at_depth(game, ai_player, depth, top_k_placements=6):
    """Choose best move at one fixed search depth."""
    best_turn = None
    best_val = -math.inf

    turns = generate_turns(game, ai_player, top_k_placements=top_k_placements, root=False)
    if not turns:
        return None

    for t in turns:
        g2 = clone_game(game)
        apply_turn(g2, ai_player, t)

        if g2.check_any_win() == ai_player:
            return t

        next_to_move = g2.current
        val = minimax(
            g2,
            depth - 1,
            -math.inf,
            math.inf,
            next_to_move,
            ai_player,
            top_k_placements
        )

        if val > best_val:
            best_val = val
            best_turn = t

    return best_turn

def choose_ai_turn(game, ai_player, depth=3, top_k_placements=6):
    """Return best full-turn action for ai_player, or None if no moves."""
    TT.clear()

    # 1. Wider root scan to avoid pruning away obvious tactical wins.
    root_turns = generate_turns(game, ai_player, top_k_placements=top_k_placements, root=True)
    if not root_turns:
        return None

    for t in root_turns:
        g2 = clone_game(game)
        apply_turn(g2, ai_player, t)
        if g2.check_any_win() == ai_player:
            print("Immediate winning move found:", t)
            return t

    # 2. Iterative deepening over the tighter search generator.
    best_turn = None
    for d in range(1, depth + 1):
        turn = choose_ai_turn_at_depth(game, ai_player, d, top_k_placements)
        if turn is not None:
            best_turn = turn

    return best_turn