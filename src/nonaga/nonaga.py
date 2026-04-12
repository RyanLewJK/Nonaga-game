import sys
import traceback
import pygame

from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.renderer import Renderer
from src.nonaga.input_handler import InputHandler
from src.nonaga.constants import SCREEN_W, SCREEN_H
from src.nonaga.menu import MenuUI

# IMPORTANT: make sure ai.py is in the same folder
from src.nonaga.ai_new import choose_ai_turn


def run_game(choice):
    DEBUG_AI = True
    DEBUG_EVENTS = False  # set True if you want to log events

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Nonaga (Python/Pygame)")
    clock = pygame.time.Clock()

    game = NonagaGame()
    renderer = Renderer(screen)
    input_handler = InputHandler(game)

    single_player = (choice.mode == "SINGLE")
    HUMAN_PLAYER = choice.side                 # "A" or "B"
    AI_PLAYER = "B" if HUMAN_PLAYER == "A" else "A"

    ai_pending = False
    ai_debug_once = False  # so "AI TURN DETECTED" prints once per AI turn

    running = True
    while running:
        # If it's AI's turn, queue it (even if we missed the exact click event)
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
                running = False
                continue

            if DEBUG_EVENTS and ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                print("EVENT:", ev)

            # Block human input during AI turn (single player only)
            if single_player and game.current != HUMAN_PLAYER:
                if DEBUG_AI and ev.type == pygame.MOUSEBUTTONDOWN:
                    print("Human clicked during AI turn (ignored).")
                continue

            input_handler.handle_event(ev)

        # --- Run AI once when pending ---
        if single_player and ai_pending and game.current == AI_PLAYER and game.phase == Phase.MOVE_PAWN:
            ai_pending = False
            ai_debug_once = False  # reset so next AI turn prints again

            try:
                if DEBUG_AI:
                    print("AI: calling choose_ai_turn...")

                # TEMP SETTINGS while debugging:
                # start small; once stable, bump depth/top_k back up
                turn = choose_ai_turn(game, AI_PLAYER, depth=2, top_k_placements=6)

                if DEBUG_AI:
                    print("AI: choose_ai_turn returned:", turn)

                if turn is None:
                    print("AI: No legal turns found. Giving turn back to human.")
                    game.current = HUMAN_PLAYER
                else:
                    pawn_i, target, rem_key, place_key = turn
                    print("AI: applying turn ->",
                          "pawn_i:", pawn_i,
                          "target:", target,
                          "remove:", rem_key,
                          "place:", place_key)

                    # Apply chosen full turn to the REAL game
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
                running = False  # stop loop so you can read the console

        renderer.draw(game)
        pygame.display.flip()
        clock.tick(60)


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Nonaga (Python/Pygame)")
    clock = pygame.time.Clock()

    menu = MenuUI(screen)
    choice = menu.run(clock)

    if choice is None:
        pygame.quit()
        sys.exit(0)

    run_game(choice)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()