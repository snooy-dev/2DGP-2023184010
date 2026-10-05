"""Classic Sonic animation viewer (Python + pico2d)."""

from pathlib import Path

import pico2d as p

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
PREFERRED_SCALE = 6
SOURCE_PATH = Path(__file__).resolve().parent / "sonic-sprite.png"
FIRST_RECT = (0, 39, 30, 39)  # left, top, width, height

# Source catalog: top-left coordinates, 76 Sonic poses in 14 action groups.
# Names describe visible poses; the original sheet has no action labels.
# y=39..77: idle (9), crouch/tuck (2); y=79..117: run (12).
# y=121..163: fast_run (3), skid (3); y=167..199: spin (9).
# y=206..232: spin_stretched (6); y=238..273: dash (6).
# y=283..317: dash_trail (6); y=326..370: turn (6), hurt (2).
# y=377..416: turn_run (8); y=426..468: surprised (2), look_down (2).
# Exclude title y=1..32, credits y>=472, and the two bonus static characters.
# Split touching pixels in row 1 at x=88, 212, 241 rather than merging poses.


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
