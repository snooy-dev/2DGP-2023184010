"""Drill #8: Hornet, rendered directly from the unchanged original sheet.

Run with Python and pico2d. All frame data and viewer code live in this file.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "assets" / "source" / "hornet_original.png"
SOURCE_SIZE = (2393, 13086)
SOURCE_SHA256 = "0bcedf01ef61f1b2482cd76afed1f76435aa43f899b0e87242c283322997b02f"
CANVAS_WIDTH, CANVAS_HEIGHT = 960, 720


@dataclass(frozen=True)
class Frame:
    """One source rectangle and its local anchor; no new image is created."""
    source_label: str
    rect: tuple[int, int, int, int]
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class Action:
    label: str
    phases: tuple[tuple[str, tuple[str, ...]], ...]
    fps: float = 12.0
    duration_overrides: tuple[tuple[int, float], ...] = ()

    @property
    def frames(self):
        return tuple(frame_id for _, frames in self.phases for frame_id in frames)

    @property
    def durations(self):
        overrides = dict(self.duration_overrides)
        return tuple(overrides.get(i, 1 / self.fps) for i in range(len(self.frames)))


# left, top, width, height, pivot_x, pivot_y; top-left source coordinates.
# Measured from the unchanged sheet, including every nonzero-alpha pixel.
SOURCE_FRAMES = {
    "air_dash_recover": (
        (551, 4374, 196, 183, 98.5, 199),
        (756, 4367, 160, 199, 93.5, 206),
        (958, 4368, 157, 205, 91.5, 205),
        (1155, 4367, 161, 202, 94.5, 206),
        (1361, 4368, 155, 201, 88.5, 205),
    ),
    "air_dash": (
        (3, 4368, 254, 136, 127.5, 136),
        (263, 4370, 251, 134, 125.5, 134),
    ),
    "air_dash_anticipate": (
        (3, 4147, 203, 195, 116, 198),
        (242, 4168, 204, 166, 112, 177),
        (495, 4193, 205, 152, 94, 152),
        (723, 4188, 205, 156, 101, 157),
        (958, 4188, 205, 157, 101, 157),
        (1193, 4188, 205, 152, 101, 157),
        (1428, 4188, 205, 156, 101, 157),
        (1663, 4188, 205, 157, 101, 157),
        (1908, 4190, 205, 144, 91, 155),
    ),
    "ground_dash_recover": (
        (630, 2864, 200, 123, 66.5, 123),
        (928, 2850, 203, 137, 62.5, 137),
        (1224, 2850, 204, 137, 60.5, 137),
        (1499, 2837, 205, 149, 79.5, 150),
        (1740, 2799, 196, 187, 132.5, 188),
        (2021, 2779, 192, 207, 145.5, 208),
    ),
    "ground_dash": (
        (3, 2780, 254, 136, 127.5, 136),
        (263, 2782, 251, 134, 125.5, 134),
    ),
    "ground_dash_anticipate": (
        (3, 2369, 203, 189, 138, 192),
        (315, 2401, 204, 156, 105, 160),
        (631, 2426, 205, 135, 68, 135),
        (903, 2421, 205, 137, 75, 140),
        (1182, 2421, 205, 137, 75, 140),
        (1461, 2421, 205, 137, 75, 140),
        (1740, 2421, 205, 137, 75, 140),
        (2019, 2421, 205, 137, 75, 140),
        (66, 2617, 205, 137, 75, 140),
        (348, 2626, 205, 128, 72, 131),
    ),
    "evade": (
        (1155, 2130, 191, 210, 94, 210),
        (1350, 2130, 192, 205, 98, 210),
        (1549, 2129, 191, 210, 98, 211),
    ),
    "evade_anticipate": (
        (555, 2132, 176, 214, 92.5, 214),
        (743, 2129, 184, 216, 92.5, 217),
        (936, 2146, 174, 200, 87.5, 200),
    ),
    "wall_impact": (
        (3, 2132, 109, 209, 63.5, 209),
        (133, 2128, 125, 205, 63.5, 213),
        (263, 2128, 125, 206, 63.5, 213),
        (393, 2128, 123, 207, 63.5, 213),
    ),
    "hard_land": (
        (668, 1941, 183, 155, 88.5, 165),
        (877, 1942, 192, 156, 89.5, 164),
        (1073, 1941, 201, 163, 103.5, 165),
        (1283, 1930, 202, 176, 103.5, 176),
    ),
    "land": (
        (11, 1917, 194, 177, 93.5, 178),
        (209, 1908, 195, 187, 101.5, 187),
        (425, 1878, 189, 216, 91.5, 217),
    ),
    "jump": (
        (49, 1650, 136, 205, 48, 205),
        (243, 1651, 127, 204, 45, 204),
        (447, 1651, 115, 202, 32, 204),
        (622, 1638, 132, 191, 48, 217),
        (767, 1633, 187, 195, 94, 222),
        (978, 1626, 160, 199, 74, 229),
        (1171, 1627, 157, 205, 72, 228),
        (1359, 1626, 161, 202, 75, 229),
        (1556, 1627, 155, 201, 69, 228),
    ),
    "jump_anticipate": (
        (18, 1441, 183, 155, 88.5, 163),
        (227, 1442, 192, 156, 89.5, 162),
        (423, 1441, 201, 163, 103.5, 163),
        (680, 1405, 143, 192, 56.5, 199),
    ),
    "flourish": (
        (46, 79, 183, 215, 136, 244),
        (404, 117, 194, 177, 139, 206),
        (757, 108, 195, 187, 147, 215),
        (1123, 92, 191, 201, 142, 231),
        (1507, 102, 176, 189, 119, 221),
        (1902, 99, 148, 193, 85, 224),
        (3, 400, 232, 227, 179, 227),
        (384, 430, 319, 166, 159, 197),
        (745, 385, 297, 211, 159, 242),
        (1106, 356, 268, 240, 159, 271),
        (1467, 327, 336, 269, 159, 300),
        (1828, 405, 331, 191, 159, 222),
        (23, 647, 240, 253, 159, 284),
        (396, 716, 195, 187, 147, 215),
    ),
    "run": (
        (8, 1195, 154, 185, 74.5, 187),
        (170, 1194, 153, 174, 74.5, 188),
        (333, 1195, 149, 186, 73.5, 187),
        (489, 1192, 158, 190, 79.5, 190),
        (656, 1195, 154, 186, 74.5, 187),
        (818, 1194, 153, 174, 74.5, 188),
        (981, 1196, 149, 184, 73.5, 186),
        (1137, 1193, 158, 188, 79.5, 189),
    ),
    "idle": (
        (3, 954, 183, 215, 92, 215),
        (190, 954, 183, 215, 92, 215),
        (378, 954, 182, 215, 91, 215),
        (565, 955, 181, 214, 91, 214),
        (752, 954, 181, 215, 91, 215),
        (938, 954, 182, 215, 92, 215),
    ),
}
FRAME_RECTS = {
    f"{phase}:{i}": Frame(phase, values[:4], *values[4:])
    for phase, frames in SOURCE_FRAMES.items()
    for i, values in enumerate(frames)
}


def phase(name, indexes=None):
    """References may reuse a rectangle, including reverse recovery frames."""
    indexes = range(len(SOURCE_FRAMES[name])) if indexes is None else indexes
    return name, tuple(f"{name}:{i}" for i in indexes)


ACTIONS = {
    "air_dash": Action("Air Dash", (phase("air_dash_anticipate"), phase("air_dash"), phase("air_dash_recover"))),
    "ground_dash": Action("Ground Dash", (phase("ground_dash_anticipate"), phase("ground_dash"), phase("ground_dash_recover"))),
    "wall_impact": Action("Wall Impact", (phase("wall_impact"),)),
    "evade": Action("Evade", (phase("evade_anticipate"), phase("evade"))),
    "jump": Action("Jump", (phase("jump_anticipate"), phase("jump"), phase("land"))),
    "hard_land": Action("Hard Land", (phase("hard_land"), phase("land", (1, 2)))),
    "flourish": Action("Flourish", (phase("flourish"),), fps=12),
    "idle": Action("Idle", (phase("idle"),), fps=8),
    "run": Action("Run", (phase("run"),), fps=14),
}
ACTION_ORDER = tuple(ACTIONS)


def draw_source(sheet, rect, scale=1.8):
    """Convert a top-origin source rectangle to Pico2d's bottom origin."""
    left, top, width, height = rect
    sheet.clip_draw(left, sheet.h - top - height, width, height,
                    CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                    width * scale, height * scale)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect", choices=ACTION_ORDER,
                        help="Freeze an action and inspect its original frame")
    parser.add_argument("--frame", type=int, default=0,
                        help="Zero-based frame for --inspect")
    parser.add_argument("--source-top", type=int,
                        help="Inspect an unmodified 960x720 region of the source sheet")
    parser.add_argument("--seconds", type=float,
                        help="Close after this many seconds (rendering smoke checks)")
    args = parser.parse_args(argv)
    if args.seconds is not None and args.seconds <= 0:
        parser.error("--seconds must be positive")
    if args.source_top is not None and not 0 <= args.source_top < SOURCE_SIZE[1]:
        parser.error("--source-top is outside the sheet")
    if args.frame and not args.inspect:
        parser.error("--frame requires --inspect")
    action_id = args.inspect or ACTION_ORDER[0]
    frame_index = args.frame
    if not 0 <= frame_index < len(ACTIONS[action_id].frames):
        parser.error("--frame is outside the selected action")
    def report():
        frame_id = ACTIONS[action_id].frames[frame_index]
        frame = FRAME_RECTS[frame_id]
        print(f"{action_id} [{frame_index}/{len(ACTIONS[action_id].frames)-1}] "
              f"{frame_id}: rect={frame.rect} pivot=({frame.pivot_x}, {frame.pivot_y})",
              flush=True)
    report()
    import pico2d as p
    opened = False
    try:
        p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
        opened = True
        sheet = p.load_image(str(SOURCE_PATH))
        if (sheet.w, sheet.h) != SOURCE_SIZE:
            raise ValueError("Unexpected original sheet dimensions")
        print(f"Loaded original: {sheet.w} x {sheet.h}", flush=True)
        start = perf_counter()
        running = True
        while running:
            for event in p.get_events():
                if event.type == p.SDL_QUIT or (
                    event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE
                ):
                    running = False
                elif args.inspect and event.type == p.SDL_KEYDOWN:
                    if event.key in (p.SDLK_RIGHT, p.SDLK_LEFT):
                        step = 1 if event.key == p.SDLK_RIGHT else -1
                        frame_index = (frame_index + step) % len(ACTIONS[action_id].frames)
                        report()
                    elif event.key in (p.SDLK_UP, p.SDLK_DOWN):
                        step = 1 if event.key == p.SDLK_DOWN else -1
                        action_id = ACTION_ORDER[(ACTION_ORDER.index(action_id) + step)
                                                 % len(ACTION_ORDER)]
                        frame_index = 0
                        report()
            if not running:
                break
            if args.seconds is not None and perf_counter() - start >= args.seconds:
                break
            p.clear_canvas()
            if args.source_top is None:
                draw_source(sheet, FRAME_RECTS[ACTIONS[action_id].frames[frame_index]].rect)
            else:
                height = min(CANVAS_HEIGHT, sheet.h - args.source_top)
                draw_source(sheet, (0, args.source_top, CANVAS_WIDTH, height), 1)
            p.update_canvas()
            p.delay(0.01)
    finally:
        if opened:
            p.close_canvas()


if __name__ == "__main__":
    main()
