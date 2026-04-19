import sys
import traceback
import pygame
import multiprocessing as mp
from queue import Empty
import time

from src.nonaga.game_state import NonagaGame, Phase
from src.nonaga.renderer import Renderer
from src.nonaga.input_handler import InputHandler
from src.nonaga.constants import SCREEN_W, SCREEN_H
from src.nonaga.menu import MenuUI

from src.nonaga.ai_new import choose_ai_turn, clone_game


def ai_worker_loop(job_queue, result_queue):
    """
    Persistent AI worker process.
    Waits for jobs, solves them, sends back results.
    """
    while True:
        job = job_queue.get()

        if job is None:
            break  # clean shutdown

        try:
            job_id = job["job_id"]
            game_copy = job["game"]
            ai_player = job["ai_player"]
            depth = job["depth"]
            top_k_placements = job["top_k_placements"]

            turn = choose_ai_turn(
                game_copy,
                ai_player,
                depth=depth,
                top_k_placements=top_k_placements
            )

            result_queue.put({
                "status": "OK",
                "job_id": job_id,
                "turn": turn,
            })

        except Exception:
            result_queue.put({
                "status": "ERROR",
                "job_id": job.get("job_id"),
                "error": traceback.format_exc(),
            })


def run_game(choice):
    DEBUG_AI = True
    DEBUG_EVENTS = False

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Nonaga (Python/Pygame)")
    clock = pygame.time.Clock()
    pause_menu_open = False

    game = NonagaGame()
    renderer = Renderer(screen)
    input_handler = InputHandler(game)

    single_player = (choice.mode == "SINGLE")
    HUMAN_PLAYER = choice.side
    AI_PLAYER = "B" if HUMAN_PLAYER == "A" else "A"

    # Final gameplay settings
    AI_DEPTH = 2
    AI_TOPK = 6

    # Persistent worker state
    ai_job_queue = None
    ai_result_queue = None
    ai_process = None

    ai_running = False
    ai_result = None
    ai_error = None
    ai_debug_once = False
    ai_job_id = 0
    ai_active_job_id = None
    ai_start_time = None

    # Start persistent worker only for single-player
    if single_player:
        ai_job_queue = mp.Queue()
        ai_result_queue = mp.Queue()
        ai_process = mp.Process(
            target=ai_worker_loop,
            args=(ai_job_queue, ai_result_queue),
            daemon=True
        )
        ai_process.start()

    renderer.draw(game, single_player=single_player, human_player=HUMAN_PLAYER)
    pygame.display.flip()
    pygame.event.pump()

    def shutdown_ai_worker():
        nonlocal ai_process, ai_job_queue, ai_result_queue, ai_running, ai_active_job_id
        try:
            if ai_job_queue is not None:
                ai_job_queue.put(None)
        except Exception:
            pass

        if ai_process is not None and ai_process.is_alive():
            ai_process.join(timeout=0.5)

        if ai_process is not None and ai_process.is_alive():
            ai_process.terminate()
            ai_process.join(timeout=0.2)

        ai_process = None
        ai_job_queue = None
        ai_result_queue = None
        ai_running = False
        ai_active_job_id = None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        if not pause_menu_open:
            game.update_timer(dt)

        # Start AI search by sending a job to the persistent worker
        if (
            not pause_menu_open
            and single_player
            and game.current == AI_PLAYER
            and game.phase == Phase.MOVE_PAWN
            and not ai_running
            and ai_process is not None
        ):
            if DEBUG_AI and not ai_debug_once:
                print("\n=== AI TURN DETECTED ===")
                print("single_player:", single_player)
                print("HUMAN_PLAYER:", HUMAN_PLAYER, "AI_PLAYER:", AI_PLAYER)
                print("game.current:", game.current, "game.phase:", game.phase)
                print("blocked:", game.blocked)
                print("A pawns:", game.pawns["A"])
                print("B pawns:", game.pawns["B"])
                print("occupied count:", len(game.occupied))
                print(f"AI: sending job to persistent worker (depth={AI_DEPTH}, top_k={AI_TOPK})...")
                ai_debug_once = True

            ai_result = None
            ai_error = None
            ai_running = True
            ai_start_time = time.time()

            ai_job_id += 1
            ai_active_job_id = ai_job_id

            game_copy = clone_game(game)

            ai_job_queue.put({
                "job_id": ai_active_job_id,
                "game": game_copy,
                "ai_player": AI_PLAYER,
                "depth": AI_DEPTH,
                "top_k_placements": AI_TOPK,
            })

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                shutdown_ai_worker()
                return "QUIT"

            if DEBUG_EVENTS and ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                print("EVENT:", ev)

            if ev.type == pygame.KEYDOWN:
                # X = cancel selection
                if ev.key == pygame.K_x:
                    if game.phase == Phase.MOVE_PAWN and game.selected_idx is not None:
                        game.cancel_selection()
                        continue

                    if game.phase == Phase.PICK_PLACE and game.removable is not None:
                        game.cancel_selection()
                        continue

                # ESC = pause menu
                if ev.key == pygame.K_ESCAPE:
                    if pause_menu_open:
                        pause_menu_open = False
                        continue

                    if game.phase != Phase.GAME_OVER:
                        pause_menu_open = True
                        continue

                if game.phase == Phase.MOVE_PAWN and game.selected_idx is not None:
                    game.cancel_selection()
                    continue

                if game.phase == Phase.PICK_PLACE and game.removable is not None:
                    game.cancel_selection()
                    continue

                if game.phase != Phase.GAME_OVER:
                    pause_menu_open = True
                    continue

            if pause_menu_open:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    action = input_handler.hit_test_pause_menu_buttons(mx, my)

                    if action == "RESUME":
                        pause_menu_open = False
                    elif action == "MENU":
                        shutdown_ai_worker()
                        return "MENU"
                    elif action == "SETTINGS":
                        print("Settings not implemented yet")
                continue

            # Block human input during AI turn
            if single_player and (game.current != HUMAN_PLAYER or ai_running) and game.phase != Phase.GAME_OVER:
                if DEBUG_AI and ev.type == pygame.MOUSEBUTTONDOWN:
                    print("Human clicked during AI turn (ignored).")
                continue

            result = input_handler.handle_event(ev)
            if result == "MENU":
                shutdown_ai_worker()
                return "MENU"
            if result == "RESTART":
                # Ignore any stale result from old position
                ai_running = False
                ai_result = None
                ai_error = None
                ai_active_job_id = None
                ai_debug_once = False
                game.reset()

        # Poll worker result queue without blocking
        if ai_result_queue is not None:
            while True:
                try:
                    msg = ai_result_queue.get_nowait()
                except Empty:
                    break

                # Ignore stale jobs
                if msg.get("job_id") != ai_active_job_id:
                    continue

                if msg["status"] == "OK":
                    ai_result = msg["turn"]
                    ai_error = None
                else:
                    ai_result = None
                    ai_error = msg.get("error", "Unknown AI worker error")

                ai_running = False

        renderer.draw(game, single_player=single_player, human_player=HUMAN_PLAYER)

        if pause_menu_open:
            renderer.draw_pause_menu()


        pygame.display.flip()

        # Apply AI move once ready
        if not pause_menu_open and ai_result is not None:
            ai_debug_once = False

            if ai_error is not None:
                print("AI worker error:")
                print(ai_error)
                shutdown_ai_worker()
                return "MENU"

            if game.phase != Phase.GAME_OVER and game.current == AI_PLAYER:
                turn = ai_result

                if DEBUG_AI:
                    print("AI: choose_ai_turn returned:", turn)
                    if ai_start_time is not None:
                        print(f"AI move took: {time.time() - ai_start_time:.2f}s")

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

                    game.pawns[AI_PLAYER][pawn_i] = target
                    game.occupied.remove(rem_key)
                    game.occupied.add(place_key)
                    game.end_turn_after_placement(place_key)

                    if DEBUG_AI:
                        print("AI: done. New current:", game.current, "phase:", game.phase)

            ai_result = None
            ai_error = None
            ai_running = False
            ai_active_job_id = None
            ai_start_time = None

    shutdown_ai_worker()
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
    mp.freeze_support()
    main()