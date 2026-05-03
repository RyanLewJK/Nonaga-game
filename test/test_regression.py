from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.game_config import survival_config, control_config, classic_config
from src.nonaga.hexgrid import k


def test_survival_never_spawns_overlapping_pawns():
    for _ in range(100):
        game = NonagaGame(
            config=survival_config(),
            human_player="A",
            ai_player="B"
        )

        all_pawns = game.pawns["A"] + game.pawns["B"]

        assert len(all_pawns) == len(set(all_pawns))


def test_survival_always_has_correct_pawn_counts():
    for _ in range(100):
        game = NonagaGame(
            config=survival_config(),
            human_player="A",
            ai_player="B"
        )

        assert len(game.pawns["A"]) == 2
        assert len(game.pawns["B"]) == 3


def test_survival_does_not_spawn_gold_or_silver():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    assert game.config.control_mode is False
    assert game.gold_disc is None
    assert game.silver_disc is None


def test_classic_does_not_spawn_gold_or_silver():
    game = NonagaGame(config=classic_config())

    assert game.gold_disc is None
    assert game.silver_disc is None


def test_control_spawns_gold_and_silver_not_on_pawns():
    for _ in range(50):
        game = NonagaGame(config=control_config())

        pawn_cells = game.pawn_set()

        assert game.gold_disc not in pawn_cells
        assert game.silver_disc not in pawn_cells


def test_cancel_after_disc_removal_restores_disc():
    game = NonagaGame(config=classic_config())

    rem = next(iter(game.compute_valid_removals()))

    game.phase = Phase.PICK_REMOVE
    game.valid_removals = game.compute_valid_removals()
    game.click_disc(rem)

    assert game.phase == Phase.PICK_PLACE
    assert rem not in game.occupied

    game.cancel_selection()

    assert game.phase == Phase.PICK_REMOVE
    assert rem in game.occupied
    assert game.removable is None


def test_right_click_preview_marker_does_not_count_as_real_selection():
    game = NonagaGame(config=classic_config())

    # This represents the preview state used in nonaga.py.
    game.selected_idx = -1
    game.valid_moves = [(0, 0)]

    # Clicking a target should not move a real pawn when selected_idx is -1.
    before_pawns = {
        "A": list(game.pawns["A"]),
        "B": list(game.pawns["B"]),
    }

    game.click_disc(k((0, 0)))

    assert game.pawns == before_pawns