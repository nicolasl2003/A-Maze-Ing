import sys

from src.tui_render import TUIRenderer
from mazegen import Config
from mazegen import Maze


def main() -> None:
    if len(sys.argv) < 2:
        print("File argument not found!\nUsage: a_maze_ing.py config.txt")
        sys.exit(1)
    try:
        cfg = Config(sys.argv[1])
    except (ValueError, FileNotFoundError) as e:
        print(f"Error during parsing: {e}")
        return
    m = Maze(cfg)
    renderer = TUIRenderer(m)
    renderer.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Unexpected error: {e}")
