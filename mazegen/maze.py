from random import Random
from .maze_types import Cell, map_type
from .conf import Config
from collections import deque


class Maze:
    """
    Generate and solve perfect mazes using recursive backtracker algorithm.
    """

    def __init__(self, cfg: Config, gen_on_init: bool = True):
        """Initialize maze with configuration."""
        self.width: int = cfg.width
        self.height: int = cfg.height
        self.entry = cfg.entry
        self.exit_ = cfg.exit_
        self.output_file: str = cfg.output_file
        self.__path: list[Cell] | None = None

        self.map_: map_type = self._init_map()
        self.pattern = self._create_pattern()

        self.random = Random(cfg.seed)
        self._DIRS_OFFSETS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        self._DIRECTION_TO_STR = [
            (0, -1, "N"),
            (1, 0, "E"),
            (0, 1, "S"),
            (-1, 0, "W"),
        ]

        if gen_on_init:
            self.gen()

    def __str__(self) -> str:
        """Return string representation of maze in hexadecimal."""
        return "\n".join("".join(f"{c:X}" for c in row) for row in self.map_)

    @property
    def path(self) -> list[Cell] | None:
        """Return the solved path."""
        return self.__path

    def _init_map(self) -> map_type:
        """Initialize maze map with all walls closed."""
        return [[0xF] * self.width for _ in range(self.height)]

    def _create_pattern(self) -> set[Cell]:
        """Create the 42 pattern in center of maze."""
        if self.height < 10 or self.width < 10:
            return set()

        offset_x = self.height // 2 - 2
        offset_y = self.width // 2 - 3

        pattern_42_pos = [
            (0, 0),
            (1, 0),
            (2, 0),
            (2, 1),
            (2, 2),
            (3, 2),
            (4, 2),
            (0, 4),
            (0, 5),
            (0, 6),
            (1, 6),
            (2, 6),
            (2, 5),
            (2, 4),
            (3, 4),
            (4, 4),
            (4, 5),
            (4, 6),
        ]

        cells = {Cell(offset_y + y, offset_x + x) for x, y in pattern_42_pos}

        if self.entry in cells or self.exit_ in cells:
            return set()
        return cells

    def _get_neighbor(self, visited: set[Cell], curr: Cell) -> list[Cell]:
        """Return unvisited neighbours of current cell."""
        neighbor = [
            Cell(curr.x, curr.y - 1),
            Cell(curr.x + 1, curr.y),
            Cell(curr.x, curr.y + 1),
            Cell(curr.x - 1, curr.y),
        ]
        return [
            c
            for c in neighbor
            if 0 <= c.x < self.width
            and 0 <= c.y < self.height
            and c not in visited
        ]

    def _create_wall(self, curr_cell: Cell, next_cell: Cell) -> None:
        """Remove walls between two adjacent cells."""
        dx, dy = next_cell.x - curr_cell.x, next_cell.y - curr_cell.y
        bit = self._DIRS_OFFSETS.index((dx, dy))
        self.map_[curr_cell.y][curr_cell.x] &= ~(1 << bit)
        self.map_[next_cell.y][next_cell.x] &= ~(1 << (bit ^ 2))

    def gen(self) -> None:
        """Generate maze using recursive backtracker algorithm."""
        self.map_ = self._init_map()
        visited: set[Cell] = set()
        stack: list[Cell] = [self.entry]
        visited.add(self.entry)
        visited.update(self.pattern)

        while stack:
            neighbor_available = self._get_neighbor(visited, stack[-1])
            if not neighbor_available:
                stack.pop()
                continue

            next_idx = int(self.random.random() * len(neighbor_available))
            next_cell = neighbor_available[next_idx]
            self._create_wall(stack[-1], next_cell)
            visited.add(next_cell)
            stack.append(next_cell)

        self.__path = self.solver_back()
        self.generate_output()

    @staticmethod
    def direction_maze(cell: int, direction: str) -> bool:
        """Check if direction is open in cell."""
        if direction == "N":
            return not (cell & 1)
        if direction == "E":
            return not (cell & 2)
        if direction == "S":
            return not (cell & 4)
        if direction == "W":
            return not (cell & 8)
        return False

    def can_move(self, x: int, y: int, direction: str) -> bool:
        """Check if move from current position is valid."""
        return self.direction_maze(self.map_[y][x], direction)

    def solver_back(self) -> list[Cell] | None:
        """Find shortest path from entry to exit using BFS."""
        end = (self.exit_.x, self.exit_.y)

        queue: deque[tuple[tuple[int, int], list[Cell]]] = deque()
        queue.append(((self.entry.x, self.entry.y), [self.entry]))

        visited: set[tuple[int, int]] = set()
        visited.add((self.entry.x, self.entry.y))

        while queue:
            node, path = queue.popleft()
            x, y = node

            if (x, y) == end:
                return path

            for dx, dy, d in self._DIRECTION_TO_STR:
                nx, ny = x + dx, y + dy

                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.can_move(x, y, d):
                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append(((nx, ny), path + [Cell(nx, ny)]))
        return None

    @staticmethod
    def path_to_moves(path: list[Cell] | None) -> str:
        """Convert path to string of moves."""
        moves: str = ""

        if path is None:
            raise ValueError("The path is not defined")

        for i in range(1, len(path)):
            x1, y1 = path[i - 1]
            x2, y2 = path[i]

            if x2 == x1 + 1:
                moves += "E"
            elif x2 == x1 - 1:
                moves += "W"
            elif y2 == y1 + 1:
                moves += "S"
            elif y2 == y1 - 1:
                moves += "N"
        return moves

    def generate_output(self) -> None:
        try:
            with open(self.output_file, "w") as f:
                f.write(f"{self.__str__()}\n\n")
                f.write(f"{self.entry.x},{self.entry.y}\n")
                f.write(f"{self.exit_.x},{self.exit_.y}\n")
                f.write(f"{self.path_to_moves(self.__path)}\n")
        except ValueError as e:
            print(f"Failed to write maze to output file: {e}")
