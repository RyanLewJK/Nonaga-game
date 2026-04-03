import pygame
from typing import Tuple
from src.nonaga.hexgrid import axial_to_pixel, parse_key
from src.nonaga.game_state import Phase
from src.nonaga.constants import (
    BG, DISC_FILL, DISC_STROKE, REM_FILL, REM_STROKE, BLOCKED_STROKE,
    PLACE_FILL, PLACE_STROKE, MOVE_FILL, MOVE_STROKE,
    A_COLOR, B_COLOR, SELECT_RING,
    HEX_SIZE, DISC_R, PAWN_R, ORIGIN,
    UI_TEXT, UI_MUTED, SCREEN_H
)

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 22)
        self.big = pygame.font.SysFont(None, 28)

    def draw_text(self, msg: str, x: int, y: int, fnt, color=UI_TEXT):
        surf = fnt.render(msg, True, color)
        self.screen.blit(surf, (x, y))

    def draw(self, game):
        self.screen.fill(BG)

        # discs
        for cell in game.occupied:
            pos = parse_key(cell)
            x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)

            fill = DISC_FILL
            stroke = DISC_STROKE

            if game.phase == Phase.PICK_REMOVE and cell in game.valid_removals:
                fill = REM_FILL
                stroke = REM_STROKE
            if game.blocked == cell:
                stroke = BLOCKED_STROKE

            pygame.draw.circle(self.screen, fill, (int(x), int(y)), DISC_R)
            pygame.draw.circle(self.screen, stroke, (int(x), int(y)), DISC_R, 2)

        # placement dots
        if game.phase == Phase.PICK_PLACE:
            for cell in game.valid_placements:
                pos = parse_key(cell)
                x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
                pygame.draw.circle(self.screen, PLACE_FILL, (int(x), int(y)), 10)
                pygame.draw.circle(self.screen, PLACE_STROKE, (int(x), int(y)), 10, 2)

        # pawn move targets
        if game.phase == Phase.MOVE_PAWN and game.selected_idx is not None:
            for pos in game.valid_moves:
                x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
                pygame.draw.circle(self.screen, MOVE_FILL, (int(x), int(y)), 12)
                pygame.draw.circle(self.screen, MOVE_STROKE, (int(x), int(y)), 12, 2)

        # pawns
        def draw_pawns(player: str, color: Tuple[int, int, int]):
            for idx, pos in enumerate(game.pawns[player]):
                x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
                ring = None
                if player == game.current and idx == game.selected_idx and game.phase == Phase.MOVE_PAWN:
                    ring = SELECT_RING

                pygame.draw.circle(self.screen, color, (int(x), int(y)), PAWN_R)
                pygame.draw.circle(self.screen, (10, 10, 10), (int(x), int(y)), PAWN_R, 2)
                if ring:
                    pygame.draw.circle(self.screen, ring, (int(x), int(y)), PAWN_R + 3, 3)

                label = self.font.render(str(idx + 1), True, (0, 0, 0))
                rect = label.get_rect(center=(int(x), int(y)))
                self.screen.blit(label, rect)

        draw_pawns("A", A_COLOR)
        draw_pawns("B", B_COLOR)

        # UI text
        phase_text = {
            Phase.MOVE_PAWN: "Move a pawn (click pawn, then destination)",
            Phase.PICK_REMOVE: "Remove an empty edge disc (click highlighted disc)",
            Phase.PICK_PLACE: "Place disc (click a highlighted dot; must touch ≥2 discs)",
            Phase.GAME_OVER: "Game over",
        }[game.phase]

        self.draw_text("Nonaga (Pygame)", 14, 12, self.big)
        self.draw_text(f"Turn: Player {game.current}", 14, 44, self.font)
        self.draw_text(f"Phase: {phase_text}", 14, 66, self.font)
        if game.blocked:
            self.draw_text(f"Blocked disc this turn: {game.blocked}", 14, 88, self.font, UI_MUTED)
        self.draw_text("Keys: R = reset, Ctrl+Z = undo", 14, SCREEN_H - 28, self.font, UI_MUTED)

        if game.phase == Phase.GAME_OVER:
            self.draw_text(f"Player {game.current} WINS!", 14, 110, self.big, (255, 230, 150))
