from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.game_config import classic_config
from src.nonaga.hexgrid import k, parse_key


def test_pawn_moves_are_generated():
    game = NonagaGame(config=classic_config())

    pawn = game.pawns["A"][0]
    moves = game.pawn_moves_from(pawn)

    assert isinstance(moves, list)
    assert len(moves) > 0


def test_pawn_cannot_move_onto_another_pawn():
    game = NonagaGame(config=classic_config())

    pawn_cells = game.pawn_set()

    for player in ["A", "B"]:
        for pawn in game.pawns[player]:
            moves = game.pawn_moves_from(pawn)

            for move in moves:
                assert k(move) not in pawn_cells


def test_valid_removals_do_not_include_pawn_cells():
    game = NonagaGame(config=classic_config())

    removals = game.compute_valid_removals()
    pawn_cells = game.pawn_set()

    assert len(removals) > 0

    for rem in removals:
        assert rem not in pawn_cells


def test_removable_discs_are_edge_discs():
    game = NonagaGame(config=classic_config())

    removals = game.compute_valid_removals()

    for rem in removals:
        assert game.is_edge_cell(rem)


def test_valid_placements_do_not_include_removed_cell():
    game = NonagaGame(config=classic_config())

    rem = next(iter(game.compute_valid_removals()))

    game.removable = rem
    game.occupied.remove(rem)

    placements = game.compute_valid_placements()

    assert rem not in placements


def test_valid_placements_touch_at_least_two_discs():
    game = NonagaGame(config=classic_config())

    rem = next(iter(game.compute_valid_removals()))

    game.removable = rem
    game.occupied.remove(rem)

    placements = game.compute_valid_placements()

    for place_key in placements:
        pos = parse_key(place_key)
        assert game.can_place_at(pos)


def test_clicking_pawn_selects_it():
    game = NonagaGame(config=classic_config())

    pawn = game.pawns["A"][0]
    pawn_key = k(pawn)

    game.click_disc(pawn_key)

    assert game.selected_idx == 0
    assert len(game.valid_moves) > 0


def test_cancel_selection_clears_selected_pawn():
    game = NonagaGame(config=classic_config())

    pawn = game.pawns["A"][0]
    pawn_key = k(pawn)

    game.click_disc(pawn_key)
    assert game.selected_idx == 0

    game.cancel_selection()

    assert game.selected_idx is None
    assert game.valid_moves == []


def test_pawn_move_changes_phase_to_pick_remove():
    game = NonagaGame(config=classic_config())

    pawn = game.pawns["A"][0]
    pawn_key = k(pawn)

    game.click_disc(pawn_key)
    target = game.valid_moves[0]

    game.click_disc(k(target))

    assert game.phase == Phase.PICK_REMOVE
    assert game.selected_idx is None
    assert len(game.valid_removals) > 0