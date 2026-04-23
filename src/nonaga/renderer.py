import pygame
from typing import Tuple
from src.nonaga.hexgrid import axial_to_pixel, parse_key
from src.nonaga.game_state import Phase
from src.nonaga.constants import (
    BG, DISC_FILL, DISC_STROKE, REM_FILL, REM_STROKE, BLOCKED_STROKE,
    PLACE_FILL, PLACE_STROKE, MOVE_FILL, MOVE_STROKE,
    A_COLOR, B_COLOR, SCREEN_W, SELECT_RING,
    HEX_SIZE, DISC_R, PAWN_R, ORIGIN,
    UI_TEXT, UI_MUTED, SCREEN_H
)

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 22)
        self.big = pygame.font.SysFont(None, 28)

        self.pawn_img_A = pygame.image.load("assets/img/disc_A_3.png").convert_alpha()
        self.pawn_img_B = pygame.image.load("assets/img/disc_B_3.png").convert_alpha()
        self.cell_img = pygame.image.load("assets/img/cell.png").convert_alpha()

        self.cell_img = pygame.transform.smoothscale(
            self.cell_img, (int(DISC_R * 1.9), int(DISC_R * 1.9))
        )

        self.pawn_img_A = pygame.transform.smoothscale(
            self.pawn_img_A, (int(PAWN_R * 3.5), int(PAWN_R * 3.5))
        )
        self.pawn_img_B = pygame.transform.smoothscale(
            self.pawn_img_B, (int(PAWN_R * 3.5), int(PAWN_R * 3.5))
        )

        self.gold_disc_img = pygame.image.load("assets/img/gold_control_disc.png").convert_alpha()
        self.silver_disc_img = pygame.image.load("assets/img/silver_control_disc.png").convert_alpha()

        self.gold_disc_img = pygame.transform.smoothscale(
            self.gold_disc_img, (int(DISC_R * 1.9), int(DISC_R * 1.9))
        )
        self.silver_disc_img = pygame.transform.smoothscale(
            self.silver_disc_img, (int(DISC_R * 1.9), int(DISC_R * 1.9))
        )

        self.turn_red = pygame.image.load("assets/img/red_turn.png").convert_alpha()
        self.turn_blue = pygame.image.load("assets/img/blue_turn.png").convert_alpha()

        self.turn_red = pygame.transform.smoothscale(self.turn_red, (120, 80))
        self.turn_blue = pygame.transform.smoothscale(self.turn_blue, (120, 80))

        self.win_red_img = pygame.image.load("assets/img/red_win.png").convert_alpha()
        self.win_blue_img = pygame.image.load("assets/img/blue_win.png").convert_alpha()
        self.you_win_img = pygame.image.load("assets/img/you_win.png").convert_alpha()
        self.you_lose_img = pygame.image.load("assets/img/you_lose.png").convert_alpha()

        self.win_red_img = pygame.transform.smoothscale(self.win_red_img, (300, 100))
        self.win_blue_img = pygame.transform.smoothscale(self.win_blue_img, (300, 100))

        self.you_win_img = pygame.transform.smoothscale(self.you_win_img, (300, 100))
        self.you_lose_img = pygame.transform.smoothscale(self.you_lose_img, (300, 100))

        self.btn_menu_img = pygame.image.load("assets/img/back_to_menu.png").convert_alpha()
        self.btn_menu_hover_img = pygame.image.load("assets/img/back_to_menu_hover.png").convert_alpha()
        self.btn_restart_img = pygame.image.load("assets/img/btn_restart.png").convert_alpha()
        self.btn_restart_hover_img = pygame.image.load("assets/img/btn_restart_hover.png").convert_alpha()

        self.btn_menu_img = pygame.transform.smoothscale(self.btn_menu_img, (140, 50))
        self.btn_restart_img = pygame.transform.smoothscale(self.btn_restart_img, (140, 50))
        self.btn_menu_hover_img = pygame.transform.smoothscale(self.btn_menu_hover_img, (140, 50))
        self.btn_restart_hover_img = pygame.transform.smoothscale(self.btn_restart_hover_img, (140, 50))

    def player_label(self, player: str, single_player=False, human_player="A") -> str:
        if not single_player:
            return f"Player {player}"
        return "You" if player == human_player else "Opponent"

    def draw_text(self, msg: str, x: int, y: int, fnt, color=UI_TEXT):
        surf = fnt.render(msg, True, color)
        self.screen.blit(surf, (x, y))

    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 320, 220
        panel_x = (SCREEN_W - panel_w) // 2
        panel_y = (SCREEN_H - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, (24, 24, 24), panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, (180, 180, 180), panel_rect, 2, border_radius=20)

        title = self.big.render("Paused", True, (245, 245, 245))
        title_rect = title.get_rect(center=(panel_rect.centerx, panel_rect.y + 32))
        self.screen.blit(title, title_rect)

        btn_w, btn_h = 180, 42
        gap = 14
        start_x = panel_x + (panel_w - btn_w) // 2
        start_y = panel_y + 70

        mx, my = pygame.mouse.get_pos()

        buttons = [
            ("Resume", pygame.Rect(start_x, start_y, btn_w, btn_h)),
            ("Settings", pygame.Rect(start_x, start_y + btn_h + gap, btn_w, btn_h)),
            ("Main Menu", pygame.Rect(start_x, start_y + 2 * (btn_h + gap), btn_w, btn_h)),
        ]

        for text, rect in buttons:
            hover = rect.collidepoint(mx, my)
            fill = (90, 90, 90) if hover else (60, 60, 60)

            pygame.draw.rect(self.screen, fill, rect, border_radius=12)
            pygame.draw.rect(self.screen, (220, 220, 220), rect, 2, border_radius=12)

            label = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=rect.center))

    def draw(self, game, single_player=False, human_player="A"):
        self.screen.fill(BG)

        if game.phase != Phase.GAME_OVER:
            turn_img = self.turn_red if game.current == "A" else self.turn_blue
            turn_rect = turn_img.get_rect(topright=(self.screen.get_width() - 20, 20))
            self.screen.blit(turn_img, turn_rect)

        # board discs
        for cell in game.occupied:
            pos = parse_key(cell)
            x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)

            rect = self.cell_img.get_rect(center=(int(x), int(y)))
            self.screen.blit(self.cell_img, rect)

            if game.gold_disc == cell:
                gold_rect = self.gold_disc_img.get_rect(center=(int(x), int(y)))
                self.screen.blit(self.gold_disc_img, gold_rect)

            if game.silver_disc == cell:
                silver_rect = self.silver_disc_img.get_rect(center=(int(x), int(y)))
                self.screen.blit(self.silver_disc_img, silver_rect)

            if game.phase == Phase.PICK_REMOVE and cell in game.valid_removals:
                pygame.draw.circle(self.screen, REM_STROKE, (int(x), int(y)), DISC_R, 3)

            info_y = 130

            if game.config.survival_mode and game.config.survival_turns is not None:
                self.draw_text(
                    f"Survive: {game.survival_turn_count}/{game.config.survival_turns}",
                    14,
                    info_y,
                    self.font,
                    UI_MUTED
                )
                info_y += 24

            if game.config.control_mode:
                gold_status = "READY" if game.gold_disc else f"Respawn {game.gold_respawn_counter}"
                silver_status = "READY" if game.silver_disc else f"Respawn {game.silver_respawn_counter}"

                self.draw_text(f"Gold: {gold_status}", 14, info_y, self.font, (230, 200, 90))
                info_y += 24
                self.draw_text(f"Silver: {silver_status}", 14, info_y, self.font, (200, 200, 220))
                info_y += 24


            if game.blocked:
                self.draw_text(f"Blocked: {game.blocked}", 14, info_y, self.font, UI_MUTED)

        # placement dots
        if game.phase == Phase.PICK_PLACE:
            for cell in game.valid_placements:
                pos = parse_key(cell)
                x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
                pygame.draw.circle(self.screen, PLACE_FILL, (int(x), int(y)), 10)
                pygame.draw.circle(self.screen, PLACE_STROKE, (int(x), int(y)), 10, 2)

        if game.phase == Phase.MOVE_PAWN and game.selected_idx is not None:
            for pos in game.valid_moves:
                x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
                pygame.draw.circle(self.screen, MOVE_FILL, (int(x), int(y)), 12)
                pygame.draw.circle(self.screen, MOVE_STROKE, (int(x), int(y)), 12, 2)

        if game.phase == "GOLD_MOVE_ENEMY" and game.gold_selected_enemy_idx is not None:
            for pos in game.gold_valid_enemy_moves:
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
            Phase.MOVE_PAWN: "Move a pawn",
            Phase.PICK_REMOVE: "Remove a disc" if game.special_remove_any else "Remove an edge disc",
            Phase.PICK_PLACE: "Place the disc",
            "GOLD_MOVE_ENEMY": "Move an enemy pawn",
            Phase.GAME_OVER: "Game over",
        }[game.phase]

        # Top-left info block
        self.draw_text(f"Phase: {phase_text}", 14, 20, self.big, (245, 245, 245))
        self.draw_text(f"Mode: {game.config.variant}", 14, 48, self.font, UI_MUTED)
        self.draw_text("Red Time", 14, 58, self.font, (230, 70, 70))
        self.draw_text(game.format_time("A"), 140, 58, self.font, UI_TEXT)
        self.draw_text("Blue Time", 14, 84, self.font, (70, 140, 255))
        self.draw_text(game.format_time("B"), 140, 84, self.font, UI_TEXT)

        if game.blocked:
            self.draw_text(f"Blocked: {game.blocked}", 14, 110, self.font, UI_MUTED)

        self.draw_text("R: Restart   X: Cancel   Esc: Menu", 14, SCREEN_H - 28, self.font, UI_MUTED)

        if game.phase == Phase.GAME_OVER:

            # dark overlay
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            # centered popup panel
            panel_w, panel_h = 360, 200
            panel_x = (SCREEN_W - panel_w) // 2
            panel_y = (SCREEN_H - panel_h) // 2
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

            pygame.draw.rect(self.screen, (24, 24, 24), panel_rect, border_radius=20)
            pygame.draw.rect(self.screen, (180, 180, 180), panel_rect, 2, border_radius=20)

            # winner image
            winner = game.winner if game.winner is not None else game.current
            if single_player:
                if winner == human_player:
                    win_img = self.you_win_img
                else:
                    win_img = self.you_lose_img
            else:
                win_img = self.win_red_img if winner == "A" else self.win_blue_img
            win_rect = win_img.get_rect(center=(panel_rect.centerx, panel_rect.centery - 30))
            self.screen.blit(win_img, win_rect)

            # two buttons side by side
            btn_w, btn_h = 150, 50
            gap = 20
            total_w = btn_w * 2 + gap
            start_x = panel_rect.centerx - total_w // 2
            btn_y = panel_rect.bottom - 75

            menu_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
            restart_rect = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

            mx, my = pygame.mouse.get_pos()

            menu_img = self.btn_menu_hover_img if menu_rect.collidepoint(mx, my) else self.btn_menu_img
            restart_img = self.btn_restart_hover_img if restart_rect.collidepoint(mx, my) else self.btn_restart_img

            self.screen.blit(menu_img, menu_rect)
            self.screen.blit(restart_img, restart_rect)