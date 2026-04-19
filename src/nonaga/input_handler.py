import pygame
from typing import Optional
from src.nonaga.hexgrid import axial_to_pixel, parse_key, Axial
from src.nonaga.game_state import Phase
from src.nonaga.constants import HEX_SIZE, DISC_R, ORIGIN, SCREEN_W, SCREEN_H


class InputHandler:
    def __init__(self, game):
        self.game = game

    def hit_test_disc(self, mx: float, my: float) -> Optional[str]:
        best = None
        best_d2 = 10**18
        for cell in self.game.occupied:
            pos = parse_key(cell)
            x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
            dx, dy = mx - x, my - y
            d2 = dx * dx + dy * dy
            if d2 <= DISC_R * DISC_R and d2 < best_d2:
                best_d2 = d2
                best = cell
        return best

    def hit_test_place(self, mx: float, my: float) -> Optional[Axial]:
        best = None
        best_d2 = 10**18
        for cell in self.game.valid_placements:
            pos = parse_key(cell)
            x, y = axial_to_pixel(pos, HEX_SIZE, ORIGIN)
            dx, dy = mx - x, my - y
            d2 = dx * dx + dy * dy
            if d2 <= 14 * 14 and d2 < best_d2:
                best_d2 = d2
                best = pos
        return best

    def hit_test_game_over_buttons(self, mx: float, my: float):
        panel_w, panel_h = 360, 200
        panel_x = (SCREEN_W - panel_w) // 2
        panel_y = (SCREEN_H - panel_h) // 2

        btn_w, btn_h = 140, 50
        gap = 20
        total_w = btn_w * 2 + gap
        start_x = panel_x + panel_w // 2 - total_w // 2
        btn_y = panel_y + panel_h - 75

        menu_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        restart_rect = pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h)

        if menu_rect.collidepoint(mx, my):
            return "MENU"
        if restart_rect.collidepoint(mx, my):
            return "RESTART"
        return None

    def hit_test_pause_menu_buttons(self, mx: float, my: float):
        panel_w, panel_h = 320, 220
        panel_x = (SCREEN_W - panel_w) // 2
        panel_y = (SCREEN_H - panel_h) // 2

        btn_w, btn_h = 180, 42
        gap = 14
        start_x = panel_x + (panel_w - btn_w) // 2
        start_y = panel_y + 70

        resume_rect = pygame.Rect(start_x, start_y, btn_w, btn_h)
        settings_rect = pygame.Rect(start_x, start_y + btn_h + gap, btn_w, btn_h)
        menu_rect = pygame.Rect(start_x, start_y + 2 * (btn_h + gap), btn_w, btn_h)

        if resume_rect.collidepoint(mx, my):
            return "RESUME"
        if settings_rect.collidepoint(mx, my):
            return "SETTINGS"
        if menu_rect.collidepoint(mx, my):
            return "MENU"

        return None

    def handle_event(self, ev: pygame.event.Event):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_r:
                self.game.reset()

        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos

            if self.game.phase == Phase.GAME_OVER:
                action = self.hit_test_game_over_buttons(mx, my)
                if action == "MENU":
                    return "MENU"
                if action == "RESTART":
                    return "RESTART"
                return None

            if self.game.phase == Phase.PICK_PLACE:
                p = self.hit_test_place(mx, my)
                if p is not None:
                    self.game.click_place(p)
            else:
                cell = self.hit_test_disc(mx, my)
                if cell is not None:
                    self.game.click_disc(cell)

        return None