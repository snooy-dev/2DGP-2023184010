from pico2d import *
import game_framework
import title_mode

image = None
logo_start_time = 0.0

def init():
    global image, logo_start_time

    image = load_image('tuk_credit.png')
    logo_start_time = get_time()

def finish():
    global image
    del image

def update():
    if get_time() - logo_start_time >= 2.0:
        game_framework.change_mode(title_mode)

def render():
    clear_canvas()
    image.draw(400, 300)
    update_canvas()

def handle_events():
    events = get_events()
