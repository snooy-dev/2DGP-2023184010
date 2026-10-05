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


ACTIONS = (
    Action("idle", make_frames((
        (1, 39, 29, 39), (31, 40, 26, 38), (58, 39, 30, 39),
        (88, 40, 28, 38), (118, 40, 30, 38), (150, 40, 30, 38),
        (182, 40, 30, 38), (212, 39, 29, 38), (241, 39, 28, 38),
    ))),
    Action("crouch", make_frames(((270, 45, 24, 32), (302, 51, 29, 26)))),
    Action("run", make_frames((
        (8, 80, 26, 37), (37, 80, 27, 37), (65, 80, 31, 38),
        (97, 80, 37, 37), (135, 80, 32, 35), (170, 79, 32, 38),
        (206, 79, 26, 38), (238, 80, 24, 37), (263, 80, 30, 37),
        (295, 80, 36, 37), (334, 80, 32, 36), (370, 79, 29, 38),
    ))),
    Action("fast_run", make_frames((
        (1, 124, 33, 40), (39, 124, 35, 39), (89, 125, 35, 38),
    ))),
    Action("skid", make_frames((
        (130, 121, 34, 42), (181, 122, 34, 41), (228, 122, 33, 40),
    ))),
    Action("spin", make_frames((
        (1, 169, 29, 30), (35, 167, 29, 31), (67, 169, 30, 29),
        (98, 169, 31, 29), (131, 168, 29, 30), (162, 168, 29, 31),
        (193, 170, 30, 29), (230, 170, 31, 29), (268, 170, 30, 30),
    ))),
    Action("spin_stretched", make_frames((
        (1, 206, 30, 27), (36, 206, 29, 27), (70, 206, 29, 27),
        (105, 206, 29, 27), (139, 206, 29, 27), (174, 206, 29, 27),
    ))),
    Action("dash", make_frames((
        (1, 239, 29, 35), (36, 239, 30, 35), (74, 239, 31, 35),
        (111, 238, 31, 36), (149, 239, 30, 35), (186, 238, 31, 36),
    ))),
    Action("dash_trail", make_frames((
        (1, 283, 29, 35), (36, 283, 30, 35), (72, 286, 39, 31),
        (123, 285, 39, 32), (172, 286, 39, 31), (218, 285, 38, 32),
    ))),
    Action("turn", make_frames((
        (1, 326, 24, 45), (31, 327, 29, 44), (65, 327, 20, 44),
        (90, 327, 25, 43), (119, 327, 25, 43), (149, 327, 20, 44),
    ))),
    Action("hurt", make_frames(((184, 341, 40, 28), (232, 341, 39, 27)))),
    Action("turn_run", make_frames((
        (1, 379, 27, 38), (31, 379, 31, 36), (64, 379, 31, 36),
        (99, 378, 33, 37), (136, 379, 32, 36), (176, 379, 33, 36),
        (217, 379, 33, 36), (254, 377, 33, 37),
    ))),
    Action("surprised", make_frames(((6, 429, 34, 40), (49, 426, 34, 43)))),
    Action("look_down", make_frames(((96, 427, 23, 39), (125, 427, 23, 39)))),
)


@dataclass
class Player:
    action_index: int = 0
    frame_index: int = 0
    elapsed: float = 0.0
    completed_repeats: int = 0
    state: str = "PLAYING"
    cycles: int = 0


def start_action(player, action_index):
    player.action_index = action_index
    player.frame_index = 0
    player.completed_repeats = 0
    player.state = "PLAYING"
    player.elapsed = 0.0


def next_frame(player):
    action = ACTIONS[player.action_index]
    if player.frame_index == len(action.frames) - 1:
        player.completed_repeats += 1
        if player.completed_repeats == REPEAT_COUNT:
            player.state = "HOLDING"
            return
    player.frame_index = (player.frame_index + 1) % len(action.frames)


def advance(player, dt):
    player.elapsed += dt
    while True:
        interval = HOLD_SECONDS if player.state == "HOLDING" else 1 / ACTIONS[player.action_index].fps
        if player.elapsed < interval:
            return
        player.elapsed -= interval
        if player.state == "HOLDING":
            next_index = (player.action_index + 1) % len(ACTIONS)
            if next_index == 0:
                player.cycles += 1
            remaining = player.elapsed
            start_action(player, next_index)
            player.elapsed = remaining
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
        draw_frame(sheet, ACTIONS[player.action_index].frames[player.frame_index])
        p.update_canvas()
        p.delay(0.01)
    p.close_canvas()


if __name__ == "__main__":
    main()
