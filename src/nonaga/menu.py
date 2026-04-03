import pygame
from dataclasses import dataclass
from typing import Optional, Tuple

# -------- Menu results --------
@dataclass
class MenuChoice:
    mode: str                 # "LOCAL" or "SINGLE"
    side: str = "A"           # "A" (Red) or "B" (Blue)

# -------- Simple UI widgets --------
class Button:
    def __init__(self, rect: pygame.Rect, text: str):
        self.rect = rect
        self.text = text
        self.hover = False

    def handle(self, mouse_pos, mouse_down) -> bool:
        self.hover = self.rect.collidepoint(mouse_pos)
        return self.hover and mouse_down

    def draw(self, surf, font, colors):
        bg, bg_hover, border, txt = colors
        pygame.draw.rect(surf, bg_hover if self.hover else bg, self.rect, border_radius=14)
        pygame.draw.rect(surf, border, self.rect, width=2, border_radius=14)

        label = font.render(self.text, True, txt)
        surf.blit(label, label.get_rect(center=self.rect.center))


class ToggleGroup:
    """Row of options; click to select."""
    def __init__(self, label: str, options, selected_index=0):
        self.label = label
        self.options = options
        self.selected = selected_index

    def draw(self, surf, font, small_font, x, y, w, h, mouse_pos, mouse_down):
        title = small_font.render(self.label, True, (220, 220, 220))
        surf.blit(title, (x, y))

        # layout buttons across width
        pad = 10
        btn_w = (w - pad * (len(self.options) - 1)) // len(self.options)
        btn_h = h
        by = y + 24

        for i, opt in enumerate(self.options):
            bx = x + i * (btn_w + pad)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)

            is_sel = (i == self.selected)
            fill = (55, 55, 55) if not is_sel else (85, 75, 120)
            fill = (70, 70, 70) if hover and not is_sel else fill

            pygame.draw.rect(surf, fill, rect, border_radius=12)
            pygame.draw.rect(surf, (120, 120, 120), rect, width=2, border_radius=12)

            lab = font.render(opt, True, (245, 245, 245))
            surf.blit(lab, lab.get_rect(center=rect.center))

            if hover and mouse_down:
                self.selected = i

    def value(self):
        return self.options[self.selected]


# -------- Menu screens --------
class MenuUI:
    MAIN = "MAIN"
    SINGLE = "SINGLE"
    HELP = "HELP"

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w, self.h = screen.get_size()

        self.title_font = pygame.font.SysFont(None, 72)
        self.h2_font = pygame.font.SysFont(None, 32)
        self.font = pygame.font.SysFont(None, 28)
        self.small = pygame.font.SysFont(None, 22)

        self.state = MenuUI.MAIN
        self.choice = MenuChoice(mode="LOCAL")

        # theme
        self.bg = (15, 15, 15)
        self.panel = (22, 22, 22)
        self.panel_border = (55, 55, 55)
        self.btn_colors = ((40, 40, 40), (60, 60, 60), (120, 120, 120), (245, 245, 245))

        # main menu buttons (centered)
        bw, bh = 320, 54
        cx = self.w // 2 - bw // 2
        top = int(self.h * 0.42)
        gap = 14

        self.btn_play = Button(pygame.Rect(cx, top + 0*(bh+gap), bw, bh), "Play (2 Players)")
        self.btn_single = Button(pygame.Rect(cx, top + 1*(bh+gap), bw, bh), "Single Player")
        self.btn_help = Button(pygame.Rect(cx, top + 2*(bh+gap), bw, bh), "How to Play")
        self.btn_quit = Button(pygame.Rect(cx, top + 3*(bh+gap), bw, bh), "Quit")

        # single player controls
        self.side_group = ToggleGroup("Side", ["Red (A)", "Blue (B)"], 0)

        self.btn_start = Button(pygame.Rect(cx, int(self.h*0.75), bw, bh), "Start")
        self.btn_back = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")

        # help
        self.btn_back2 = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")

    def _panel(self, rect: pygame.Rect):
        pygame.draw.rect(self.screen, self.panel, rect, border_radius=18)
        pygame.draw.rect(self.screen, self.panel_border, rect, width=2, border_radius=18)

    def _draw_centered(self, text, font, y, color=(245, 245, 245)):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(self.w//2, y)))

    def draw_main(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("NONAGA", self.title_font, int(self.h * 0.18))
        self._draw_centered("Shift the board. Connect your 3 pawns.", self.h2_font, int(self.h * 0.26), (200, 200, 200))

        # panel behind buttons (auto-fit to all buttons)
        buttons = [self.btn_play, self.btn_single, self.btn_help, self.btn_quit]
        left   = min(b.rect.left for b in buttons)
        top    = min(b.rect.top for b in buttons)
        right  = max(b.rect.right for b in buttons)
        bottom = max(b.rect.bottom for b in buttons)

        panel_rect = pygame.Rect(left, top, right - left, bottom - top).inflate(80, 50)
        self._panel(panel_rect)


        if self.btn_play.handle(mouse_pos, mouse_down):
            return "PLAY_LOCAL"
        if self.btn_single.handle(mouse_pos, mouse_down):
            self.state = MenuUI.SINGLE
        if self.btn_help.handle(mouse_pos, mouse_down):
            self.state = MenuUI.HELP
        if self.btn_quit.handle(mouse_pos, mouse_down):
            return "QUIT"

        for b in [self.btn_play, self.btn_single, self.btn_help, self.btn_quit]:
            b.draw(self.screen, self.font, self.btn_colors)

        footer = "Tip: R = reset • Ctrl+Z = undo"
        self.screen.blit(self.small.render(footer, True, (170, 170, 170)),
                         (self.w//2 - 130, self.h - 32))
        return None

    def draw_single(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("Single Player", self.title_font, int(self.h * 0.16))
        self._draw_centered("Choose your side", self.h2_font, int(self.h * 0.24), (200, 200, 200))

        panel = pygame.Rect(self.w//2 - 260, int(self.h*0.30), 520, int(self.h*0.30))
        self._panel(panel)

        x = panel.x + 24
        y = panel.y + 22
        self.side_group.draw(self.screen, self.font, self.small, x, y, panel.w - 48, 46, mouse_pos, mouse_down)

        # update choice from toggle
        self.choice.mode = "SINGLE"
        self.choice.side = "A" if self.side_group.value().startswith("Red") else "B"

        if self.btn_start.handle(mouse_pos, mouse_down):
            return "START_SINGLE"
        if self.btn_back.handle(mouse_pos, mouse_down):
            self.state = MenuUI.MAIN

        self.btn_start.draw(self.screen, self.font, self.btn_colors)
        self.btn_back.draw(self.screen, self.font, self.btn_colors)
        return None

    def draw_help(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("How to Play", self.title_font, int(self.h * 0.16))
        panel = pygame.Rect(self.w//2 - 300, int(self.h*0.28), 600, int(self.h*0.52))
        self._panel(panel)

        lines = [
            "On your turn:",
            "  1) Move a pawn (it slides in a straight line until blocked).",
            "  2) Relocate a disc:",
            "     - remove an empty edge disc",
            "     - place it so it touches at least 2 discs",
            "",
            "Win by getting your 3 pawns into one connected cluster (neighbors).",
        ]

        tx = panel.x + 24
        ty = panel.y + 20
        for i, line in enumerate(lines):
            f = self.h2_font if i == 0 else self.small
            color = (230, 230, 230) if i == 0 else (200, 200, 200)
            surf = f.render(line, True, color)
            self.screen.blit(surf, (tx, ty))
            ty += 34 if i == 0 else 26

        if self.btn_back2.handle(mouse_pos, mouse_down):
            self.state = MenuUI.MAIN
        self.btn_back2.draw(self.screen, self.font, self.btn_colors)
        return None

    def run(self, clock: pygame.time.Clock) -> Optional[MenuChoice]:
        """Blocks until user chooses a mode or quits. Returns MenuChoice or None if quit."""
        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_down = False

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    # ESC always goes back, or quits from main
                    if self.state == MenuUI.MAIN:
                        return None
                    self.state = MenuUI.MAIN
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mouse_down = True

            self.screen.fill(self.bg)

            action = None
            if self.state == MenuUI.MAIN:
                action = self.draw_main(mouse_pos, mouse_down)
            elif self.state == MenuUI.SINGLE:
                action = self.draw_single(mouse_pos, mouse_down)
            elif self.state == MenuUI.HELP:
                action = self.draw_help(mouse_pos, mouse_down)

            pygame.display.flip()
            clock.tick(60)

            if action == "QUIT":
                return None
            if action == "PLAY_LOCAL":
                return MenuChoice(mode="LOCAL")
            if action == "START_SINGLE":
                return self.choice
