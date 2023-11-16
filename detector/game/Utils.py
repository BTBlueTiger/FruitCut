from enum import Enum
import random
import numpy as np
import pygame
from numpy.core.records import ndarray

from detector import Config


class ScreenBorderType(Enum):
    """
    Simple convenience enumeration
    """
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3
    ANY = 4


def calculate_random_parabola(speed: int):
    """
    Calculates a random parabolic path of an entity.

    Individual adjustments can be changed in Config.py.
    :return: Random parabolic way
    """
    # Random int between a min width and max width
    # Screen start -> |Min width, .............., max width| <- Screen start
    # Changes could be done in Config.py
    x_pos = random.randint(Config.SCREEN_MIN_WIDTH_FRUIT, Config.SCREEN_WIDTH - Config.SCREEN_MIN_WIDTH_FRUIT)
    middle_of_x = Config.SCREEN_WIDTH // 2
    # Random int of how high a entity can fly
    highest_point = random.randint(Config.SCREEN_MIN_HEIGHT_FRUIT, Config.SCREEN_MAX_HEIGHT_FRUIT)
    # High Point or... vertex
    vertex = middle_of_x + (x_pos - middle_of_x) / 2

    # Calculate the coefficient "a" to ensure the parabola inverts and opens downward
    a = (Config.SCREEN_HEIGHT - highest_point) / ((vertex - middle_of_x) ** 2)

    # create with numpy the x values of the parabola
    # speed * points on path
    # the lower speed * points_on_path -> faster fruit
    points_on_path = 40
    if x_pos > middle_of_x:
        x_values = np.linspace(middle_of_x, x_pos, speed * points_on_path)
    else:
        x_values = np.linspace(x_pos, middle_of_x, speed * points_on_path)

    if random.randint(0, 1) == 0:
        x_values.sort(-1)

    # calculate all matching y values to x
    y_values = a * (x_values - vertex) ** 2 + highest_point

    return x_values, y_values


# DEPRECATED
def calculate_angle(pos_x: tuple):
    """
    First idea of the trajectory, discarded but maybe still useful in the future.
    :param pos_x:
    :return:
    """
    mid = Config.SCREEN_WIDTH // 2
    nearest_end = ScreenBorderType.RIGHT if pos_x > mid else ScreenBorderType.LEFT
    distance_to_border = pos_x if nearest_end == ScreenBorderType else Config.SCREEN_WIDTH - pos_x
    highest_point = random.randint(Config.SCREEN_MAX_HEIGHT_FRUIT, Config.SCREEN_MIN_HEIGHT_FRUIT)
    hypotenuse = np.sqrt(highest_point ** 2 + distance_to_border - mid ** 2)
    alpha = np.arcsin(Config.SCREEN_HEIGHT / hypotenuse)
    beta = 90 - alpha
    return beta


def draw_text_on_screen(screen, text: str, pos: tuple, color: tuple):
    """
    Simple convinience function to draw a text with its attributes
    """
    font = pygame.font.SysFont(Config.FONT_FAMILY, Config.FONT_SIZE)
    text = font.render(text, True, color)
    screen.blit(text, pos)
