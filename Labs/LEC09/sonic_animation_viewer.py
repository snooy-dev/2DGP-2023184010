"""Classic Sonic animation viewer (Python + pico2d)."""

import pico2d as p

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600


def main():
    p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    p.clear_canvas()
    p.update_canvas()
    p.close_canvas()


if __name__ == "__main__":
    main()
