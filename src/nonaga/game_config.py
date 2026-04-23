from dataclasses import dataclass
from typing import Optional


@dataclass
class GameConfig:
    variant: str = "CLASSIC"

    # -------- Board / pieces --------
    board_radius: int = 2
    pawns_a: int = 3
    pawns_b: int = 3
    allow_normal_connection_win: bool = True

    # -------- Timer --------
    # None means use the normal default in the game (currently 5 minutes)
    turn_time_limit: Optional[int] = None

    # -------- Survival mode --------
    survival_mode: bool = False
    survival_turns: Optional[int] = None

    # -------- Control mode / special discs --------
    control_mode: bool = False
    gold_enabled: bool = False
    silver_enabled: bool = False
    respawn_delay_turns: int = 2

    # -------- AI tuning --------
    ai_depth: int = 2
    ai_top_k: int = 6


def classic_config() -> GameConfig:
    return GameConfig(
        variant="CLASSIC",
        board_radius=2,
        pawns_a=3,
        pawns_b=3,
        allow_normal_connection_win=True,
        ai_depth=2,
        ai_top_k=8
    )


def mega_config() -> GameConfig:
    return GameConfig(
        variant="MEGA",
        board_radius=3,
        pawns_a=4,
        pawns_b=4,
        allow_normal_connection_win=True,
        ai_depth=2,
        ai_top_k=2,
        turn_time_limit = 420
    )


def survival_config() -> GameConfig:
    return GameConfig(
        variant="SURVIVAL",
        board_radius=2,
        pawns_a=2,
        pawns_b=3,
        allow_normal_connection_win=False,
        survival_mode=True,
        survival_turns=12,
        ai_depth=2,
        ai_top_k=6
    )


def control_config() -> GameConfig:
    return GameConfig(
        variant="CONTROL",
        board_radius=2,
        pawns_a=3,
        pawns_b=3,
        allow_normal_connection_win=True,
        control_mode=True,
        gold_enabled=True,
        silver_enabled=True,
        respawn_delay_turns=2,
        ai_depth=2,
        ai_top_k=6
    )