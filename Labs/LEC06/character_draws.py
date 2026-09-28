# 실습 과제 진행
from pico2d import *

open_canvas(800, 600)
character = load_image('character.png')

def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)

def move_circle():
    for degree in range(360):
        theta = math.radians(degree)
        x = 400 + 200 * math.cos(theta)
        y = 300 + 200 * math.sin(theta)
        draw_character(x, y)

def draw_top():
    for x in range(50, 750, 5):
        draw_character(x, 550)

def draw_left():
    for y in range(550, 50, -5):
        draw_character(750, y)

def draw_bottom():
    for x in range(750, 50, -5):
        draw_character(x, 50)

def draw_right():
    for y in range(50, 550, 5):
        draw_character(50, y)

def move_rectangle():
    draw_top()
    draw_left()
    draw_bottom()
    draw_right()

def draw_left_side():
    for t in range(100):
        t /= 100
        draw_character(400 + t * 350, 600 - t * 550)

def draw_right_side():
    pass

def move_triangle():
    # draw_left_side()
    draw_bottom()
    draw_right_side()

while True:
    # move_circle()
    # move_rectangle()
    move_triangle()

close_canvas()