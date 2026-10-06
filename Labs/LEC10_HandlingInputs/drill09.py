from pico2d import *


def handle_events():
    global running

    for event in get_events():
        if event.type == SDL_QUIT:
            running = False


def update():
    pass


def draw():
    clear_canvas()
    update_canvas()


TUK_WIDTH, TUK_HEIGHT = 1280, 1024
open_canvas(TUK_WIDTH, TUK_HEIGHT)
running = True

while running:
    handle_events()
    update()
    draw()
    delay(0.05)

close_canvas()
