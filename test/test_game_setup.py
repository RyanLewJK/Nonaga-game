from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.game_config import (
    classic_config,
    mega_config,
    control_config,
    survival_config,
)


def test_classic_initial_setup():
    game = NonagaGame(config=classic_config())

    assert game.config.variant == "CLASSIC"
    assert len(game.occupied) == 19
    assert len(game.pawns["A"]) == 3
    assert len(game.pawns["B"]) == 3
    assert game.current == "A"
    assert game.phase == Phase.MOVE_PAWN
    assert game.winner is None


def test_mega_initial_setup():
    game = NonagaGame(config=mega_config())

    assert game.config.variant == "MEGA"
    assert len(game.occupied) == 37
    assert len(game.pawns["A"]) == 4
    assert len(game.pawns["B"]) == 4
    assert game.phase == Phase.MOVE_PAWN


def test_control_initial_setup():
    game = NonagaGame(config=control_config())

    assert game.config.variant == "CONTROL"
    assert game.config.control_mode is True
    assert game.gold_disc is not None
    assert game.silver_disc is not None
    assert game.gold_disc != game.silver_disc


def test_survival_initial_setup():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    assert game.config.variant == "SURVIVAL"
    assert game.config.survival_mode is True
    assert game.human_player == "A"
    assert game.ai_player == "B"
    assert len(game.pawns["A"]) == 2
    assert len(game.pawns["B"]) == 3
    assert game.survival_turn_count == 0