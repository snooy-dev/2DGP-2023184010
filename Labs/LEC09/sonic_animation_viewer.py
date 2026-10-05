"""Classic Sonic animation viewer (Python + pico2d)."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import pico2d as p

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
PREFERRED_SCALE = 6
SOURCE_PATH = Path(__file__).resolve().parent / "sonic-sprite.png"
FPS = 12
REPEAT_COUNT = 5
HOLD_SECONDS = 1.0

# Source catalog: top-left coordinates, 76 Sonic poses in 14 action groups.
# Names describe visible poses; the original sheet has no action labels.
# y=39..77: idle (9), crouch/tuck (2); y=79..117: run (12).
# y=121..163: fast_run (3), skid (3); y=167..199: spin (9).
# y=206..232: spin_stretched (6); y=238..273: dash (6).
# y=283..317: dash_trail (6); y=326..370: turn (6), hurt (2).
# y=377..416: turn_run (8); y=426..468: surprised (2), look_down (2).
# Exclude title y=1..32, credits y>=472, and the two bonus static characters.
# Split touching pixels in row 1 at x=88, 212, 241 rather than merging poses.


@dataclass(frozen=True)
class Frame:
    left: int
    top: int
    width: int
    height: int
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class Action:
    name: str
    frames: tuple[Frame, ...]
    fps: float = FPS


def make_frames(rectangles):
    return tuple(Frame(left, top, width, height, width / 2, height)
                 for left, top, width, height in rectangles)


ACTIONS = (Action("idle", make_frames((
    (1, 39, 29, 39), (31, 40, 26, 38), (58, 39, 30, 39),
    (88, 40, 28, 38), (118, 40, 30, 38), (150, 40, 30, 38),
    (182, 40, 30, 38), (212, 39, 29, 38), (241, 39, 28, 38),
))),)


@dataclass
class Player:
    frame_index: int = 0
    elapsed: float = 0.0
    completed_repeats: int = 0
    state: str = "PLAYING"


def next_frame(player):
    if player.frame_index == len(ACTIONS[0].frames) - 1:
        player.completed_repeats += 1
        if player.completed_repeats == REPEAT_COUNT:
            player.state = "HOLDING"
            return
    player.frame_index = (player.frame_index + 1) % len(ACTIONS[0].frames)


def advance(player, dt):
    player.elapsed += dt
    while player.state != "FINISHED":
        interval = HOLD_SECONDS if player.state == "HOLDING" else 1 / ACTIONS[0].fps
        if player.elapsed < interval:
            return
        player.elapsed -= interval
        if player.state == "HOLDING":
            player.state = "FINISHED"
        else:
            next_frame(player)


def draw_frame(sheet, frame):
    bottom = sheet.h - frame.top - frame.height
    sheet.clip_draw(frame.left, bottom, frame.width, frame.height,
                    CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                    frame.width * PREFERRED_SCALE, frame.height * PREFERRED_SCALE)


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
    player = Player()
    previous = perf_counter()
    while handle_events():
        now = perf_counter()
        advance(player, now - previous)
        previous = now
        p.clear_canvas()
        draw_frame(sheet, ACTIONS[0].frames[player.frame_index])
        p.update_canvas()
        p.delay(0.01)
    p.close_canvas()


if __name__ == "__main__":
    main()
