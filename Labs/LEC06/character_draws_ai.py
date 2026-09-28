import math

from pico2d import clear_canvas, close_canvas, delay, load_image, open_canvas, update_canvas


def draw_character(x, y):
    clear_canvas()
    character.draw(x, y)
    update_canvas()
    delay(0.01)


def move_line(start, end, steps):
    for step in range(steps + 1):
        t = step / steps
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        draw_character(x, y)


def move_circle():
    for degree in range(361):
        theta = math.radians(degree + 90)
        x = 400 + 250 * math.cos(theta)
        y = 300 + 250 * math.sin(theta)
        draw_character(x, y)


def move_rectangle():
    corners = [(50, 550), (750, 550), (750, 50), (50, 50), (50, 550)]
    for start, end in zip(corners, corners[1:]):
        move_line(start, end, 350 if start[1] == end[1] else 250)


def move_triangle():
    corners = [(400, 550), (750, 50), (50, 50), (400, 550)]
    for start, end in zip(corners, corners[1:]):
        move_line(start, end, 350)


open_canvas(800, 600)
character = load_image('character.png')

while True:
    move_circle()
    move_rectangle()
    move_triangle()

close_canvas()
