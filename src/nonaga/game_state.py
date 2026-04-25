import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from src.nonaga.hexgrid import Axial, DIRS, k, parse_key
from src.nonaga.game_config import GameConfig, classic_config


class Phase:
    MOVE_PAWN = "MOVE_PAWN"
    PICK_REMOVE = "PICK_REMOVE"
    PICK_PLACE = "PICK_PLACE"
    GAME_OVER = "GAME_OVER"


@dataclass
class Snapshot:
    occupied: Set[str]
    pawns: Dict[str, List[Axial]]
    current: str
    phase: str
    selected_idx: Optional[int]
    removable: Optional[str]
    blocked: Optional[str]
    time_left: Dict[str, float]
    winner: Optional[str]

    survival_turn_count: int

    gold_disc: Optional[str]
    silver_disc: Optional[str]

    gold_respawn_counter: int
    silver_respawn_counter: int

    special_remove_any: bool

    gold_move_enemy_active: bool
    gold_movable_enemy_indices: List[int]
    gold_valid_enemy_moves: List[Axial]
    gold_selected_enemy_idx: Optional[int]


class NonagaGame:
    def __init__(
        self,
        config: Optional[GameConfig] = None,
        human_player: str = "A",
        ai_player: str = "B"
    ):
        self.config = config if config is not None else classic_config()

        if self.config.survival_mode:
            self.human_player = "A"
            self.ai_player = "B"
        else:
            self.human_player = human_player
            self.ai_player = ai_player

        default_time = 300.0
        if self.config.turn_time_limit is not None:
            default_time = float(self.config.turn_time_limit)

        self.time_left = {"A": default_time, "B": default_time}
        self.winner: Optional[str] = None
        self.occupied: Set[str] = set()
        self.pawns: Dict[str, List[Axial]] = {"A": [], "B": []}
        self.current = "A"
        self.phase = Phase.MOVE_PAWN
        self.selected_idx: Optional[int] = None
        self.removable: Optional[str] = None
        self.blocked: Optional[str] = None

        self.valid_moves: List[Axial] = []
        self.valid_removals: Set[str] = set()
        self.valid_placements: Set[str] = set()

        self.survival_turn_count = 0

        self.gold_disc: Optional[str] = None
        self.silver_disc: Optional[str] = None

        self.removed_was_gold = False
        self.removed_was_silver = False

        self.gold_respawn_counter = 0
        self.silver_respawn_counter = 0

        self.gold_move_enemy_active = False
        self.gold_movable_enemy_indices: List[int] = []
        self.gold_valid_enemy_moves: List[Axial] = []
        self.gold_selected_enemy_idx: Optional[int] = None

        self.special_remove_any = False

        self.last_action_text = ""
        self.last_action_timer = 0.0

        self.history: List[Snapshot] = []
        self.reset()

    def snapshot(self):
        self.history.append(
            Snapshot(
                occupied=set(self.occupied),
                pawns={"A": [p[:] for p in self.pawns["A"]], "B": [p[:] for p in self.pawns["B"]]},
                current=self.current,
                phase=self.phase,
                selected_idx=self.selected_idx,
                removable=self.removable,
                blocked=self.blocked,
                time_left=dict(self.time_left),
                winner=self.winner,

                survival_turn_count=self.survival_turn_count,

                gold_disc=self.gold_disc,
                silver_disc=self.silver_disc,

                gold_respawn_counter=self.gold_respawn_counter,
                silver_respawn_counter=self.silver_respawn_counter,

                special_remove_any=self.special_remove_any,

                gold_move_enemy_active=self.gold_move_enemy_active,
                gold_movable_enemy_indices=list(self.gold_movable_enemy_indices),
                gold_valid_enemy_moves=list(self.gold_valid_enemy_moves),
                gold_selected_enemy_idx=self.gold_selected_enemy_idx,
            )
        )
        if len(self.history) > 200:
            self.history.pop(0)

    def cancel_selection(self):
        if self.phase == Phase.MOVE_PAWN and self.selected_idx is not None:
            self.selected_idx = None
            self.valid_moves = []
            return

        if self.phase == Phase.PICK_PLACE and self.removable is not None:
            self.occupied.add(self.removable)

            if self.removed_was_gold:
                self.gold_disc = self.removable
                self.removed_was_gold = False

            if self.removed_was_silver:
                self.silver_disc = self.removable
                self.removed_was_silver = False

            self.phase = Phase.PICK_REMOVE
            self.valid_placements = set()
            self.valid_removals = self.compute_valid_removals()
            self.removable = None
            return

    def _board_radius(self) -> int:
        return self.config.board_radius
    
    def opponent_of(self, player: str) -> str:
        return "B" if player == "A" else "A"

    def start_gold_enemy_move_phase(self):
        opponent = self.opponent_of(self.current)

        self.gold_movable_enemy_indices = []
        self.gold_valid_enemy_moves = []
        self.gold_selected_enemy_idx = None

        for idx, pos in enumerate(self.pawns[opponent]):
            moves = self.pawn_moves_from(pos)
            if moves:
                self.gold_movable_enemy_indices.append(idx)

        if self.gold_movable_enemy_indices:
            self.phase = "GOLD_MOVE_ENEMY"
        else:
            # no valid enemy pawn moves, just end normally
            self.gold_move_enemy_active = False
            self.finish_turn()

    def _initial_time(self) -> float:
        if self.config.turn_time_limit is not None:
            return float(self.config.turn_time_limit)
        return 300.0

    def _initial_pawns(self) -> Dict[str, List[Axial]]:
        # Survival mode: human has 2 pawns, AI has 3 with 2 already together
        if self.config.survival_mode:
            human_pawns = [(2, 0), (0, 2)]

            ai_options = [
                [(-2, 0), (-1, 0), (2, -2)],
                [(1, -1), (1, 1), (-2, 2)],
                [(-2, 0), (-1, 1), (1, -2)],
                [(-1, 0), (1, -1), (-2, 2)]
            ]

            ai_pawns = random.choice(ai_options)

            return {
                "A": human_pawns,
                "B": ai_pawns
            }

        # Standard board
        if self.config.board_radius == 2:
            corners = [(2, 0), (2, -2), (0, -2), (-2, 0), (-2, 2), (0, 2)]
            return {
                "A": [corners[0], corners[2], corners[4]],
                "B": [corners[1], corners[3], corners[5]],
            }

        # Mega board
        if self.config.board_radius == 3:
            corners = [(3, 0), (3, -3), (0, -3), (-3, 0), (-3, 3), (0, 3)]
            return {
                "A": [corners[0], corners[2], corners[4], (-1, -2)],
                "B": [corners[1], corners[3], corners[5], (1, 2)],
            }

        # Fallback
        corners = [(2, 0), (2, -2), (0, -2), (-2, 0), (-2, 2), (0, 2)]
        return {
            "A": [corners[0], corners[2], corners[4]],
            "B": [corners[1], corners[3], corners[5]],
        }

    def available_special_cells(self) -> List[str]:
        pawnset = self.pawn_set()
        out = []

        for cell in self.occupied:
            if cell in pawnset:
                continue
            if cell == self.gold_disc or cell == self.silver_disc:
                continue
            out.append(cell)

        return out

    def spawn_gold_disc(self):
        if not self.config.gold_enabled:
            self.gold_disc = None
            return

        cells = self.available_special_cells()
        self.gold_disc = random.choice(cells) if cells else None

    def spawn_silver_disc(self):
        if not self.config.silver_enabled:
            self.silver_disc = None
            return

        cells = self.available_special_cells()
        self.silver_disc = random.choice(cells) if cells else None

    def set_action_text(self, text: str, duration: float = 1.5):
        self.last_action_text = text
        self.last_action_timer = duration

    def is_edge_cell(self, cell_key: str) -> bool:
        q, r = parse_key(cell_key)
        for dq, dr in DIRS:
            if k((q + dq, r + dr)) not in self.occupied:
                return True
        return False

    def handle_special_landing(self, player: str, target: Axial):
        if not self.config.control_mode:
            return

        cell = k(target)

        if self.gold_disc is not None and cell == self.gold_disc:
            self.gold_disc = None
            self.gold_respawn_counter = self.config.respawn_delay_turns
            self.gold_move_enemy_active = True

        elif self.silver_disc is not None and cell == self.silver_disc:
            self.silver_disc = None
            self.silver_respawn_counter = self.config.respawn_delay_turns
            self.special_remove_any = True


    def advance_special_respawns(self):
        if self.gold_disc is None and self.gold_respawn_counter > 0:
            self.gold_respawn_counter -= 1
            if self.gold_respawn_counter == 0:
                self.spawn_gold_disc()

        if self.silver_disc is None and self.silver_respawn_counter > 0:
            self.silver_respawn_counter -= 1
            if self.silver_respawn_counter == 0:
                self.spawn_silver_disc()

    def reset(self):
        self.history.clear()
        self.occupied.clear()

        radius = self.config.board_radius
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if max(abs(q), abs(r), abs(s)) <= radius:
                    self.occupied.add(k((q, r)))

        self.pawns = self._initial_pawns()

        self.current = self.human_player if self.config.survival_mode else "A"
        self.phase = Phase.MOVE_PAWN
        self.selected_idx = None
        self.removable = None
        self.blocked = None

        default_time = 300.0
        if self.config.turn_time_limit is not None:
            default_time = float(self.config.turn_time_limit)
        self.time_left = {"A": default_time, "B": default_time}

        self.winner = None
        self.survival_turn_count = 0

        self.gold_disc = None
        self.silver_disc = None
        self.removed_was_gold = False
        self.removed_was_silver = False
        self.gold_respawn_counter = 0
        self.silver_respawn_counter = 0
        self.special_remove_any = False

        self.gold_move_enemy_active = False
        self.gold_movable_enemy_indices = []
        self.gold_valid_enemy_moves = []
        self.gold_selected_enemy_idx = None

        self.last_action_text = ""
        self.last_action_timer = 0.0

        if self.config.control_mode:
            self.spawn_gold_disc()
            self.spawn_silver_disc()

        self.recompute()

    def pawn_set(self) -> Set[str]:
        s = set()
        for p in self.pawns["A"]:
            s.add(k(p))
        for p in self.pawns["B"]:
            s.add(k(p))
        return s

    def pawn_moves_from(self, pos: Axial) -> List[Axial]:
        q, r = pos
        pawnset = self.pawn_set()
        moves: List[Axial] = []

        for dq, dr in DIRS:
            cq, cr = q, r
            moved = False

            while True:
                nq, nr = cq + dq, cr + dr

                if k((nq, nr)) not in self.occupied:
                    break
                if k((nq, nr)) in pawnset:
                    break

                cq, cr = nq, nr
                moved = True

            if moved:
                moves.append((cq, cr))

        return moves

    def compute_valid_removals(self) -> Set[str]:
        pawnset = self.pawn_set()
        out: Set[str] = set()

        for cell in self.occupied:
            if cell in pawnset:
                continue

            if self.special_remove_any:
                out.add(cell)
                continue

            q, r = parse_key(cell)
            open_sides = 0
            for dq, dr in DIRS:
                if k((q + dq, r + dr)) not in self.occupied:
                    open_sides += 1
            if open_sides > 0:
                out.add(cell)

        return out

    def can_place_at(self, pos: Axial) -> bool:
        if k(pos) in self.occupied:
            return False
        q, r = pos
        touches = 0
        for dq, dr in DIRS:
            if k((q + dq, r + dr)) in self.occupied:
                touches += 1
        return touches >= 2

    def compute_valid_placements(self) -> Set[str]:
        qs, rs = [], []
        for cell in self.occupied:
            q, r = parse_key(cell)
            qs.append(q)
            rs.append(r)

        qmin, qmax = min(qs) - 2, max(qs) + 2
        rmin, rmax = min(rs) - 2, max(rs) + 2

        out: Set[str] = set()
        for q in range(qmin, qmax + 1):
            for r in range(rmin, rmax + 1):
                cell_key = k((q, r))

                if cell_key == self.removable:
                    continue

                if self.can_place_at((q, r)):
                    out.add(cell_key)

        return out

    def pawn_index_at(self, player: str, cell_key: str) -> Optional[int]:
        for i, pos in enumerate(self.pawns[player]):
            if k(pos) == cell_key:
                return i
        return None

    def is_win(self, player: str) -> bool:
        cells = [k(p) for p in self.pawns[player]]
        if not cells:
            return False

        S = set(cells)
        stack = [cells[0]]
        seen = set()

        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            q, r = parse_key(cur)
            for dq, dr in DIRS:
                nk = k((q + dq, r + dr))
                if nk in S and nk not in seen:
                    stack.append(nk)

        return len(seen) == len(cells)

    def check_survival_win(self) -> Optional[str]:
        if not self.config.survival_mode:
            return None

        if self.config.survival_turns is None:
            return None

        if self.survival_turn_count >= self.config.survival_turns:
            return self.human_player

        return None

    def check_any_win(self) -> Optional[str]:
        if self.config.survival_mode:
            if self.is_win(self.ai_player):
                return self.ai_player

            winner = self.check_survival_win()
            if winner is not None:
                return winner

            return None

        if self.is_win("A"):
            return "A"
        if self.is_win("B"):
            return "B"

        return None

    def finish_turn(self):
        previous_player = self.current
        self.current = "B" if self.current == "A" else "A"

        if self.config.survival_mode and previous_player == self.human_player:
            self.survival_turn_count += 1
            winner = self.check_survival_win()
            if winner is not None:
                self.winner = winner
                self.phase = Phase.GAME_OVER
                return

        self.advance_special_respawns()

        self.special_remove_any = False

        self.gold_move_enemy_active = False
        self.gold_movable_enemy_indices = []
        self.gold_valid_enemy_moves = []
        self.gold_selected_enemy_idx = None

        self.phase = Phase.MOVE_PAWN
        self.recompute()

    def end_turn_after_placement(self, placed_key: str):
        self.blocked = None
        self.removable = None
        self.selected_idx = None
        self.valid_moves = []
        self.valid_removals = set()
        self.valid_placements = set()

        winner = self.check_any_win()
        if winner is not None:
            self.winner = winner
            self.phase = Phase.GAME_OVER
            return

        if self.gold_move_enemy_active:
            self.start_gold_enemy_move_phase()
            return

        self.finish_turn()

    def recompute(self):
        self.valid_moves = []
        self.valid_removals = self.compute_valid_removals()
        self.valid_placements = set()

    def click_disc(self, cell_key: str):
        if self.phase == Phase.GAME_OVER:
            return

        if self.phase == Phase.MOVE_PAWN:
            idx = self.pawn_index_at(self.current, cell_key)
            if idx is not None:
                self.selected_idx = idx
                self.valid_moves = self.pawn_moves_from(self.pawns[self.current][idx])
                return

            if self.selected_idx is not None and self.selected_idx >= 0:
                target = parse_key(cell_key)
                if target in self.valid_moves:
                    self.pawns[self.current][self.selected_idx] = target
                    self.handle_special_landing(self.current, target)
                    self.selected_idx = None
                    self.valid_moves = []
                    self.phase = Phase.PICK_REMOVE
                    self.valid_removals = self.compute_valid_removals()
                    return

        elif self.phase == Phase.PICK_REMOVE:
            if cell_key in self.valid_removals:
                self.removable = cell_key

                # remember whether the removed disc carries a special marker
                self.removed_was_gold = (cell_key == self.gold_disc)
                self.removed_was_silver = (cell_key == self.silver_disc)

                self.occupied.remove(cell_key)

                # temporarily remove marker from old location
                if self.removed_was_gold:
                    self.gold_disc = None
                if self.removed_was_silver:
                    self.silver_disc = None

                self.valid_placements = self.compute_valid_placements()
                self.phase = Phase.PICK_PLACE
                return

        elif self.phase == Phase.PICK_PLACE:
            return
        
        elif self.phase == "GOLD_MOVE_ENEMY":
            opponent = self.opponent_of(self.current)

            idx = self.pawn_index_at(opponent, cell_key)
            if idx is not None:
                if idx in self.gold_movable_enemy_indices:
                    self.gold_selected_enemy_idx = idx
                    self.gold_valid_enemy_moves = self.pawn_moves_from(self.pawns[opponent][idx])
                return

            if self.gold_selected_enemy_idx is not None:
                target = parse_key(cell_key)
                if target in self.gold_valid_enemy_moves:
                    self.pawns[opponent][self.gold_selected_enemy_idx] = target

                    winner = self.check_any_win()
                    if winner is not None:
                        self.winner = winner
                        self.phase = Phase.GAME_OVER
                        return

                    self.finish_turn()
                return

    def click_place(self, pos: Axial):
        if self.phase != Phase.PICK_PLACE:
            return
        cell_key = k(pos)
        if cell_key in self.valid_placements:
            self.occupied.add(cell_key)

            if getattr(self, "removed_was_gold", False):
                self.gold_disc = cell_key
                self.removed_was_gold = False

            if getattr(self, "removed_was_silver", False):
                self.silver_disc = cell_key
                self.removed_was_silver = False

            self.end_turn_after_placement(cell_key)

    def update_timer(self, dt: float):
        if self.last_action_timer > 0:
            self.last_action_timer -= dt
            if self.last_action_timer <= 0:
                self.last_action_text = ""
                self.last_action_timer = 0
        if self.phase == Phase.GAME_OVER:
            return
        self.time_left[self.current] -= dt
        if self.time_left[self.current] <= 0:
            self.time_left[self.current] = 0
            self.winner = "B" if self.current == "A" else "A"
            self.phase = Phase.GAME_OVER
            self.selected_idx = None
            self.valid_moves = []
            self.valid_removals = set()
            self.valid_placements = set()

    def format_time(self, player: str) -> str:
        total = max(0, int(self.time_left[player]))
        minutes = total // 60
        seconds = total % 60
        return f"{minutes:02d}:{seconds:02d}"