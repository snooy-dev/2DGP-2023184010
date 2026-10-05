"""Classic Sonic viewer. Optional verification: --trace --cycles 2."""

import argparse
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import sys
from time import perf_counter

try:
    import pico2d as p
except ImportError:
    print("pico2d is required. Install it with: python -m pip install pico2d", file=sys.stderr)
    raise SystemExit(1)

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
PREFERRED_SCALE = 6
MARGIN = 36
SOURCE_PATH = Path(__file__).resolve().parent / "sonic-sprite.png"
FPS = 12
REPEAT_COUNT = 5
HOLD_SECONDS = 1.0
TIME_EPSILON = 1e-10

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


def make_frames(rectangles, baseline=None, pivots=None):
    # Preserve each pose's vertical offset within its original source row.
    baseline = max(top + height for _, top, _, height in rectangles) if baseline is None else baseline
    return tuple(Frame(left, top, width, height,
                       pivots[i] if pivots is not None else width / 2,
                       baseline - top)
                 for i, (left, top, width, height) in enumerate(rectangles))


ACTIONS = (
    Action("idle", make_frames((
        (1, 39, 29, 39), (31, 40, 26, 38), (58, 39, 30, 39),
        (88, 40, 28, 38), (118, 40, 30, 38), (150, 40, 30, 38),
        (182, 40, 30, 38), (212, 39, 29, 38), (241, 39, 28, 38),
    ), baseline=78, pivots=(15, 13, 14, 14, 16, 16, 16, 15, 14))),
    Action("crouch", make_frames(((270, 45, 24, 32), (302, 51, 29, 26)), baseline=78)),
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
        (99, 377, 33, 38), (136, 379, 32, 36), (176, 379, 33, 36),
        (217, 379, 33, 36), (254, 378, 33, 36),
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
    timeline: float = 0.0


def start_action(player, action_index):
    player.action_index = action_index
    player.frame_index = 0
    player.completed_repeats = 0
    player.state = "PLAYING"
    player.elapsed = 0.0


def next_frame(player, emit=None):
    action = ACTIONS[player.action_index]
    if player.frame_index == len(action.frames) - 1:
        player.completed_repeats += 1
        if emit:
            emit("repeat", player)
        if player.completed_repeats == REPEAT_COUNT:
            player.state = "HOLDING"
            if emit:
                emit("hold", player)
            return
    player.frame_index = (player.frame_index + 1) % len(action.frames)


def advance(player, dt, emit=None):
    if not isfinite(dt) or dt < 0:
        raise ValueError("Elapsed time must be finite and nonnegative")
    player.elapsed += dt
    while True:
        interval = HOLD_SECONDS if player.state == "HOLDING" else 1 / ACTIONS[player.action_index].fps
        if player.elapsed + TIME_EPSILON < interval:
            return
        player.elapsed = max(0.0, player.elapsed - interval)
        player.timeline += interval
        if player.state == "HOLDING":
            next_index = (player.action_index + 1) % len(ACTIONS)
            if next_index == 0:
                player.cycles += 1
            remaining = player.elapsed
            start_action(player, next_index)
            player.elapsed = remaining
            if emit:
                emit("action", player)
        else:
            next_frame(player, emit)


def action_layout(action):
    left = max(f.pivot_x for f in action.frames)
    right = max(f.width - f.pivot_x for f in action.frames)
    top = max(f.pivot_y for f in action.frames)
    bottom = max(f.height - f.pivot_y for f in action.frames)
    scale = min(PREFERRED_SCALE,
                (CANVAS_WIDTH - 2 * MARGIN) / (left + right),
                (CANVAS_HEIGHT - 2 * MARGIN) / (top + bottom))
    return ((CANVAS_WIDTH + (left - right) * scale) / 2,
            (CANVAS_HEIGHT + (bottom - top) * scale) / 2, scale)


def draw_frame(sheet, frame, layout):
    bottom = sheet.h - frame.top - frame.height
    anchor_x, anchor_y, scale = layout
    x = anchor_x + (frame.width / 2 - frame.pivot_x) * scale
    y = anchor_y + (frame.pivot_y - frame.height / 2) * scale
    sheet.clip_draw(frame.left, bottom, frame.width, frame.height,
                    x, y, frame.width * scale, frame.height * scale)


def handle_events():
    for event in p.get_events():
        if event.type == p.SDL_QUIT:
            return False
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            return False
    return True


def validate_actions(sheet):
    if not ACTIONS:
        raise ValueError("No animation actions registered")
    for action in ACTIONS:
        if not action.frames or not isfinite(action.fps) or action.fps <= 0:
            raise ValueError(f"Invalid frames or FPS: {action.name}")
        for frame in action.frames:
            if (frame.width <= 0 or frame.height <= 0
                    or frame.left < 0 or frame.top < 0
                    or frame.left + frame.width > sheet.w
                    or frame.top + frame.height > sheet.h
                    or not isfinite(frame.pivot_x) or not isfinite(frame.pivot_y)):
                raise ValueError(f"Invalid source frame: {action.name}: {frame}")


def trace_event(kind, player):
    print(f"{player.timeline:10.6f} {kind:6} "
          f"action={ACTIONS[player.action_index].name} "
          f"repeat={player.completed_repeats} frame={player.frame_index} "
          f"cycle={player.cycles}", flush=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", action="store_true", help="Log action, repeat and hold boundaries")
    parser.add_argument("--cycles", type=int, help="Exit after N full cycles (default: infinite)")
    parser.add_argument("--seconds", type=float, help="Exit after N seconds for a rendering smoke check")
    args = parser.parse_args(argv)
    if args.cycles is not None and args.cycles <= 0:
        parser.error("--cycles must be positive")
    if args.seconds is not None and (not isfinite(args.seconds) or args.seconds <= 0):
        parser.error("--seconds must be finite and positive")
    return args


def main(argv=None):
    args = parse_args(argv)
    if not SOURCE_PATH.is_file():
        print(f"Sprite image not found: {SOURCE_PATH}. Place sonic-sprite.png beside this script.", file=sys.stderr)
        return 1
    opened = False
    try:
        p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
        opened = True
        p.hide_lattice()
        sheet = p.load_image(str(SOURCE_PATH))
        validate_actions(sheet)
        layouts = tuple(action_layout(action) for action in ACTIONS)
        player = Player()
        emit = trace_event if args.trace else None
        if emit:
            emit("action", player)
        started = previous = perf_counter()
        while handle_events():
            now = perf_counter()
            if args.seconds is not None and now - started >= args.seconds:
                break
            advance(player, now - previous, emit)
            previous = now
            if args.cycles is not None and player.cycles >= args.cycles:
                break
            p.clear_canvas()
            draw_frame(sheet, ACTIONS[player.action_index].frames[player.frame_index],
                       layouts[player.action_index])
            p.update_canvas()
            p.delay(0.01)
    except (OSError, ValueError) as error:
        print(f"Cannot start viewer with {SOURCE_PATH}: {str(error) or 'image load failed'}. "
              "Check the PNG file and animation data.", file=sys.stderr)
        return 1
    finally:
        if opened:
            p.close_canvas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
