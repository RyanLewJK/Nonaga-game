from src.nonaga.game_state import NonagaGame
from src.nonaga.game_config import classic_config, mega_config, survival_config


def test_classic_connected_pawns_win():
    game = NonagaGame(config=classic_config())

    game.pawns["A"] = [(0, 0), (1, 0), (2, 0)]

    assert game.is_win("A") is True
    assert game.check_any_win() == "A"


def test_classic_disconnected_pawns_do_not_win():
    game = NonagaGame(config=classic_config())

    game.pawns["A"] = [(2, 0), (0, -2), (-2, 2)]

    assert game.is_win("A") is False


def test_mega_requires_all_four_pawns_connected():
    game = NonagaGame(config=mega_config())

    game.pawns["A"] = [(0, 0), (1, 0), (2, 0), (3, 0)]

    assert game.is_win("A") is True
    assert game.check_any_win() == "A"


def test_survival_human_wins_after_turn_limit():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    game.survival_turn_count = game.config.survival_turns

    assert game.check_survival_win() == "A"


def test_survival_ai_wins_if_ai_pawns_connected():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    game.pawns["B"] = [(0, 0), (1, 0), (2, 0)]

    assert game.check_any_win() == "B"