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
