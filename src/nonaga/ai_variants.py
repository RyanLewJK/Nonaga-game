from src.nonaga.hexgrid import parse_key


def _opp(player: str) -> str:
    return "B" if player == "A" else "A"


def _hex_distance(a, b):
    aq, ar = a
    bq, br = b
    return (abs(aq - bq) + abs((aq + ar) - (bq + br)) + abs(ar - br)) // 2


def _pairwise_distance_sum(pawns):
    total = 0
    n = len(pawns)
    for i in range(n):
        for j in range(i + 1, n):
            total += _hex_distance(pawns[i], pawns[j])
    return total


def _adjacent_pair_count(pawns):
    count = 0
    n = len(pawns)
    for i in range(n):
        for j in range(i + 1, n):
            if _hex_distance(pawns[i], pawns[j]) == 1:
                count += 1
    return count


def _mobility(game, player):
    total = 0
    for pos in game.pawns[player]:
        total += len(game.pawn_moves_from(pos))
    return total


def _distance_to_cell_key(pawns, cell_key: str):
    pos = parse_key(cell_key)
    return min(_hex_distance(p, pos) for p in pawns)


def evaluate_classic(game, ai_player: str) -> float:
    opp = _opp(ai_player)

    my_cluster = _pairwise_distance_sum(game.pawns[ai_player])
    opp_cluster = _pairwise_distance_sum(game.pawns[opp])

    my_mob = _mobility(game, ai_player)
    opp_mob = _mobility(game, opp)

    my_adj = _adjacent_pair_count(game.pawns[ai_player])
    opp_adj = _adjacent_pair_count(game.pawns[opp])

    return (
        -12 * my_cluster
        + 8 * opp_cluster
        + 2 * (my_mob - opp_mob)
        + 40 * my_adj
        - 45 * opp_adj
    )


def evaluate_mega(game, ai_player: str) -> float:
    opp = _opp(ai_player)

    my_cluster = _pairwise_distance_sum(game.pawns[ai_player])
    opp_cluster = _pairwise_distance_sum(game.pawns[opp])

    my_mob = _mobility(game, ai_player)
    opp_mob = _mobility(game, opp)

    my_adj = _adjacent_pair_count(game.pawns[ai_player])
    opp_adj = _adjacent_pair_count(game.pawns[opp])

    # Mega board needs stronger emphasis on connectivity,
    # because distances are naturally larger.
    return (
        -16 * my_cluster
        + 10 * opp_cluster
        + 2 * (my_mob - opp_mob)
        + 55 * my_adj
        - 50 * opp_adj
    )


def evaluate_survival(game, ai_player: str) -> float:
    """
    Survival assumptions:
    - Human wins by surviving enough turns.
    - AI wants to stop that by increasing pressure.
    - Normal connection win is disabled in this mode.
    """
    human = game.human_player
    ai = game.ai_player

    # If this evaluator is called for the non-AI side by mistake,
    # still produce a coherent score from ai_player's perspective.
    opp = _opp(ai_player)

    ai_cluster = _pairwise_distance_sum(game.pawns[ai])
    human_mob = _mobility(game, human)
    ai_mob = _mobility(game, ai)

    # How close AI is to the human pawns
    pressure = 0
    for hp in game.pawns[human]:
        nearest_ai = min(_hex_distance(hp, ap) for ap in game.pawns[ai])
        pressure += nearest_ai

    # Fewer turns remaining for the human should be better for AI
    turns_left = 0
    if game.config.survival_turns is not None:
        turns_left = game.config.survival_turns - game.survival_turn_count

    # Lower pressure distance is better, lower human mobility is better
    # Lower turns_left means AI is actually in danger, so penalize that
    score = (
        -14 * ai_cluster
        - 7 * human_mob
        + 2 * ai_mob
        - 10 * pressure
        - 8 * turns_left
    )

    # Mild fallback structure term so the evaluator stays stable
    my_cluster = _pairwise_distance_sum(game.pawns[ai_player])
    opp_cluster = _pairwise_distance_sum(game.pawns[opp])
    score += -2 * my_cluster + 1 * opp_cluster

    return score


def evaluate_control(game, ai_player: str) -> float:
    opp = _opp(ai_player)

    score = evaluate_classic(game, ai_player)

    if game.gold_disc is not None:
        my_gold_dist = _distance_to_cell_key(game.pawns[ai_player], game.gold_disc)
        opp_gold_dist = _distance_to_cell_key(game.pawns[opp], game.gold_disc)

        score += -30 * my_gold_dist
        score += 18 * opp_gold_dist

    if game.silver_disc is not None:
        my_silver_dist = _distance_to_cell_key(game.pawns[ai_player], game.silver_disc)
        opp_silver_dist = _distance_to_cell_key(game.pawns[opp], game.silver_disc)

        score += -14 * my_silver_dist
        score += 8 * opp_silver_dist

    # Reward currently active power-up states
    if getattr(game, "gold_move_enemy_active", False) and game.current == ai_player:
        score += 120

    if getattr(game, "special_remove_any", False) and game.current == ai_player:
        score += 35

    return score


def evaluate_by_mode(game, ai_player: str) -> float:
    variant = game.config.variant

    if variant == "CLASSIC":
        return evaluate_classic(game, ai_player)
    if variant == "MEGA":
        return evaluate_mega(game, ai_player)
    if variant == "SURVIVAL":
        return evaluate_survival(game, ai_player)
    if variant == "CONTROL":
        return evaluate_control(game, ai_player)

    return evaluate_classic(game, ai_player)