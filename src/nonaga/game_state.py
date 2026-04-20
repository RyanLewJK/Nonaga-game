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


class NonagaGame:
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config if config is not None else classic_config()

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

        self.control_targets: Set[str] = set()
        self.survival_turn_count = 0

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
            self.phase = Phase.PICK_REMOVE
            self.valid_placements = set()
            self.valid_removals = self.compute_valid_removals()
            self.removable = None
            return

    def _board_radius(self) -> int:
        return self.config.board_radius

    def _initial_time(self) -> float:
        if self.config.turn_time_limit is not None:
            return float(self.config.turn_time_limit)
        return 300.0

    def _initial_pawns(self) -> Dict[str, List[Axial]]:
        if self.config.board_radius == 2:
            corners = [(2, 0), (2, -2), (0, -2), (-2, 0), (-2, 2), (0, 2)]
            return {
                "A": [corners[0], corners[2], corners[4]],
                "B": [corners[1], corners[3], corners[5]],
            }

        if self.config.board_radius == 3:
            corners = [(3, 0), (3, -3), (0, -3), (-3, 0), (-3, 3), (0, 3)]
            return {
                "A": [corners[0], corners[2], corners[4], (-1, -2)],
                "B": [corners[1], corners[3], corners[5], (1, 2)],
            }

        corners = [(2, 0), (2, -2), (0, -2), (-2, 0), (-2, 2), (0, 2)]
        return {
            "A": [corners[0], corners[2], corners[4]],
            "B": [corners[1], corners[3], corners[5]],
        }

    def _setup_control_targets(self):
        self.control_targets.clear()

        if not self.config.control_mode:
            return

        if self.config.board_radius == 2:
            targets = [(0, 0), (1, -1), (-1, 1)]
        else:
            targets = [(0, 0), (1, -1), (-1, 1), (1, 0)]

        self.control_targets = {k(t) for t in targets}

    def count_controlled_targets(self, player: str) -> int:
        pawn_keys = {k(p) for p in self.pawns[player]}
        return sum(1 for cell in self.control_targets if cell in pawn_keys)

    def reset(self):
        self.history.clear()
        self.occupied.clear()

        radius = self._board_radius()

        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if max(abs(q), abs(r), abs(s)) <= radius:
                    self.occupied.add(k((q, r)))

        self.pawns = self._initial_pawns()

        self.current = "A"
        self.phase = Phase.MOVE_PAWN
        self.selected_idx = None
        self.removable = None
        self.blocked = None
        self.time_left = {"A": self._initial_time(), "B": self._initial_time()}
        self.winner = None
        self.survival_turn_count = 0

        self._setup_control_targets()
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

    def check_control_win(self) -> Optional[str]:
        if not self.config.control_mode:
            return None

        required = self.config.control_required
        if self.count_controlled_targets("A") >= required:
            return "A"
        if self.count_controlled_targets("B") >= required:
            return "B"

        return None

    def check_survival_win(self) -> Optional[str]:
        if not self.config.survival_mode:
            return None

        if self.config.survival_turns is None:
            return None

        # currently assumes human is A
        if self.survival_turn_count >= self.config.survival_turns:
            return "A"

        return None

    def check_any_win(self) -> Optional[str]:
        if self.is_win("A"):
            return "A"
        if self.is_win("B"):
            return "B"

        winner = self.check_control_win()
        if winner is not None:
            return winner

        winner = self.check_survival_win()
        if winner is not None:
            return winner

        return None

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

        previous_player = self.current
        self.current = "B" if self.current == "A" else "A"

        if self.config.survival_mode and previous_player == "A":
            self.survival_turn_count += 1
            winner = self.check_survival_win()
            if winner is not None:
                self.winner = winner
                self.phase = Phase.GAME_OVER
                return

        self.phase = Phase.MOVE_PAWN
        self.recompute()

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

            if self.selected_idx is not None:
                target = parse_key(cell_key)
                if target in self.valid_moves:
                    self.pawns[self.current][self.selected_idx] = target
                    self.selected_idx = None
                    self.valid_moves = []
                    self.phase = Phase.PICK_REMOVE
                    self.valid_removals = self.compute_valid_removals()
                    return

        elif self.phase == Phase.PICK_REMOVE:
            if cell_key in self.valid_removals:
                self.occupied.remove(cell_key)
                self.removable = cell_key
                self.valid_placements = self.compute_valid_placements()
                self.phase = Phase.PICK_PLACE
                return

        elif self.phase == Phase.PICK_PLACE:
            return

    def click_place(self, pos: Axial):
        if self.phase != Phase.PICK_PLACE:
            return
        cell_key = k(pos)
        if cell_key in self.valid_placements:
            self.occupied.add(cell_key)
            self.end_turn_after_placement(cell_key)

    def update_timer(self, dt: float):
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