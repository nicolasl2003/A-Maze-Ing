import readchar
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
import queue
import threading

from mazegen import Maze
from mazegen import Cell, DIRECTION


class TUIRenderer:
    """Terminal UI renderer for A-Maze-ing."""

    def __init__(self, maze: Maze) -> None:
        """Initialize renderer with maze."""
        self._console = Console()
        self._maze = maze

        self._PALETTES: list[tuple[str, str]] = [
            ("bright_white", "Classic"),
            ("cyan", "Ocean"),
            ("yellow", "Gold"),
            ("magenta", "Neon"),
            ("bright_green", "Matrix"),
        ]

        self._WALL = "██"
        self._PATH = "  "
        self._PATH_MARKER = "██"

        self.__palette_idx: int = 0
        self.__v_offset: int = 0
        self.__view_height: int = 1
        self.__running: bool = True
        self.__status: str = "Ready"

        self.__dirty: bool = True
        self.__row_cache: list[Text] | None = None
        self.__cache_color: str = ""
        self.__show_path: bool = False
        self.__last_size:  tuple[int, int] = 0, 0

        self.__key_queue: queue.Queue[str] = queue.Queue()

    def run(self) -> None:
        """Start the blocking render + input loop."""
        threading.Thread(target=self.__read_keys, daemon=True).start()

        with Live(
            self._build_renderable(),
            console=self._console,
            screen=True,
            vertical_overflow="visible",
        ) as live:
            while self.__running:
                try:
                    key = self.__key_queue.get(timeout=0.1)
                    while not self.__key_queue.empty():
                        key = self.__key_queue.get_nowait()
                    self._handle_key(key)
                    self.__dirty = True
                except queue.Empty:
                    pass
                size = (self._console.size.width, self._console.size.height)
                if self.__dirty or size != self.__last_size:
                    live.update(self._build_renderable())
                    self.__last_size = size
                    self.__dirty = False

    def __read_keys(self) -> None:
        """Read keys in background thread."""
        while self.__running:
            try:
                key = readchar.readkey()
                self.__key_queue.put(key)
            except (KeyboardInterrupt, EOFError):
                self.__running = False
                break

    def _handle_key(self, key: str) -> None:
        """Handle keyboard input."""
        match key:
            case "r" | "R":
                self.__status = "Generating..."
                self._maze.gen()
                self.__v_offset = 0
                self.__row_cache = None
                self.__status = "New maze generated"
            case "p" | "P":
                self.__show_path = not self.__show_path
                self.__row_cache = None
                self.__status = "Path ON" if self.__show_path else "Path OFF"
            case "w" | "W" | readchar.key.UP:
                self.__v_offset = max(0, self.__v_offset - 1)
            case "s" | "S" | readchar.key.DOWN:
                max_scroll = max(
                    0, 2 * self._maze.height + 1 - self.__view_height
                )
                self.__v_offset = min(max_scroll, self.__v_offset + 1)
            case "c" | "C":
                self.__palette_idx = (self.__palette_idx + 1) % len(
                    self._PALETTES
                )
                self.__row_cache = None
                self.__status = (
                    f"Color -> {self._PALETTES[self.__palette_idx][1]}"
                )
            case "q" | "Q" | "\x03" | readchar.key.CTRL_C:
                self.__running = False

    def _build_renderable(self) -> Panel:
        """Build the main renderable panel."""
        color, _ = self._PALETTES[self.__palette_idx]
        width = self._console.size.width
        height = self._console.size.height
        self.__view_height = max(1, height - 9)
        needed = 2 * (2 * self._maze.width + 1) + 10

        inner = (
            self._render_too_narrow(width, needed)
            if width < needed
            else Group(
                self._render_maze(color), Text(""), self._render_menu(color)
            )
        )
        return Panel(
            inner,
            title=f"[bold {color}]A-Maze-ing[/]",
            subtitle=f"[dim italic]{self.__status}[/]",
            border_style=color,
            padding=(1, 4),
            expand=False,
        )

    @staticmethod
    def _render_too_narrow(got: int, need: int) -> Group:
        """Render warning when terminal is too narrow."""
        return Group(
            Text(""),
            Text(
                "⚠  terminal too narrow", justify="center", style="bold red"
            ),
            Text("─" * 28, justify="center", style="dim red"),
            Text(""),
            Text(f"need   {need} cols", justify="center", style="dim"),
            Text(f"got    {got} cols", justify="center", style="dim"),
            Text(
                f"short  {need - got} cols",
                justify="center",
                style="bold yellow",
            ),
            Text(""),
            Text(
                "resize your terminal or lower WIDTH",
                justify="center",
                style="dim italic",
            ),
            Text(""),
        )

    def _render_maze(self, color: str) -> Text:
        """Render the maze with optional path."""
        if self.__row_cache is None or self.__cache_color != color:
            self.__row_cache = self._build_row_cache(color)
            self.__cache_color = color

        visible = self.__row_cache[
            self.__v_offset: self.__v_offset + self.__view_height
        ]
        out = Text(justify="center")
        for i, row in enumerate(visible):
            out.append_text(row)
            if i < len(visible) - 1:
                out.append("\n")
        return out

    def _build_row_cache(self, color: str) -> list[Text]:
        """Build cached rows for maze rendering with continuous pathing."""
        W, H = self._maze.width, self._maze.height

        current_path = self._maze.path if self.__show_path else None
        path_set = (
            {(c.x, c.y) for c in current_path} if current_path else set()
        )

        s = {
            "wall": Style(color=color),
            "blue": Style(color="blue", bold=True),
            "green": Style(color="green", bold=True),
            "red": Style(color="red", bold=True),
            "path": Style(color="dark_sea_green2", blink=True),
        }

        WALL_CELL: tuple[str, Style] = (self._WALL, s["wall"])
        PATH_CELL: tuple[str, Style | None] = (self._PATH, None)
        SOLVED_CELL: tuple[str, Style] = (self._PATH_MARKER, s["path"])
        PATTERN_CELL: tuple[str, Style] = (self._WALL, s["blue"])

        ascii_map: list[list[tuple[str, Style | None]]] = [
            [WALL_CELL] * (2 * W + 1) for _ in range(2 * H + 1)
        ]

        def get_connector_cell(
            curr_pos: tuple[int, int], next_pos: tuple[int, int]
        ) -> tuple[str, Style | None]:
            if curr_pos in path_set and next_pos in path_set:
                return SOLVED_CELL
            return PATH_CELL

        for y in range(H):
            for x in range(W):
                cell_hex: int = self._maze.map_[y][x]
                in_path = (x, y) in path_set

                if Cell(x, y) in self._maze.pattern:
                    ascii_map[2 * y + 1][2 * x + 1] = PATTERN_CELL
                elif in_path:
                    ascii_map[2 * y + 1][2 * x + 1] = SOLVED_CELL
                else:
                    ascii_map[2 * y + 1][2 * x + 1] = PATH_CELL

                if not (cell_hex & DIRECTION.NORTH.value):
                    ascii_map[2 * y][2 * x + 1] = get_connector_cell(
                        (x, y), (x, y - 1)
                    )
                if not (cell_hex & DIRECTION.EAST.value):
                    ascii_map[2 * y + 1][2 * x + 2] = get_connector_cell(
                        (x, y), (x + 1, y)
                    )
                if not (cell_hex & DIRECTION.SOUTH.value):
                    ascii_map[2 * y + 2][2 * x + 1] = get_connector_cell(
                        (x, y), (x, y + 1)
                    )
                if not (cell_hex & DIRECTION.OUEST.value):
                    ascii_map[2 * y + 1][2 * x] = get_connector_cell(
                        (x, y), (x - 1, y)
                    )

        ex, ey = self._maze.entry.x, self._maze.entry.y
        ascii_map[2 * ey + 1][2 * ex + 1] = (self._WALL, s["green"])
        ex, ey = self._maze.exit_.x, self._maze.exit_.y
        ascii_map[2 * ey + 1][2 * ex + 1] = (self._WALL, s["red"])

        rows = []
        for row in ascii_map:
            t = Text(justify="center")
            for char, style in row:
                t.append(char, style=style)
            rows.append(t)
        return rows

    def _render_menu(self, color: str) -> Table:
        """Render the control menu."""
        table = Table.grid(expand=False, padding=(0, 3))
        for _ in range(4):
            table.add_column(justify="center")
        path_status = "Path ON" if self.__show_path else "Path OFF"
        table.add_row(
            self._key("R", "Regen", color),
            self._key("P", path_status, color),
            self._key("C", self._PALETTES[self.__palette_idx][1], color),
            self._key("Q", "Quit", color),
        )
        return table

    @staticmethod
    def _key(k: str, label: str, color: str) -> Text:
        """Render a key label."""
        t = Text()
        t.append(f" {k} ", style=f"bold black on {color}")
        t.append(f" {label}", style="dim")
        return t
