from src.nonaga.game_state import NonagaGame
from src.nonaga.game_config import (
    classic_config,
    mega_config,
    control_config,
    survival_config,
)
from src.nonaga.ai_new import (
    choose_ai_turn,
    generate_turns,
    apply_turn,
    clone_game,
)


def test_ai_generates_turns_classic():
    game = NonagaGame(config=classic_config())

    turns = generate_turns(game, "B", top_k_placements=4)

    assert isinstance(turns, list)
    assert len(turns) > 0

    for turn in turns:
        assert len(turn) == 4


def test_ai_choose_turn_returns_valid_tuple_classic():
    game = NonagaGame(config=classic_config())
    game.current = "B"

    turn = choose_ai_turn(
        clone_game(game),
        "B",
        depth=1,
        top_k_placements=4
    )

    assert turn is not None
    assert len(turn) == 4


def test_ai_returns_move_for_all_modes():
    configs = [
        classic_config(),
        mega_config(),
        control_config(),
        survival_config(),
    ]

    for config in configs:
        game = NonagaGame(
            config=config,
            human_player="A",
            ai_player="B"
        )
        game.current = "B"

        turn = choose_ai_turn(
            clone_game(game),
            "B",
            depth=1,
            top_k_placements=4
        )

        assert turn is not None
        assert len(turn) == 4


def test_apply_ai_turn_does_not_crash():
    game = NonagaGame(config=classic_config())
    game.current = "B"

    turns = generate_turns(game, "B", top_k_placements=4)
    turn = turns[0]

    g2 = clone_game(game)
    apply_turn(g2, "B", turn)

    assert g2 is not None
    assert len(g2.pawns["A"]) == 3
    assert len(g2.pawns["B"]) == 3
    assert len(g2.occupied) > 0


def test_clone_game_does_not_copy_history():
    game = NonagaGame(config=classic_config())

    game.snapshot()
    assert len(game.history) > 0

    cloned = clone_game(game)

    assert cloned is not game
    assert cloned.pawns == game.pawns
    assert cloned.occupied == game.occupied
    assert cloned.history == []