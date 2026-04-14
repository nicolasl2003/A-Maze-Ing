from .maze_types import Cell


class Config:
    """Load and validate maze configuration from a KEY=VALUE file.

    Args:
        path: Path to the configuration file.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.

    Example:
        config = Config("config.txt")
    """

    _REQUIRED = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}

    def __init__(self, path: str) -> None:
        """Load config from file and validate all values."""
        raw = self._load(path)
        self._check_required(raw)

        self.width: int = self._int(raw, "WIDTH", min_val=1)
        self.height: int = self._int(raw, "HEIGHT", min_val=1)
        self.output_file: str = self._string(raw, "OUTPUT_FILE")
        self.entry: Cell = self._coord(raw, "ENTRY")
        self.exit_: Cell = self._coord(raw, "EXIT")
        self.perfect: bool = self._bool(raw, "PERFECT")
        self.seed: int | None = (
            self._int(raw, "SEED") if "SEED" in raw else None
        )
        self._validate_bounds()
        self._validate_different()

    def _load(self, path: str) -> dict[str, str]:
        """Read config file, skip comments/blanks, return key→value dict."""
        try:
            result: dict[str, str] = {}
            with open(path) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        raise ValueError(
                            f"line {lineno}: expected KEY=VALUE, got {line!r}"
                        )
                    key, value = line.split("=", maxsplit=1)
                    # Not sure ??? Remove whitespace or no maybe of to check
                    # and raise an error
                    result[key.strip()] = value.strip()
            return result
        except FileNotFoundError:
            raise FileNotFoundError(f"config file not found: {path!r}")

    def _check_required(self, raw: dict[str, str]) -> None:
        """Raise if any required key is missing."""
        missing = self._REQUIRED - raw.keys()
        if missing:
            raise ValueError(
                f"missing required key(s): {', '.join(sorted(missing))}"
            )

    def _int(
        self, raw: dict[str, str], key: str, min_val: int | None = None
    ) -> int:
        """Parse key as integer, optionally with minimum value."""
        try:
            value = int(raw[key])
        except ValueError:
            raise ValueError(f"{key}: expected integer, got {raw[key]!r}")
        if min_val is not None and value < min_val:
            raise ValueError(f"{key}: must be >= {min_val}, got {value!r}")
        return value

    def _bool(self, raw: dict[str, str], key: str) -> bool:
        """Parse key as boolean ('True' or 'False')."""
        value = raw[key]
        if value == "True":
            return True
        if value == "False":
            return False
        raise ValueError(f"{key}: expected 'True' or 'False', got {value!r}")

    def _coord(self, raw: dict[str, str], key: str) -> Cell:
        """Parse key as 'x,y' coordinate tuple."""
        value = raw[key]
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError(f"{key}: expected format 'x,y', got {value!r}")
        try:
            return Cell(int(parts[0].strip()), int(parts[1].strip()))
        except ValueError:
            raise ValueError(
                f"{key}: coordinates must be integers, got {value!r}"
            )

    def _string(self, raw: dict[str, str], key: str) -> str:
        """Return non-empty string value for key."""
        value = raw[key]
        if not value:
            raise ValueError(f"{key}: value must not be empty")
        return value

    def _validate_bounds(self) -> None:
        """
        Ensure entry and exit are inside maze dimensions and validate
        height and width.
        """
        for label, (x, y) in (("ENTRY", self.entry), ("EXIT", self.exit_)):
            if not (0 <= x < self.width):
                raise ValueError(
                    f"{label}: x={x} out of bounds (0..{self.width - 1})"
                )
            if not (0 <= y < self.height):
                raise ValueError(
                    f"{label}: y={y} out of bounds (0..{self.height - 1})"
                )

    def _validate_different(self) -> None:
        """Ensure entry and exit are not the same cell."""
        if self.entry == self.exit_:
            raise ValueError("ENTRY and EXIT must be different cells")

    def __repr__(self) -> str:
        """Return string representation of Config."""
        return (
            f"Config(width={self.width}, height={self.height}, "
            f"entry={self.entry}, exit={self.exit_}, "
            f"perfect={self.perfect}, output_file={self.output_file!r}, "
            f"seed={self.seed})"
        )
