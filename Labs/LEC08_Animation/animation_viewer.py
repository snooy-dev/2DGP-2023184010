"""Drill #8: Hornet, rendered directly from the unchanged original sheet.

Run with Python and pico2d. All frame data and viewer code live in this file.
"""
import argparse
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import math
from time import perf_counter

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "hornet_sheet.png"
CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720
MARGIN_X, MARGIN_Y = 36, 64
PREFERRED_SCALE = 2.0
REPEAT_COUNT = 5
PAUSE_SECONDS = 1.0


@dataclass(frozen=True)
class Frame:
    """One source rectangle and its local anchor; no new image is created."""
    rect: tuple[int, int, int, int]
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class Action:
    label: str
    phases: tuple[tuple[str, tuple[str, ...]], ...]
    fps: float = 12.0
    duration_overrides: tuple[tuple[int, float], ...] = ()

    @cached_property
    def frames(self):
        return tuple(frame_id for _, frames in self.phases for frame_id in frames)

    @cached_property
    def durations(self):
        overrides = dict(self.duration_overrides)
        return tuple(overrides.get(i, 1 / self.fps) for i in range(len(self.frames)))


# left, top, width, height, pivot_x, pivot_y; top-left source coordinates.
# Measured from the unchanged sheet, including every nonzero-alpha pixel.
SOURCE_FRAMES = {
    "flourish": (
        (46, 79, 183, 215, 91, 244),
        (404, 117, 194, 177, 110, 206),
        (757, 108, 195, 187, 97, 215),
        (1123, 92, 191, 201, 94, 231),
        (1507, 102, 176, 189, 71, 221),
        (1902, 99, 148, 193, 73, 224),
        (3, 400, 232, 227, 188, 227),
        (384, 430, 319, 166, 164, 197),
        (745, 385, 297, 211, 165, 242),
        (1106, 356, 268, 240, 165, 271),
        (1467, 327, 336, 269, 164, 300),
        (1828, 405, 331, 191, 165, 222),
        (23, 647, 240, 253, 165, 284),
        (396, 716, 195, 187, 97, 215),
    ),
    "idle": (
        (3, 954, 183, 215, 91, 215),
        (190, 954, 183, 215, 90, 215),
        (378, 954, 182, 215, 88, 215),
        (565, 955, 181, 214, 88, 214),
        (752, 954, 181, 215, 89, 215),
        (938, 954, 182, 215, 90, 215),
    ),
    "run": (
        (8, 1195, 154, 185, 74, 187),
        (170, 1194, 153, 174, 78, 188),
        (333, 1195, 149, 186, 77, 187),
        (489, 1192, 158, 190, 82, 190),
        (656, 1195, 154, 186, 79, 187),
        (818, 1194, 153, 174, 79, 188),
        (981, 1196, 149, 184, 73, 186),
        (1137, 1193, 158, 188, 79, 189),
    ),
    "jump_anticipate": (
        (18, 1441, 183, 155, 107, 163),
        (227, 1442, 192, 156, 99, 162),
        (423, 1441, 201, 163, 107, 163),
        (680, 1405, 143, 192, 74, 199),
    ),
    "jump": (
        (49, 1650, 136, 205, 66, 205),
        (243, 1651, 127, 204, 64, 204),
        (447, 1651, 115, 202, 48, 204),
        (622, 1638, 132, 191, 67, 217),
        (767, 1633, 187, 195, 116, 222),
        (978, 1626, 160, 199, 102, 229),
        (1171, 1627, 157, 205, 99, 228),
        (1359, 1626, 161, 202, 102, 229),
        (1556, 1627, 155, 201, 97, 228),
    ),
    "land": (
        (11, 1917, 194, 177, 110, 178),
        (209, 1908, 195, 187, 97, 187),
        (425, 1878, 189, 216, 87, 217),
    ),
    "hard_land": (
        (668, 1941, 183, 155, 107, 165),
        (877, 1942, 192, 156, 99, 164),
        (1073, 1941, 201, 163, 107, 165),
        (1283, 1930, 202, 176, 105, 176),
    ),
    "wall_impact": (
        (3, 2132, 109, 209, 49, 209),
        (133, 2128, 125, 205, 38, 213),
        (263, 2128, 125, 206, 38, 213),
        (393, 2128, 123, 207, 38, 213),
    ),
    "evade_anticipate": (
        (555, 2132, 176, 214, 89, 214),
        (743, 2129, 184, 216, 94, 217),
        (936, 2146, 174, 200, 84, 200),
    ),
    "evade": (
        (1155, 2130, 191, 210, 135, 210),
        (1350, 2130, 192, 205, 132, 210),
        (1549, 2129, 191, 210, 134, 211),
    ),
    "ground_dash_anticipate": (
        (3, 2369, 203, 189, 104, 192),
        (315, 2401, 204, 156, 108, 160),
        (631, 2426, 205, 135, 93, 135),
        (903, 2421, 205, 137, 105, 140),
        (1182, 2421, 205, 137, 107, 140),
        (1461, 2421, 205, 137, 108, 140),
        (1740, 2421, 205, 137, 105, 140),
        (2019, 2421, 205, 137, 107, 140),
        (66, 2617, 205, 137, 108, 140),
        (348, 2626, 205, 128, 100, 131),
    ),
    "ground_dash": (
        (3, 2780, 254, 136, 178, 136),
        (263, 2782, 251, 134, 178, 134),
    ),
    "ground_dash_recover": (
        (630, 2864, 200, 123, 122, 123),
        (928, 2850, 203, 137, 113, 137),
        (1224, 2850, 204, 137, 111, 137),
        (1499, 2837, 205, 149, 115, 150),
        (1740, 2799, 196, 187, 99, 188),
        (2021, 2779, 192, 207, 97, 208),
    ),
    "air_dash_anticipate": (
        (3, 4147, 203, 195, 104, 198),
        (242, 4168, 204, 166, 108, 177),
        (495, 4193, 205, 152, 93, 152),
        (723, 4188, 205, 156, 105, 157),
        (958, 4188, 205, 157, 107, 157),
        (1193, 4188, 205, 152, 108, 157),
        (1428, 4188, 205, 156, 105, 157),
        (1663, 4188, 205, 157, 107, 157),
        (1908, 4190, 205, 144, 100, 155),
    ),
    "air_dash": (
        (3, 4368, 254, 136, 178, 136),
        (263, 4370, 251, 134, 178, 134),
    ),
    "air_dash_recover": (
        (551, 4374, 196, 183, 96, 199),
        (756, 4367, 160, 199, 102, 206),
        (958, 4368, 157, 205, 99, 205),
        (1155, 4367, 161, 202, 102, 206),
        (1361, 4368, 155, 201, 97, 205),
    ),
    "sphere_ground_anticipate": (
        (27, 5186, 160, 199, 102, 200),
        (293, 5192, 160, 193, 60, 194),
        (514, 5197, 203, 186, 75, 189),
        (739, 5201, 204, 184, 87, 185),
        (970, 5203, 215, 181, 95, 183),
        (1198, 5213, 221, 171, 104, 173),
        (1437, 5221, 223, 165, 97, 165),
        (1676, 5213, 221, 171, 104, 173),
        (1926, 5203, 215, 181, 95, 183),
        (2173, 5201, 204, 184, 87, 185),
    ),
    "sphere_air_anticipate": (
        (25, 5409, 160, 199, 102, 203),
        (311, 5419, 160, 193, 60, 193),
        (528, 5416, 203, 184, 75, 196),
        (753, 5423, 204, 164, 88, 189),
        (987, 5425, 215, 161, 95, 187),
        (1223, 5431, 221, 159, 105, 181),
        (1467, 5435, 223, 148, 97, 177),
    ),
    "sphere": (
        (3, 5644, 131, 174, 67, 174),
        (160, 5644, 118, 154, 82, 174),
        (304, 5642, 115, 162, 79, 176),
        (448, 5643, 114, 167, 76, 175),
        (593, 5643, 117, 168, 73, 175),
        (739, 5643, 118, 169, 70, 175),
        (886, 5643, 117, 168, 66, 175),
        (1032, 5641, 120, 170, 65, 177),
        (1179, 5635, 117, 176, 61, 183),
    ),
    "sphere_recover": (
        (1372, 5635, 231, 174, 118, 210),
        (1607, 5648, 200, 197, 121, 197),
    ),
    "throw_anticipate": (
        (3, 6790, 192, 210, 95, 210),
        (325, 6800, 182, 200, 73, 200),
        (607, 6787, 192, 211, 82, 213),
        (907, 6804, 205, 194, 80, 196),
        (1188, 6802, 205, 198, 82, 198),
        (1469, 6802, 205, 198, 82, 198),
        (1750, 6802, 205, 197, 80, 198),
        (2031, 6802, 205, 198, 82, 198),
        (64, 7019, 205, 197, 80, 198),
        (360, 7026, 201, 189, 79, 191),
    ),
    "throw": (
        (25, 7240, 129, 185, 57, 186),
        (158, 7291, 150, 135, 94, 135),
        (324, 7298, 137, 127, 76, 128),
        (468, 7294, 149, 131, 88, 132),
        (634, 7294, 138, 131, 77, 132),
        (789, 7294, 138, 131, 75, 132),
    ),
    "throw_recover": (
        (11, 7500, 231, 137, 126, 137),
        (259, 7504, 203, 132, 119, 133),
        (489, 7505, 203, 131, 125.5, 132),
        (732, 7505, 203, 131, 125, 132),
        (975, 7505, 203, 131, 123.5, 132),
        (1227, 7449, 184, 187, 93, 188),
    ),
    "counter_anticipate": (
        (56, 8034, 109, 211, 49, 214),
        (244, 8036, 112, 210, 62, 212),
        (379, 8108, 184, 140, 128, 140),
    ),
    "counter_stance": (
        (599, 8037, 184, 140, 128, 140),
        (787, 8042, 184, 133, 130, 135),
        (975, 8037, 183, 138, 125, 140),
        (1163, 8034, 184, 140, 124, 143),
    ),
    "counter_end": (
        (1383, 8036, 112, 210, 62, 210),
        (1498, 8034, 109, 211, 49, 212),
    ),
    "counter_attack_anticipate": (
        (5, 8271, 257, 275, 187, 279),
        (266, 8304, 258, 242, 163, 246),
        (623, 8384, 146, 166, 103, 166),
    ),
    "counter_attack_1": (
        (824, 8271, 359, 371, 307, 371),
    ),
    "counter_attack_2": (
        (1219, 8270, 597, 333, 347, 333),
    ),
    "counter_attack_recover": (
        (1855, 8328, 233, 141, 52, 141),
        (2092, 8270, 147, 199, 58, 199),
    ),
    "barb_throw_anticipate": (
        (3, 8676, 142, 211, 82, 214),
        (230, 8678, 108, 210, 50, 212),
        (391, 8688, 120, 202, 55, 202),
        (553, 8665, 101, 224, 72, 225),
    ),
    "barb_throw": (
        (719, 8677, 113, 175, 66, 176),
        (869, 8664, 126, 189, 59, 189),
        (1009, 8664, 126, 189, 58, 189),
        (1149, 8664, 126, 189, 56, 189),
    ),
    "barb_throw_recover": (
        (20, 8925, 215, 202, 110, 203),
        (253, 8918, 200, 209, 107, 210),
        (484, 8915, 195, 212, 99, 213),
        (711, 8912, 188, 215, 97, 216),
        (949, 8913, 183, 215, 91, 215),
    ),
    "stun_air": (
        (36, 9983, 233, 166, 130, 166),
        (325, 9989, 241, 135, 142, 160),
        (609, 9957, 242, 187, 180, 192),
        (913, 9955, 231, 155, 168, 194),
        (1306, 9923, 154, 171, 91, 226),
        (1602, 9970, 215, 153, 102, 179),
    ),
    "stun": (
        (3, 10172, 205, 175, 115, 186),
        (229, 10212, 201, 132, 119, 146),
        (446, 10186, 180, 170, 109, 172),
        (661, 10189, 179, 169, 108, 169),
        (876, 10190, 179, 165, 107, 168),
        (1091, 10191, 179, 164, 108, 167),
    ),
    "wounded": (
        (10, 10397, 195, 187, 97, 199),
        (222, 10381, 185, 213, 108, 215),
        (437, 10382, 184, 214, 109, 214),
        (649, 10383, 185, 212, 111, 213),
        (863, 10382, 187, 213, 111, 214),
        (1079, 10382, 188, 213, 110, 214),
        (1295, 10381, 187, 211, 108, 215),
    ),
}
FRAME_RECTS = {
    f"{phase}:{i}": Frame(values[:4], *values[4:])
    for phase, frames in SOURCE_FRAMES.items()
    for i, values in enumerate(frames)
}


def phase(name, indexes=None):
    """References may reuse a rectangle, including reverse recovery frames."""
    indexes = range(len(SOURCE_FRAMES[name])) if indexes is None else indexes
    return name, tuple(f"{name}:{i}" for i in indexes)


ACTIONS = {
    "stagger": Action("Stagger", (phase("stun_air"), phase("stun"), phase("stun", (1, 0)))),
    "wounded": Action("Wounded", (phase("stun", (0, 1)), phase("wounded"))),
    "barb_throw": Action("Barb Throw", (phase("barb_throw_anticipate"), phase("barb_throw"), phase("barb_throw_recover"))),
    "counter_attack": Action("Counter Attack", (phase("counter_attack_anticipate"), phase("counter_attack_1"), phase("counter_attack_2"), phase("counter_attack_recover")), duration_overrides=((3, 0.12), (4, 0.12))),
    "counter": Action("Counter", (phase("counter_anticipate"), phase("counter_stance"), phase("counter_end"))),
    "throw": Action("Throw", (phase("throw_anticipate"), phase("throw"), phase("throw_recover"))),
    "sphere_ground": Action("Sphere Ground", (phase("sphere_ground_anticipate"), phase("sphere"), phase("sphere_recover"))),
    "sphere_air": Action("Sphere Air", (phase("sphere_air_anticipate"), phase("sphere"), phase("sphere_recover"))),
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
ACTION_ORDER = (
    "flourish", "idle", "run", "jump", "hard_land", "wall_impact", "evade",
    "ground_dash", "air_dash", "sphere_ground", "sphere_air", "throw",
    "counter", "counter_attack", "barb_throw", "stagger", "wounded",
)


@dataclass
class Player:
    action_index: int = 0
    frame_index: int = 0
    elapsed: float = 0.0
    completed_repeats: int = 0
    mode: str = 'PLAYING'
    cycles: int = 0
    timeline: float = 0.0


def advance(player, dt, emit=None):
    """Consume elapsed time, carrying overshoot across every frame boundary."""
    while dt > 0:
        action = ACTIONS[ACTION_ORDER[player.action_index]]
        duration = PAUSE_SECONDS if player.mode == 'PAUSING' else action.durations[player.frame_index]
        remaining = duration - player.elapsed
        if dt < remaining - 1e-10:
            player.elapsed += dt
            player.timeline += dt
            break
        player.timeline += remaining
        dt = max(0.0, dt - remaining)
        player.elapsed = 0.0
        if player.mode == 'PAUSING':
            player.action_index = (player.action_index + 1) % len(ACTION_ORDER)
            if player.action_index == 0:
                player.cycles += 1
            player.mode = 'PLAYING'
            player.frame_index = 0
            player.completed_repeats = 0
            if emit:
                emit('start', player)
        elif player.frame_index + 1 < len(action.frames):
            player.frame_index += 1
        else:
            player.completed_repeats += 1
            if emit:
                emit('repeat', player)
            if player.completed_repeats == REPEAT_COUNT:
                player.mode = 'PAUSING'
                if emit:
                    emit('pause', player)
            else:
                player.frame_index = 0


def trace_event(event, player):
    print(f"{player.timeline:10.6f} {event:6s} "
          f"action={ACTION_ORDER[player.action_index]} "
          f"repeat={player.completed_repeats} frame={player.frame_index} "
          f"cycle={player.cycles}", flush=True)


def action_layout(action):
    """One scale per entire action; leave room for every frame and its effects."""
    frames = [FRAME_RECTS[frame_id] for frame_id in action.frames]
    left = max(frame.pivot_x for frame in frames)
    right = max(frame.rect[2] - frame.pivot_x for frame in frames)
    top = max(frame.pivot_y for frame in frames)
    bottom = max(frame.rect[3] - frame.pivot_y for frame in frames)
    scale = min(PREFERRED_SCALE,
                (CANVAS_WIDTH / 2 - MARGIN_X) / max(left, right),
                (CANVAS_HEIGHT - 2 * MARGIN_Y) / (top + bottom))
    return CANVAS_WIDTH / 2, (CANVAS_HEIGHT + (bottom - top) * scale) / 2, scale


def load_hud_font(p):
    """An optional system font; running the animation never needs a font asset."""
    import os
    candidates = (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/consola.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
    )
    for path in candidates:
        if path.is_file():
            try:
                return p.load_font(str(path), 20)
            except OSError:
                pass
    return None


def draw_frame(sheet, frame, anchor_x, anchor_y, scale):
    """Keep the body anchor stable despite irregular rectangles and effects."""
    left, top, width, height = frame.rect
    draw_x = anchor_x + (width / 2 - frame.pivot_x) * scale
    draw_y = anchor_y + (frame.pivot_y - height / 2) * scale
    sheet.clip_draw(left, sheet.h - top - height, width, height,
                    draw_x, draw_y, width * scale, height * scale)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", action="store_true",
                        help="Log action starts, completed repeats and pauses")
    parser.add_argument("--cycles", type=int,
                        help="Exit after complete cycles (default: repeat forever)")
    parser.add_argument("--seconds", type=float,
                        help="Close after this many seconds (rendering smoke checks)")
    args = parser.parse_args(argv)
    if args.cycles is not None and args.cycles <= 0:
        parser.error("--cycles must be positive")
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error("--seconds must be finite and positive")
    action_id = ACTION_ORDER[0]
    frame_index = 0
    inspecting = False
    def report():
        frame_id = ACTIONS[action_id].frames[frame_index]
        frame = FRAME_RECTS[frame_id]
        print(f"{action_id} [{frame_index}/{len(ACTIONS[action_id].frames)-1}] "
              f"{frame_id}: rect={frame.rect} pivot=({frame.pivot_x}, {frame.pivot_y})",
              flush=True)
    report()
    import pico2d as p
    layouts = {key: action_layout(action) for key, action in ACTIONS.items()}
    p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        p.hide_lattice()
        font = load_hud_font(p)
        sheet = p.load_image(str(SOURCE_PATH))
        print(f"Loaded original: {sheet.w} x {sheet.h}", flush=True)
        start = previous = perf_counter()
        player = Player()
        emit = trace_event if args.trace else None
        if emit:
            emit('start', player)
        running = True
        while running:
            mode_changed = False
            for event in p.get_events():
                if event.type == p.SDL_QUIT or (
                    event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE
                ):
                    running = False
                elif event.type == p.SDL_KEYDOWN:
                    if event.key == p.SDLK_i:
                        inspecting = not inspecting
                        mode_changed = True
                        if inspecting:
                            report()
                    elif inspecting and event.key in (p.SDLK_RIGHT, p.SDLK_LEFT):
                        step = 1 if event.key == p.SDLK_RIGHT else -1
                        frame_index = (frame_index + step) % len(ACTIONS[action_id].frames)
                        report()
                    elif inspecting and event.key in (p.SDLK_UP, p.SDLK_DOWN):
                        step = 1 if event.key == p.SDLK_DOWN else -1
                        action_id = ACTION_ORDER[(ACTION_ORDER.index(action_id) + step)
                                                 % len(ACTION_ORDER)]
                        frame_index = 0
                        report()
            if not running:
                break
            if args.seconds is not None and perf_counter() - start >= args.seconds:
                break
            now = perf_counter()
            if not inspecting:
                # Inspection freezes Player, including a partly elapsed hold.
                # Do not charge time spent inspecting when I resumes playback.
                if not mode_changed:
                    advance(player, now - previous, emit)
                action_id = ACTION_ORDER[player.action_index]
                frame_index = player.frame_index
                if args.cycles is not None and player.cycles >= args.cycles:
                    break
            previous = now
            p.clear_canvas()
            draw_frame(sheet, FRAME_RECTS[ACTIONS[action_id].frames[frame_index]],
                       *layouts[action_id])
            if font:
                font.draw(36, CANVAS_HEIGHT - 32,
                          f'HORNET  /  {ACTIONS[action_id].label}  /  '
                          f'Frame {frame_index + 1}/{len(ACTIONS[action_id].frames)}')
                if not inspecting:
                    status = 'HOLD 1.0s' if player.mode == 'PAUSING' else 'PLAYING'
                    font.draw(830, CANVAS_HEIGHT - 32,
                              f'{status}  Done {player.completed_repeats}/{REPEAT_COUNT}')
                else:
                    font.draw(830, CANVAS_HEIGHT - 32, 'INSPECT')
                help_text = ('I: resume    Left/Right: frame    Up/Down: action'
                             if inspecting else 'I: inspect')
                font.draw(36, 30, f'ESC: close    {help_text}')
            p.update_canvas()
            p.delay(0.01)
    finally:
        p.close_canvas()


if __name__ == "__main__":
    raise SystemExit(main())
