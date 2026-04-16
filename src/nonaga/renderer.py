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

        self.pawn_img_A = pygame.image.load("assets/img/disc_A.png").convert_alpha()
        self.pawn_img_B = pygame.image.load("assets/img/disc_B.png").convert_alpha()
        self.cell_img = pygame.image.load("assets/img/cell.png").convert_alpha()

        self.cell_img = pygame.transform.smoothscale(
            self.cell_img, (int(DISC_R * 2.2), int(DISC_R * 2.2))
        )

        self.pawn_img_A = pygame.transform.smoothscale(
            self.pawn_img_A, (int(PAWN_R * 3.5), int(PAWN_R * 3.5))
        )
        self.pawn_img_B = pygame.transform.smoothscale(
            self.pawn_img_B, (int(PAWN_R * 3.5), int(PAWN_R * 3.5))
        )

    def player_label(self, player: str, single_player=False, human_player="A") -> str:
        if not single_player:
            return f"Player {player}"
        return "You" if player == human_player else "Opponent"

    def draw_text(self, msg: str, x: int, y: int, fnt, color=UI_TEXT):
        surf = fnt.render(msg, True, color)
        self.screen.blit(surf, (x, y))

    def draw(self, game, single_player=False, human_player="A"):
        self.screen.fill(BG)

        # board discs
        for cell in game.occupied:
            pos = parse_key(cell)
            x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)

            rect = self.cell_img.get_rect(center=(int(x), int(y)))
            self.screen.blit(self.cell_img, rect)

            if game.phase == Phase.PICK_REMOVE and cell in game.valid_removals:
                pygame.draw.circle(self.screen, REM_STROKE, (int(x), int(y)), DISC_R, 3)

            if game.blocked == cell:
                pygame.draw.circle(self.screen, BLOCKED_STROKE, (int(x), int(y)), DISC_R, 3)

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

                img = self.pawn_img_A if player == "A" else self.pawn_img_B
                rect = img.get_rect(center=(int(x), int(y)))
                self.screen.blit(img, rect)

                if ring:
                    pygame.draw.circle(self.screen, ring, (int(x), int(y)), PAWN_R + 6, 3)

        draw_pawns("A", A_COLOR)
        draw_pawns("B", B_COLOR)

        phase_text = {
            Phase.MOVE_PAWN: "Move a pawn (click pawn, then destination)",
            Phase.PICK_REMOVE: "Remove an empty edge disc (click highlighted disc)",
            Phase.PICK_PLACE: "Place disc (click a highlighted dot; must touch ≥2 discs)",
            Phase.GAME_OVER: "Game over",
        }[game.phase]

        current_label = self.player_label(game.current, single_player, human_player)
        a_label = self.player_label("A", single_player, human_player)
        b_label = self.player_label("B", single_player, human_player)

        self.draw_text("Nonaga", 14, 12, self.big)
        self.draw_text(f"Turn: {current_label}", 14, 44, self.font)
        self.draw_text(f"Phase: {phase_text}", 14, 66, self.font)
        self.draw_text(f"{a_label} Time: {game.format_time('A')}", 14, 88, self.font)
        self.draw_text(f"{b_label} Time: {game.format_time('B')}", 14, 110, self.font)

        if game.blocked:
            self.draw_text(f"Blocked disc this turn: {game.blocked}", 14, 132, self.font, UI_MUTED)

        self.draw_text("Keys: R = reset, Esc = cancel selection", 14, SCREEN_H - 28, self.font, UI_MUTED)

        if game.phase == Phase.GAME_OVER:
            winner = game.winner if game.winner is not None else game.current
            winner_label = self.player_label(winner, single_player, human_player)
            self.draw_text(f"{winner_label} WINS!", 14, 160, self.big, (255, 230, 150))

            bx, by, bw, bh = 14, 200, 200, 40
            pygame.draw.rect(self.screen, (80, 80, 80), (bx, by, bw, bh))
            pygame.draw.rect(self.screen, (200, 200, 200), (bx, by, bw, bh), 2)

            label = self.font.render("Back to Menu", True, (255, 255, 255))
            rect = label.get_rect(center=(bx + bw // 2, by + bh // 2))
            self.screen.blit(label, rect)