# ai.py
# Updated: replaces copy.deepcopy(game) with a fast clone that does NOT copy undo history.
# This prevents the AI from freezing the game.

import math
from src.nonaga.game_state import NonagaGame
from src.nonaga.hexgrid import parse_key, k
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

        game.special_remove_any,

        game.gold_move_enemy_active,
        tuple(game.gold_movable_enemy_indices),
        tuple(game.gold_valid_enemy_moves),
        game.gold_selected_enemy_idx,
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
    """
    Fast clone for AI search.
    Copies only what is needed for move generation, special mode logic,
    and evaluation. Does not copy undo history.
    """
    ng = NonagaGame.__new__(NonagaGame)

    # config / mode
    ng.config = g.config

    # board + pawns
    ng.occupied = set(g.occupied)
    ng.pawns = {
        "A": [tuple(p) for p in g.pawns["A"]],
        "B": [tuple(p) for p in g.pawns["B"]],
    }

    # turn state
    ng.current = g.current
    ng.phase = g.phase
    ng.selected_idx = g.selected_idx
    ng.removable = g.removable
    ng.blocked = g.blocked

    # timer / winner
    ng.time_left = dict(g.time_left)
    ng.winner = g.winner

    # mode-specific state
    ng.human_player = g.human_player
    ng.ai_player = g.ai_player
    ng.survival_turn_count = g.survival_turn_count

    ng.gold_disc = g.gold_disc
    ng.silver_disc = g.silver_disc

    ng.gold_respawn_counter = g.gold_respawn_counter
    ng.silver_respawn_counter = g.silver_respawn_counter

    ng.special_remove_any = g.special_remove_any

    ng.gold_move_enemy_active = g.gold_move_enemy_active
    ng.gold_movable_enemy_indices = list(g.gold_movable_enemy_indices)
    ng.gold_valid_enemy_moves = list(g.gold_valid_enemy_moves)
    ng.gold_selected_enemy_idx = g.gold_selected_enemy_idx

    # UI / cached fields
    ng.valid_moves = []
    ng.valid_removals = set()
    ng.valid_placements = set()

    # no undo history for AI
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

    target_key = k(target)

    if game.config.control_mode:
        if g1.gold_disc is not None and target_key == g1.gold_disc:
            return 100000
        if g1.silver_disc is not None and target_key == g1.silver_disc:
            return 50000

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

    if game.config.variant == "CONTROL":
        if root:
            endpoint_limit = 3
            removal_limit = 4
            placement_limit = min(top_k_placements, 12)
        else:
            endpoint_limit = 2
            removal_limit = 4
            placement_limit = min(top_k_placements, 12)
    elif game.config.variant == "MEGA":
        if root:
            endpoint_limit = 3
            removal_limit = 4
            placement_limit = min(top_k_placements, 6)
        else:
            endpoint_limit = 2
            removal_limit = 3
            placement_limit = min(top_k_placements, 5)
    else:
        if root:
            endpoint_limit = 2
            removal_limit = 4
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
            g1.current = player
            g1.pawns[player][pawn_i] = target
            g1.handle_special_landing(player, target)

            removals = list(g1.compute_valid_removals())
            removals.sort(key=lambda rem: removal_score(g1, player, rem), reverse=True)
            removals = removals[:removal_limit]

            for rem_key in removals:
                g2 = clone_game(g1)

                if rem_key not in g2.occupied:
                    continue

                g2.removable = rem_key
                g2.occupied.remove(rem_key)

                placements = list(g2.compute_valid_placements())
                if not placements:
                    continue

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
                    return (-2 * near_me) - (1 * near_opp)

                placements.sort(key=place_score, reverse=True)

                for place_key in placements[:placement_limit]:
                    turns.append((pawn_i, target, rem_key, place_key))

    print("generate_turns produced:", len(turns))

    return turns


def apply_turn(game, player, turn):
    """
    Apply a full turn to a cloned game using the game's real mode-aware rules.
    """
    pawn_i, target, rem_key, place_key = turn

    game.current = player
    game.pawns[player][pawn_i] = target
    game.handle_special_landing(player, target)

    winner = game.check_any_win()
    if winner is not None:
        game.winner = winner
        game.phase = "GAME_OVER"
        return

    removed_was_gold = (rem_key == game.gold_disc)
    removed_was_silver = (rem_key == game.silver_disc)

    if rem_key in game.occupied:
        game.occupied.remove(rem_key)

    if removed_was_gold:
        game.gold_disc = None
    if removed_was_silver:
        game.silver_disc = None

    game.occupied.add(place_key)

    if removed_was_gold:
        game.gold_disc = place_key
    if removed_was_silver:
        game.silver_disc = place_key

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

def find_immediate_win(game, ai_player):
    """
    Exhaustive one-pawn-move scan for immediate wins.
    This avoids pruning hiding a winning move.
    """
    for pawn_i, pawn_pos in enumerate(game.pawns[ai_player]):
        endpoints = game.pawn_moves_from(pawn_pos)

        for target in endpoints:
            g1 = clone_game(game)
            g1.current = ai_player
            g1.pawns[ai_player][pawn_i] = target
            g1.handle_special_landing(ai_player, target)

            # Check if the pawn move itself creates a win
            if g1.check_any_win() == ai_player:
                removals = list(g1.compute_valid_removals())

                for rem_key in removals:
                    g2 = clone_game(g1)

                    if rem_key not in g2.occupied:
                        continue

                    g2.removable = rem_key
                    g2.occupied.remove(rem_key)

                    placements = list(g2.compute_valid_placements())

                    for place_key in placements:
                        if place_key == rem_key:
                            continue

                        print("Immediate winning move found:", (pawn_i, target, rem_key, place_key))
                        return (pawn_i, target, rem_key, place_key)

    return None


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

def choose_ai_turn(game, ai_player, depth=2, top_k_placements=8):
    """Return best full-turn action for ai_player, or None if no moves."""
    TT.clear()

    winning_turn = find_immediate_win(game, ai_player)
    if winning_turn is not None:
        return winning_turn

    if game.config.variant == "CONTROL":
        return choose_ai_turn_control(game, ai_player)

    root_turns = generate_turns(
        game,
        ai_player,
        top_k_placements=top_k_placements,
        root=False
    )

    if not root_turns:
        return None

    best_turn = None
    for d in range(1, depth + 1):
        turn = choose_ai_turn_at_depth(game, ai_player, d, top_k_placements)
        if turn is not None:
            best_turn = turn

    return best_turn

def choose_ai_turn_control(game, ai_player):
    """
    Fast greedy chooser for Control mode.
    No minimax; just score a small set of candidate full turns.
    """
    turns = generate_turns(game, ai_player, top_k_placements=12, root=False)
    print("CONTROL candidate turns:", len(turns))

    if not turns:
        return None

    best_turn = None
    best_val = -math.inf

    for i, t in enumerate(turns):
        g2 = clone_game(game)
        apply_turn(g2, ai_player, t)

        # immediate win check
        if g2.check_any_win() == ai_player:
            return t

        val = evaluate(g2, ai_player)

        if val > best_val:
            best_val = val
            best_turn = t

    return best_turn