from dataclasses import dataclass
from typing import Optional


@dataclass
class GameConfig:
    variant: str = "CLASSIC"

    # board
    board_radius: int = 2
    pawns_per_player: int = 3
    win_length: int = 3

    # timer
    turn_time_limit: Optional[int] = None  # None = default 5 mins

    # control mode
    control_mode: bool = False
    control_required: int = 0

    # survival mode
    survival_mode: bool = False
    survival_turns: Optional[int] = None


def classic_config() -> GameConfig:
    return GameConfig(
        variant="CLASSIC",
        board_radius=2,
        pawns_per_player=3,
        win_length=3
    )


def mega_config() -> GameConfig:
    return GameConfig(
        variant="MEGA",
        board_radius=3,
        pawns_per_player=4,
        win_length=4
    )


def control_config() -> GameConfig:
    return GameConfig(
        variant="CONTROL",
        board_radius=2,
        pawns_per_player=3,
        win_length=3,
        control_mode=True,
        control_required=3
    )


def survival_config() -> GameConfig:
    return GameConfig(
        variant="SURVIVAL",
        board_radius=2,
        pawns_per_player=3,
        win_length=3,
        survival_mode=True,
        survival_turns=15
    )