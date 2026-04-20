import pygame
from dataclasses import dataclass
from typing import Optional

from src.nonaga.game_config import (
    GameConfig,
    classic_config,
    mega_config,
    control_config,
    survival_config
)


# -------- Menu results --------
@dataclass
class MenuChoice:
    mode: str                  # "LOCAL" or "SINGLE"
    side: str = "A"            # "A" (Red) or "B" (Blue)
    variant: str = "CLASSIC"   # "CLASSIC", "MEGA", "CONTROL", "SURVIVAL"
    config: Optional[GameConfig] = None


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


class ImageButton:
    def __init__(self, rect: pygame.Rect, img_path: str, hover_img_path: str):
        self.rect = rect
        self.hover = False

        self.img = pygame.image.load(img_path).convert_alpha()
        self.hover_img = pygame.image.load(hover_img_path).convert_alpha()

        self.img = pygame.transform.smoothscale(self.img, (rect.w, rect.h))
        self.hover_img = pygame.transform.smoothscale(self.hover_img, (rect.w, rect.h))

    def handle(self, mouse_pos, mouse_down) -> bool:
        self.hover = self.rect.collidepoint(mouse_pos)
        return self.hover and mouse_down

    def draw(self, surf):
        surf.blit(self.hover_img if self.hover else self.img, self.rect)


class ToggleGroup:
    def __init__(self, label: str, options, selected_index=0):
        self.label = label
        self.options = options
        self.selected = selected_index

    def draw(self, surf, font, small_font, x, y, w, h, mouse_pos, mouse_down):
        title = small_font.render(self.label, True, (220, 220, 220))
        surf.blit(title, (x, y))

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


class MenuCard:
    def __init__(self, rect: pygame.Rect, title: str, description: list[str], image=None):
        self.rect = rect
        self.title = title
        self.description = description
        self.image = image
        self.hover = False

    def handle(self, mouse_pos, mouse_down) -> bool:
        self.hover = self.rect.collidepoint(mouse_pos)
        return self.hover and mouse_down

    def draw(self, surf, title_font, text_font):
        scale = 1.06 if self.hover else 1.0
        title_color = (255, 255, 255) if self.hover else (235, 235, 235)
        text_color = (245, 245, 245) if self.hover else (200, 200, 200)

        center_x = self.rect.centerx
        base_y = self.rect.y

        title_surf = title_font.render(self.title, True, title_color)
        if self.hover:
            title_surf = pygame.transform.smoothscale(
                title_surf,
                (int(title_surf.get_width() * scale), int(title_surf.get_height() * scale))
            )
        surf.blit(title_surf, title_surf.get_rect(midtop=(center_x, base_y + 10)))

        if self.image:
            img = self.image
            if self.hover:
                img = pygame.transform.smoothscale(
                    self.image,
                    (int(self.image.get_width() * scale), int(self.image.get_height() * scale))
                )
            img_rect = img.get_rect(center=(center_x, base_y + 120))
            surf.blit(img, img_rect)

        start_y = base_y + 210
        for i, line in enumerate(self.description):
            line_surf = text_font.render(line, True, text_color)
            if self.hover:
                line_surf = pygame.transform.smoothscale(
                    line_surf,
                    (int(line_surf.get_width() * 1.03), int(line_surf.get_height() * 1.03))
                )
            surf.blit(line_surf, line_surf.get_rect(center=(center_x, start_y + i * 34)))


# -------- Menu screens --------
class MenuUI:
    MAIN = "MAIN"
    PLAY = "PLAY"
    CLASSIC = "CLASSIC"
    MODES = "MODES"
    SINGLE = "SINGLE"
    HELP = "HELP"
    SETTINGS = "SETTINGS"

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w, self.h = screen.get_size()

        self.title_font = pygame.font.SysFont(None, 72)
        self.h2_font = pygame.font.SysFont(None, 32)
        self.font = pygame.font.SysFont(None, 28)
        self.small = pygame.font.SysFont(None, 22)

        self.state = MenuUI.MAIN
        self.choice = MenuChoice(mode="LOCAL")

        self.logo = pygame.image.load("assets/img/logo_2.png").convert_alpha()
        self.logo = pygame.transform.smoothscale(self.logo, (300, 150))

        self.card_image = pygame.image.load("assets/img/logo_2.png").convert_alpha()
        self.card_image = pygame.transform.smoothscale(self.card_image, (170, 120))

        self.bg = (15, 15, 15)
        self.panel = (22, 22, 22)
        self.panel_border = (55, 55, 55)
        self.btn_colors = ((40, 40, 40), (60, 60, 60), (120, 120, 120), (245, 245, 245))

        bw, bh = 280, 65
        cx = self.w // 2 - bw // 2
        top = int(self.h * 0.42)
        gap = 14

        self.btn_play = ImageButton(
            pygame.Rect(cx, top + 0*(bh+gap), bw, bh),
            "assets/img/play_btn.png",
            "assets/img/play_btn_hover.png"
        )

        self.btn_help = ImageButton(
            pygame.Rect(cx, top + 1*(bh+gap), bw, bh),
            "assets/img/help_btn.png",
            "assets/img/help_btn_hover.png"
        )

        self.btn_settings = ImageButton(
            pygame.Rect(cx, top + 2*(bh+gap), bw, bh),
            "assets/img/settings_btn.png",
            "assets/img/settings_btn_hover.png"
        )

        self.btn_exit = ImageButton(
            pygame.Rect(cx, top + 3*(bh+gap), bw, bh),
            "assets/img/exit_btn.png",
            "assets/img/exit_btn_hover.png"
        )

        self.btn_back_play = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")
        self.btn_back_classic = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")
        self.btn_back_modes = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")

        card_w, card_h = 260, 300
        left_x = 80
        right_x = self.w - 80 - card_w
        card_y = 140

        self.card_classic = MenuCard(
            pygame.Rect(left_x, card_y, card_w, card_h),
            "CLASSIC",
            ["Standard Nonaga", "Play the original rules"],
            self.card_image
        )

        self.card_modes = MenuCard(
            pygame.Rect(right_x, card_y, card_w, card_h),
            "MODES",
            ["Special variants", "New ways to play"],
            self.card_image
        )

        self.card_one_player = MenuCard(
            pygame.Rect(left_x, card_y, card_w, card_h),
            "1 PLAYER",
            ["Play against AI"],
            self.card_image
        )

        self.card_two_player = MenuCard(
            pygame.Rect(right_x, card_y, card_w, card_h),
            "2 PLAYER",
            ["Play locally with a friend"],
            self.card_image
        )

        small_w, small_h = 220, 280
        gap3 = 50
        total_w = 3 * small_w + 2 * gap3
        start_x = (self.w - total_w) // 2
        modes_y = 150

        self.card_control = MenuCard(
            pygame.Rect(start_x, modes_y, small_w, small_h),
            "CONTROL",
            ["Capture key tiles", "Win by positioning"],
            self.card_image
        )

        self.card_mega = MenuCard(
            pygame.Rect(start_x + small_w + gap3, modes_y, small_w, small_h),
            "MEGA BOARD",
            ["Larger board", "Connect all 4"],
            self.card_image
        )

        self.card_survival = MenuCard(
            pygame.Rect(start_x + 2 * (small_w + gap3), modes_y, small_w, small_h),
            "SURVIVAL",
            ["Hold out against AI", "Survive for 15 turns"],
            self.card_image
        )

        self.side_group = ToggleGroup("Side", ["Red (A)", "Blue (B)"], 0)
        self.btn_start = Button(pygame.Rect(cx, int(self.h*0.75), bw, bh), "Start")
        self.btn_back = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")

        self.btn_back2 = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")
        self.btn_back3 = Button(pygame.Rect(24, self.h - 70, 140, 46), "Back")

    def _panel(self, rect: pygame.Rect):
        pygame.draw.rect(self.screen, self.panel, rect, border_radius=18)
        pygame.draw.rect(self.screen, self.panel_border, rect, width=2, border_radius=18)

    def _draw_centered(self, text, font, y, color=(245, 245, 245)):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(self.w//2, y)))

    def draw_main(self, mouse_pos, mouse_down) -> Optional[str]:
        logo_rect = self.logo.get_rect(center=(self.w // 2, int(self.h * 0.18)))
        self.screen.blit(self.logo, logo_rect)

        self._draw_centered(
            "Shift the board. Connect your pawns.",
            self.h2_font,
            int(self.h * 0.30),
            (200, 200, 200)
        )

        buttons = [self.btn_play, self.btn_help, self.btn_settings, self.btn_exit]
        left = min(b.rect.left for b in buttons)
        top = min(b.rect.top for b in buttons)
        right = max(b.rect.right for b in buttons)
        bottom = max(b.rect.bottom for b in buttons)

        panel_rect = pygame.Rect(left, top, right - left, bottom - top).inflate(80, 50)
        self._panel(panel_rect)

        if self.btn_play.handle(mouse_pos, mouse_down):
            self.state = MenuUI.PLAY
        if self.btn_help.handle(mouse_pos, mouse_down):
            self.state = MenuUI.HELP
        if self.btn_settings.handle(mouse_pos, mouse_down):
            self.state = MenuUI.SETTINGS
        if self.btn_exit.handle(mouse_pos, mouse_down):
            return "QUIT"

        for b in buttons:
            b.draw(self.screen)

        footer = "Based on the classic board game"
        self.screen.blit(
            self.small.render(footer, True, (170, 170, 170)),
            (self.w//2 - 140, self.h - 32)
        )
        return None

    def draw_play_menu(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("PLAY", self.title_font, 70)

        pygame.draw.line(
            self.screen,
            (220, 220, 220),
            (self.w // 2, 120),
            (self.w // 2, self.h - 110),
            3
        )

        if self.card_classic.handle(mouse_pos, mouse_down):
            self.state = MenuUI.CLASSIC
        if self.card_modes.handle(mouse_pos, mouse_down):
            self.state = MenuUI.MODES
        if self.btn_back_play.handle(mouse_pos, mouse_down):
            self.state = MenuUI.MAIN

        self.card_classic.draw(self.screen, self.h2_font, self.h2_font)
        self.card_modes.draw(self.screen, self.h2_font, self.h2_font)
        self.btn_back_play.draw(self.screen, self.font, self.btn_colors)
        return None

    def draw_classic_menu(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("CLASSIC", self.title_font, 70)

        pygame.draw.line(
            self.screen,
            (220, 220, 220),
            (self.w // 2, 120),
            (self.w // 2, self.h - 110),
            3
        )

        if self.card_one_player.handle(mouse_pos, mouse_down):
            self.choice.mode = "SINGLE"
            self.choice.variant = "CLASSIC"
            self.state = MenuUI.SINGLE

        if self.card_two_player.handle(mouse_pos, mouse_down):
            return "PLAY_LOCAL"

        if self.btn_back_classic.handle(mouse_pos, mouse_down):
            self.state = MenuUI.PLAY

        self.card_one_player.draw(self.screen, self.h2_font, self.h2_font)
        self.card_two_player.draw(self.screen, self.h2_font, self.h2_font)
        self.btn_back_classic.draw(self.screen, self.font, self.btn_colors)
        return None

    def draw_modes_menu(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("MODES", self.title_font, 70)

        x1 = self.card_control.rect.right + 25
        x2 = self.card_mega.rect.right + 25

        pygame.draw.line(self.screen, (220, 220, 220), (x1, 140), (x1, self.h - 110), 3)
        pygame.draw.line(self.screen, (220, 220, 220), (x2, 140), (x2, self.h - 110), 3)

        if self.card_control.handle(mouse_pos, mouse_down):
            self.choice.mode = "SINGLE"
            self.choice.variant = "CONTROL"
            self.state = MenuUI.SINGLE

        if self.card_mega.handle(mouse_pos, mouse_down):
            self.choice.mode = "SINGLE"
            self.choice.variant = "MEGA"
            self.state = MenuUI.SINGLE

        if self.card_survival.handle(mouse_pos, mouse_down):
            self.choice.mode = "SINGLE"
            self.choice.variant = "SURVIVAL"
            self.state = MenuUI.SINGLE

        if self.btn_back_modes.handle(mouse_pos, mouse_down):
            self.state = MenuUI.PLAY

        self.card_control.draw(self.screen, self.h2_font, self.h2_font)
        self.card_mega.draw(self.screen, self.h2_font, self.h2_font)
        self.card_survival.draw(self.screen, self.h2_font, self.h2_font)
        self.btn_back_modes.draw(self.screen, self.font, self.btn_colors)
        return None

    def draw_single(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered(self.choice.variant, self.title_font, int(self.h * 0.16))
        self._draw_centered("Choose your side", self.h2_font, int(self.h * 0.24), (200, 200, 200))

        panel = pygame.Rect(self.w//2 - 260, int(self.h*0.30), 520, int(self.h*0.30))
        self._panel(panel)

        x = panel.x + 24
        y = panel.y + 22
        self.side_group.draw(self.screen, self.font, self.small, x, y, panel.w - 48, 46, mouse_pos, mouse_down)

        self.choice.mode = "SINGLE"
        self.choice.side = "A" if self.side_group.value().startswith("Red") else "B"

        if self.btn_start.handle(mouse_pos, mouse_down):
            return "START_SINGLE"

        if self.btn_back.handle(mouse_pos, mouse_down):
            if self.choice.variant == "CLASSIC":
                self.state = MenuUI.CLASSIC
            else:
                self.state = MenuUI.MODES

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
            "Win by getting all your pawns into one connected cluster.",
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

    def draw_settings(self, mouse_pos, mouse_down) -> Optional[str]:
        self._draw_centered("Settings", self.title_font, int(self.h * 0.16))
        panel = pygame.Rect(self.w//2 - 300, int(self.h*0.30), 600, 220)
        self._panel(panel)

        text = self.h2_font.render("Settings will be added later.", True, (210, 210, 210))
        self.screen.blit(text, text.get_rect(center=panel.center))

        if self.btn_back3.handle(mouse_pos, mouse_down):
            self.state = MenuUI.MAIN
        self.btn_back3.draw(self.screen, self.font, self.btn_colors)
        return None

    def run(self, clock: pygame.time.Clock) -> Optional[MenuChoice]:
        while True:
            mouse_down = False
            mouse_pos = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None

                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    if self.state == MenuUI.MAIN:
                        return None
                    elif self.state == MenuUI.PLAY:
                        self.state = MenuUI.MAIN
                    elif self.state == MenuUI.CLASSIC:
                        self.state = MenuUI.PLAY
                    elif self.state == MenuUI.MODES:
                        self.state = MenuUI.PLAY
                    elif self.state == MenuUI.SINGLE:
                        if self.choice.variant == "CLASSIC":
                            self.state = MenuUI.CLASSIC
                        else:
                            self.state = MenuUI.MODES
                    elif self.state in (MenuUI.HELP, MenuUI.SETTINGS):
                        self.state = MenuUI.MAIN

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mouse_down = True
                    mouse_pos = ev.pos

            self.screen.fill(self.bg)

            action = None
            if self.state == MenuUI.MAIN:
                action = self.draw_main(mouse_pos, mouse_down)
            elif self.state == MenuUI.PLAY:
                action = self.draw_play_menu(mouse_pos, mouse_down)
            elif self.state == MenuUI.CLASSIC:
                action = self.draw_classic_menu(mouse_pos, mouse_down)
            elif self.state == MenuUI.MODES:
                action = self.draw_modes_menu(mouse_pos, mouse_down)
            elif self.state == MenuUI.SINGLE:
                action = self.draw_single(mouse_pos, mouse_down)
            elif self.state == MenuUI.HELP:
                action = self.draw_help(mouse_pos, mouse_down)
            elif self.state == MenuUI.SETTINGS:
                action = self.draw_settings(mouse_pos, mouse_down)

            pygame.display.flip()
            clock.tick(60)

            if action == "QUIT":
                return None

            if action == "PLAY_LOCAL":
                return MenuChoice(
                    mode="LOCAL",
                    side="A",
                    variant="CLASSIC",
                    config=classic_config()
                )

            if action == "START_SINGLE":
                if self.choice.variant == "CLASSIC":
                    config = classic_config()
                elif self.choice.variant == "MEGA":
                    config = mega_config()
                elif self.choice.variant == "CONTROL":
                    config = control_config()
                elif self.choice.variant == "SURVIVAL":
                    config = survival_config()
                else:
                    config = classic_config()

                return MenuChoice(
                    mode=self.choice.mode,
                    side=self.choice.side,
                    variant=self.choice.variant,
                    config=config
                )