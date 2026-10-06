from pathlib import Path

from pico2d import *


def handle_events():
    global running, facing

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                running = False
            elif event.key == SDLK_RIGHT:
                pressed_keys.add(SDLK_RIGHT)
                facing = 1
            elif event.key == SDLK_LEFT:
                pressed_keys.add(SDLK_LEFT)
                facing = -1
            elif event.key == SDLK_UP:
                pressed_keys.add(SDLK_UP)
            elif event.key == SDLK_DOWN:
                pressed_keys.add(SDLK_DOWN)
        elif event.type == SDL_KEYUP:
            if event.key == SDLK_RIGHT:
                pressed_keys.discard(SDLK_RIGHT)
            elif event.key == SDLK_LEFT:
                pressed_keys.discard(SDLK_LEFT)
            elif event.key == SDLK_UP:
                pressed_keys.discard(SDLK_UP)
            elif event.key == SDLK_DOWN:
                pressed_keys.discard(SDLK_DOWN)


def update():
    global frame, x, y, dx, dy

    frame = (frame + 1) % 8
    dx = int(SDLK_RIGHT in pressed_keys) - int(SDLK_LEFT in pressed_keys)
    dy = int(SDLK_UP in pressed_keys) - int(SDLK_DOWN in pressed_keys)
    x += dx * 5
    y += dy * 5
    x = max(50, x)
    x = min(TUK_WIDTH - 50, x)
    y = max(50, y)
    y = min(TUK_HEIGHT - 50, y)


def draw():
    clear_canvas()
    tuk_ground.draw(TUK_WIDTH // 2, TUK_HEIGHT // 2)
    row = 300 if facing == 1 else 200
    if dx > 0:
        row = 100
    elif dx < 0:
        row = 0
    elif dy != 0:
        row = 100 if facing == 1 else 0
    character.clip_draw(frame * 100, row, 100, 100, x, y)
    update_canvas()


TUK_WIDTH, TUK_HEIGHT = 1280, 1024
open_canvas(TUK_WIDTH, TUK_HEIGHT)
image_dir = Path(__file__).resolve().parent
tuk_ground = load_image(str(image_dir / 'TUK_GROUND.png'))
character = load_image(str(image_dir / 'animation_sheet.png'))
x, y = TUK_WIDTH // 2, TUK_HEIGHT // 2
frame = 0
pressed_keys = set()
dx = 0
dy = 0
facing = 1
running = True

while running:
    handle_events()
    update()
    draw()
    delay(0.05)

close_canvas()
