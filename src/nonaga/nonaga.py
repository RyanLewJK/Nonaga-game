import sys
import traceback
import pygame

from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.renderer import Renderer
from src.nonaga.input_handler import InputHandler
from src.nonaga.constants import SCREEN_W, SCREEN_H
from src.nonaga.menu import MenuUI

from src.nonaga.ai_new import choose_ai_turn


def run_game(choice):
    DEBUG_AI = True
    DEBUG_EVENTS = False

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Nonaga (Python/Pygame)")
    clock = pygame.time.Clock()

    game = NonagaGame()
    renderer = Renderer(screen)
    input_handler = InputHandler(game)

    single_player = (choice.mode == "SINGLE")
    HUMAN_PLAYER = choice.side
    AI_PLAYER = "B" if HUMAN_PLAYER == "A" else "A"

    ai_pending = False
    ai_debug_once = False

    # Draw initial board immediately so screen is not black
    renderer.draw(game, single_player=single_player, human_player=HUMAN_PLAYER)
    pygame.display.flip()
    pygame.event.pump()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        # Update timer every frame
        game.update_timer(dt)

        # If time ran out, just keep showing game-over screen
        if game.phase == Phase.GAME_OVER:
            ai_pending = False

        # Queue AI turn
        if single_player and game.current == AI_PLAYER and game.phase == Phase.MOVE_PAWN:
            ai_pending = True
            if DEBUG_AI and not ai_debug_once:
                print("\n=== AI TURN DETECTED ===")
                print("single_player:", single_player)
                print("HUMAN_PLAYER:", HUMAN_PLAYER, "AI_PLAYER:", AI_PLAYER)
                print("game.current:", game.current, "game.phase:", game.phase)
                print("blocked:", game.blocked)
                print("A pawns:", game.pawns["A"])
                print("B pawns:", game.pawns["B"])
                print("occupied count:", len(game.occupied))
                ai_debug_once = True

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "QUIT"

            if DEBUG_EVENTS and ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                print("EVENT:", ev)

            # Block human input during AI turn, but still allow menu button on game over
            if single_player and game.current != HUMAN_PLAYER and game.phase != Phase.GAME_OVER:
                if DEBUG_AI and ev.type == pygame.MOUSEBUTTONDOWN:
                    print("Human clicked during AI turn (ignored).")
                continue

            result = input_handler.handle_event(ev)
            if result == "MENU":
                return "MENU"

        # Draw board/UI every frame
        renderer.draw(game, single_player=single_player, human_player=HUMAN_PLAYER)
        pygame.display.flip()

        # Run AI once when pending
        if single_player and ai_pending and game.current == AI_PLAYER and game.phase == Phase.MOVE_PAWN:
            ai_pending = False
            ai_debug_once = False
            pygame.event.pump()

            try:
                if DEBUG_AI:
                    print("AI: calling choose_ai_turn...")

                turn = choose_ai_turn(game, AI_PLAYER, depth=2, top_k_placements=6)

                if DEBUG_AI:
                    print("AI: choose_ai_turn returned:", turn)

                if turn is None:
                    print("AI: No legal turns found. Giving turn back to human.")
                    game.current = HUMAN_PLAYER
                else:
                    pawn_i, target, rem_key, place_key = turn
                    print(
                        "AI: applying turn ->",
                        "pawn_i:", pawn_i,
                        "target:", target,
                        "remove:", rem_key,
                        "place:", place_key
                    )

                    game.snapshot()
                    game.pawns[AI_PLAYER][pawn_i] = target
                    game.occupied.remove(rem_key)
                    game.occupied.add(place_key)
                    game.end_turn_after_placement(place_key)

                    if DEBUG_AI:
                        print("AI: done. New current:", game.current, "phase:", game.phase)

            except Exception:
                print("\n!!! AI CRASHED !!!")
                traceback.print_exc()
                print("State dump at crash:")
                print("current:", game.current, "phase:", game.phase, "AI_PLAYER:", AI_PLAYER)
                print("blocked:", game.blocked)
                print("A pawns:", game.pawns["A"])
                print("B pawns:", game.pawns["B"])
                print("occupied count:", len(game.occupied))
                return "MENU"


def main():
    pygame.init()

    while True:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Nonaga (Python/Pygame)")
        clock = pygame.time.Clock()

        menu = MenuUI(screen)
        choice = menu.run(clock)

        if choice is None:
            break

        result = run_game(choice)
        if result == "QUIT":
            break

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()