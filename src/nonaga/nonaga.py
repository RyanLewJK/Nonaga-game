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
from src.nonaga.hexgrid import k

from src.nonaga.ai_new import choose_ai_turn, clone_game


def ai_worker_loop(job_queue, result_queue):
    while True:
        job = job_queue.get()

        if job is None:
            break

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
            err = traceback.format_exc()
            print("AI worker crashed:")
            print(err)
            result_queue.put({
                "status": "ERROR",
                "job_id": job.get("job_id"),
                "error": err,
            })


def run_game(choice):
    DEBUG_AI = True
    DEBUG_EVENTS = False

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Nonaga (Python/Pygame)")
    clock = pygame.time.Clock()
    pause_menu_open = False

    single_player = (choice.mode == "SINGLE")
    HUMAN_PLAYER = choice.side
    AI_PLAYER = "B" if HUMAN_PLAYER == "A" else "A"

    game = NonagaGame(
        config=choice.config,
        human_player=HUMAN_PLAYER,
        ai_player=AI_PLAYER
    )

    renderer = Renderer(screen)
    input_handler = InputHandler(game)

    AI_DEPTH = choice.config.ai_depth if choice.config else 2
    AI_TOPK = choice.config.ai_top_k if choice.config else 6

    print("AI config:", choice.config.variant, "depth=", AI_DEPTH, "top_k=", AI_TOPK)

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
    ai_result_ready = False

    MIN_AI_THINK_TIME = 0.8

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

    def resolve_ai_gold_powerup():
        opponent = HUMAN_PLAYER
        print("AI resolving GOLD powerup")
        best_idx = None
        best_target = None
        best_score = -10**9

        for idx in game.gold_movable_enemy_indices:
            current_pos = game.pawns[opponent][idx]
            moves = game.pawn_moves_from(current_pos)

            for target_pos in moves:
                score = 0
                for j, other in enumerate(game.pawns[opponent]):
                    if j != idx:
                        score += abs(target_pos[0] - other[0]) + abs(target_pos[1] - other[1])

                if score > best_score:
                    best_score = score
                    best_idx = idx
                    best_target = target_pos

        if best_idx is not None and best_target is not None:
            game.pawns[opponent][best_idx] = best_target
            game.set_action_text("AI used GOLD to move your pawn!")
        else:
            game.set_action_text("AI activated GOLD, but no pawn could move.")
        print("AI moved human pawn:", best_idx, best_target)
        winner = game.check_any_win()
        if winner is not None:
            game.winner = winner
            game.phase = Phase.GAME_OVER
            return

        game.gold_move_enemy_active = False
        game.gold_movable_enemy_indices = []
        game.gold_valid_enemy_moves = []
        game.gold_selected_enemy_idx = None
        game.finish_turn()

    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        if not pause_menu_open:
            game.update_timer(dt)

        # Start AI search
        if (
            not pause_menu_open
            and single_player
            and game.current == AI_PLAYER
            and game.phase == Phase.MOVE_PAWN
            and not ai_running
            and not ai_result_ready
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
            ai_result_ready = False
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

            # ---------------- KEYBOARD INPUT ----------------
            if ev.type == pygame.KEYDOWN:

                # Restart
                if ev.key == pygame.K_r:
                    ai_running = False
                    ai_result = None
                    ai_error = None
                    ai_result_ready = False
                    ai_active_job_id = None
                    ai_debug_once = False
                    ai_start_time = None
                    game.reset()
                    continue

                # Cancel selection
                if ev.key == pygame.K_x:
                    if game.phase == Phase.MOVE_PAWN and game.selected_idx is not None:
                        game.cancel_selection()
                        continue

                    if game.phase == Phase.PICK_PLACE and game.removable is not None:
                        game.cancel_selection()
                        continue

                # Pause menu only opens with ESC
                if ev.key == pygame.K_ESCAPE:
                    if pause_menu_open:
                        pause_menu_open = False
                    elif game.phase != Phase.GAME_OVER:
                        pause_menu_open = True
                    continue

            # ---------------- PAUSE MENU INPUT ----------------
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

            # ---------------- BLOCK HUMAN DURING AI TURN ----------------
            if (
                single_player
                and (game.current != HUMAN_PLAYER or ai_running)
                and game.phase != Phase.GAME_OVER
            ):
                if DEBUG_AI and ev.type == pygame.MOUSEBUTTONDOWN:
                    print("Human clicked during AI turn (ignored).")
                continue

            # ---------------- RIGHT-CLICK ENEMY MOVE PREVIEW ----------------
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                cell_key = input_handler.hit_test_disc(*ev.pos)

                if cell_key is not None:
                    enemy = "B" if game.current == "A" else "A"
                    idx = game.pawn_index_at(enemy, cell_key)

                    if idx is not None:
                        # -1 means preview mode, not a real selected pawn
                        game.selected_idx = -1
                        game.valid_moves = game.pawn_moves_from(game.pawns[enemy][idx])
                    else:
                        game.selected_idx = None
                        game.valid_moves = []

                continue

            # ---------------- NORMAL INPUT ----------------
            result = input_handler.handle_event(ev)

            if result == "MENU":
                shutdown_ai_worker()
                return "MENU"

            if result == "RESTART":
                ai_running = False
                ai_result = None
                ai_error = None
                ai_result_ready = False
                ai_active_job_id = None
                ai_debug_once = False
                ai_start_time = None
                game.reset()

        # Poll worker result queue
        if ai_result_queue is not None:
            while True:
                try:
                    msg = ai_result_queue.get_nowait()
                except Empty:
                    break

                if msg.get("job_id") != ai_active_job_id:
                    continue

                if msg["status"] == "OK":
                    ai_result = msg["turn"]
                    ai_error = None
                    ai_result_ready = True
                else:
                    ai_result = None
                    ai_error = msg.get("error", "Unknown AI worker error")
                    ai_result_ready = True

                ai_running = False

        renderer.draw(game, single_player=single_player, human_player=HUMAN_PLAYER)

        if pause_menu_open:
            renderer.draw_pause_menu()

        pygame.display.flip()

        # Handle AI worker errors
        if ai_error is not None:
            print("AI worker error:")
            print(ai_error)
            shutdown_ai_worker()
            return "MENU"

        # Apply AI move once ready
        if not pause_menu_open and ai_result_ready:
            ai_debug_once = False

            is_winning_move = False

            if ai_result is not None:
                test_game = clone_game(game)
                pawn_i, target, rem_key, place_key = ai_result
                test_game.pawns[AI_PLAYER][pawn_i] = target
                test_game.current = AI_PLAYER
                if test_game.check_any_win() == AI_PLAYER:
                    is_winning_move = True

            if (
                not is_winning_move
                and ai_start_time is not None
                and (time.time() - ai_start_time) < MIN_AI_THINK_TIME
            ):
                continue

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

                    landed_on_gold = game.gold_disc is not None and k(target) == game.gold_disc
                    landed_on_silver = game.silver_disc is not None and k(target) == game.silver_disc
                    print("AI landed_on_gold:", landed_on_gold)
                    print("AI landed_on_silver:", landed_on_silver)

                    game.pawns[AI_PLAYER][pawn_i] = target
                    game.handle_special_landing(AI_PLAYER, target)

                    winner = game.check_any_win()
                    if winner is not None:
                        game.winner = winner
                        game.phase = Phase.GAME_OVER
                    else:
                        removed_was_gold = (rem_key == game.gold_disc)
                        removed_was_silver = (rem_key == game.silver_disc)

                        if rem_key in game.occupied:
                            game.occupied.remove(rem_key)

                        if removed_was_gold:
                            game.gold_disc = None
                        if removed_was_silver:
                            game.silver_disc = None

                        game.occupied.add(place_key)

                        if removed_was_gold:
                            game.gold_disc = place_key
                        if removed_was_silver:
                            game.silver_disc = place_key

                        game.end_turn_after_placement(place_key)

                        if game.phase == "GOLD_MOVE_ENEMY":
                            resolve_ai_gold_powerup()

                    if DEBUG_AI:
                        print("AI: done. New current:", game.current, "phase:", game.phase)

            ai_result = None
            ai_error = None
            ai_result_ready = False
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