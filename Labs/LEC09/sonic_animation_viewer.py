"""Classic Sonic animation viewer (Python + pico2d)."""

from pathlib import Path

import pico2d as p

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
PREFERRED_SCALE = 6
SOURCE_PATH = Path(__file__).resolve().parent / "sonic-sprite.png"
FIRST_RECT = (0, 39, 30, 39)  # left, top, width, height


def draw_frame(sheet):
    left, top, width, height = FIRST_RECT
    bottom = sheet.h - top - height
    sheet.clip_draw(left, bottom, width, height,
                    CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                    width * PREFERRED_SCALE, height * PREFERRED_SCALE)


def handle_events():
    for event in p.get_events():
        if event.type == p.SDL_QUIT:
            return False
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            return False
    return True


def main():
    p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    p.hide_lattice()
    sheet = p.load_image(str(SOURCE_PATH))
    while handle_events():
        p.clear_canvas()
        draw_frame(sheet)
        p.update_canvas()
        p.delay(0.01)
    p.close_canvas()


if __name__ == "__main__":
    main()
