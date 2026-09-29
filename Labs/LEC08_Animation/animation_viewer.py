"""Drill #8: Hornet, rendered directly from the unchanged original sheet.

Run with Python and pico2d. All frame data and viewer code live in this file.
"""
import argparse
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "assets" / "source" / "hornet_original.png"
SOURCE_SIZE = (2393, 13086)
SOURCE_SHA256 = "0bcedf01ef61f1b2482cd76afed1f76435aa43f899b0e87242c283322997b02f"
CANVAS_WIDTH, CANVAS_HEIGHT = 960, 720


def draw_source(sheet, rect, scale=1.8):
    """Convert a top-origin source rectangle to Pico2d's bottom origin."""
    left, top, width, height = rect
    sheet.clip_draw(left, sheet.h - top - height, width, height,
                    CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                    width * scale, height * scale)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-top", type=int,
                        help="Inspect an unmodified 960x720 region of the source sheet")
    parser.add_argument("--seconds", type=float,
                        help="Close after this many seconds (rendering smoke checks)")
    args = parser.parse_args(argv)
    if args.seconds is not None and args.seconds <= 0:
        parser.error("--seconds must be positive")
    if args.source_top is not None and not 0 <= args.source_top < SOURCE_SIZE[1]:
        parser.error("--source-top is outside the sheet")
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
            if not running:
                break
            if args.seconds is not None and perf_counter() - start >= args.seconds:
                break
            p.clear_canvas()
            if args.source_top is None:
                draw_source(sheet, (3, 22, 358, 301))
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

