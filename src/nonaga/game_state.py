from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from src.nonaga.hexgrid import Axial, DIRS, k, parse_key

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


class NonagaGame:
    def __init__(self):
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
            )
        )
        if len(self.history) > 200:
            self.history.pop(0)

    def undo(self):
        if not self.history:
            return
        h = self.history.pop()
        self.occupied = set(h.occupied)
        self.pawns = {"A": [tuple(p) for p in h.pawns["A"]], "B": [tuple(p) for p in h.pawns["B"]]}
        self.current = h.current
        self.phase = h.phase
        self.selected_idx = h.selected_idx
        self.removable = h.removable
        self.blocked = h.blocked
        self.recompute()

    def reset(self):
        self.history.clear()
        self.occupied.clear()

        # 19 discs = hex radius 2
        for q in range(-2, 3):
            for r in range(-2, 3):
                s = -q - r
                if max(abs(q), abs(r), abs(s)) <= 2:
                    self.occupied.add(k((q, r)))

        corners = [(2, 0), (2, -2), (0, -2), (-2, 0), (-2, 2), (0, 2)]
        self.pawns["A"] = [corners[0], corners[2], corners[4]]
        self.pawns["B"] = [corners[1], corners[3], corners[5]]

        self.current = "A"
        self.phase = Phase.MOVE_PAWN
        self.selected_idx = None
        self.removable = None
        self.blocked = None
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
            while True:
                nq, nr = cq + dq, cr + dr
                if k((nq, nr)) not in self.occupied:
                    break
                if k((nq, nr)) in pawnset:
                    break
                cq, cr = nq, nr
            if (cq, cr) != (q, r):
                moves.append((cq, cr))
        return moves

    def compute_valid_removals(self) -> Set[str]:
        # Approximation: removable if empty, on boundary (missing at least one neighbor), and not blocked
        pawnset = self.pawn_set()
        out: Set[str] = set()

        for cell in self.occupied:
            if cell == self.blocked:
                continue
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
        # brute-force around current cluster bounds
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
                if self.can_place_at((q, r)):
                    out.add(k((q, r)))
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
        return len(seen) == 3

    def end_turn_after_placement(self, placed_key: str):
        self.blocked = None  # opponent can't remove this disc next turn
        self.removable = None
        self.selected_idx = None
        self.valid_moves = []
        self.valid_removals = set()
        self.valid_placements = set()

        if self.is_win(self.current):
            self.phase = Phase.GAME_OVER
            return

        self.current = "B" if self.current == "A" else "A"
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
                    self.snapshot()
                    self.pawns[self.current][self.selected_idx] = target
                    self.selected_idx = None
                    self.valid_moves = []
                    self.phase = Phase.PICK_REMOVE
                    self.valid_removals = self.compute_valid_removals()
                    return

        elif self.phase == Phase.PICK_REMOVE:
            if cell_key in self.valid_removals:
                self.snapshot()
                self.occupied.remove(cell_key)
                self.removable = cell_key
                self.valid_placements = self.compute_valid_placements()
                self.phase = Phase.PICK_PLACE
                return

        elif self.phase == Phase.PICK_PLACE:
            # clicks for placement handled separately (empty cells)
            return

    def click_place(self, pos: Axial):
        if self.phase != Phase.PICK_PLACE:
            return
        cell_key = k(pos)
        if cell_key in self.valid_placements:
            self.snapshot()
            self.occupied.add(cell_key)
            self.end_turn_after_placement(cell_key)