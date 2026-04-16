import pygame
from typing import Optional
from src.nonaga.hexgrid import axial_to_pixel, parse_key, Axial
from src.nonaga.game_state import Phase
from src.nonaga.constants import HEX_SIZE, DISC_R, ORIGIN


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

    def hit_test_menu_button(self, mx: float, my: float) -> bool:
        bx, by, bw, bh = 14, 200, 200, 40
        return bx <= mx <= bx + bw and by <= my <= by + bh

    def handle_event(self, ev: pygame.event.Event):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_r:
                self.game.reset()
            elif ev.key == pygame.K_ESCAPE:
                self.game.cancel_selection()

        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos

            if self.game.phase == Phase.GAME_OVER:
                if self.hit_test_menu_button(mx, my):
                    return "MENU"
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