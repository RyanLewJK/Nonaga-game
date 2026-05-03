from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.game_config import control_config, survival_config
from src.nonaga.hexgrid import k


def test_gold_powerup_activates_on_landing():
    game = NonagaGame(config=control_config())

    game.gold_disc = k((0, 0))
    game.gold_respawn_counter = 0
    game.gold_move_enemy_active = False

    game.handle_special_landing("A", (0, 0))

    assert game.gold_disc is None
    assert game.gold_move_enemy_active is True
    assert game.gold_respawn_counter == game.config.respawn_delay_turns


def test_silver_powerup_activates_on_landing():
    game = NonagaGame(config=control_config())

    game.silver_disc = k((0, 0))
    game.silver_respawn_counter = 0
    game.special_remove_any = False

    game.handle_special_landing("A", (0, 0))

    assert game.silver_disc is None
    assert game.special_remove_any is True
    assert game.silver_respawn_counter == game.config.respawn_delay_turns


def test_control_powerups_do_not_activate_outside_control_mode():
    game = NonagaGame(config=survival_config())

    game.gold_disc = k((0, 0))
    game.silver_disc = k((1, 0))

    game.handle_special_landing("A", (0, 0))

    assert game.gold_disc == k((0, 0))
    assert game.gold_move_enemy_active is False


def test_special_remove_any_allows_non_edge_disc_removal():
    game = NonagaGame(config=control_config())

    game.special_remove_any = True
    removals = game.compute_valid_removals()
    pawn_cells = game.pawn_set()

    for cell in removals:
        assert cell not in pawn_cells

    assert len(removals) > 0


def test_survival_turn_counter_increases_after_human_turn():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    assert game.survival_turn_count == 0
    assert game.current == "A"

    game.finish_turn()

    assert game.survival_turn_count == 1
    assert game.current == "B"


def test_survival_turn_counter_does_not_increase_after_ai_turn():
    game = NonagaGame(
        config=survival_config(),
        human_player="A",
        ai_player="B"
    )

    game.current = "B"
    game.survival_turn_count = 0

    game.finish_turn()

    assert game.survival_turn_count == 0
    assert game.current == "A"