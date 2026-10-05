"""Classic Sonic animation viewer (Python + pico2d)."""

import pico2d as p

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600


def handle_events():
    for event in p.get_events():
        if event.type == p.SDL_QUIT:
            return False
        if event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
            return False
    return True


def main():
    p.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    while handle_events():
        p.clear_canvas()
        p.update_canvas()
        p.delay(0.01)
    p.close_canvas()


if __name__ == "__main__":
    main()
