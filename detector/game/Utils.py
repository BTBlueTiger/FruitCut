from enum import Enum
import random
import numpy as np

from detector.game import Config


class ScreenBorderType(Enum):
    """
    Simple convenience enumeration
    """
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3
    ANY = 4


def calculate_random_parabola(speed):
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

    # create with numpy the x values of the parabola, 100 -> 100 values of x
    if x_pos > middle_of_x:
        x_values = np.linspace(middle_of_x, x_pos, speed * 20)
    else:
        x_values = np.linspace(x_pos, middle_of_x, speed * 20)

    if random.randint(0, 1) == 0:
        x_values.sort(-1)

    # calculate all matching y values to x
    y_values = a * (x_values - vertex) ** 2 + highest_point

    return x_values, y_values


def calculate_angle(pos_x):
    """
    First idea of the trajectory, discarded but maybe still useful in the future for cut fruit.
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


def calculate_rest_path(entity_pos):
    # Given data
    start_x = entity_pos[0]  # Adjust the starting x-coordinate as needed
    start_y = entity_pos[1]  # Adjust the starting y-coordinate as needed
    y_axis = Config.SCREEN_HEIGHT  # The desired y-axis position

    # Calculate the vertex (h, k) using the starting point
    h = start_x
    k = start_y

    # Calculate x1 and x2 such that the parabola reaches the y-axis at Config.SCREEN_HEIGHT
    # Ensure that x1 and x2 are within the screen bounds
    x1 = h - np.sqrt(k / (y_axis - k))
    x2 = h + np.sqrt(k / (y_axis - k))
    x1 = max(x1, 0)  # Ensure x1 is not negative
    x2 = min(x2, Config.SCREEN_WIDTH)  # Ensure x2 is not greater than the screen width

    # Calculate the coefficient a using the vertex form of the parabola equation
    a = k / min((x1 - h) ** 2, (x2 - h) ** 2)

    # Create an array of x values that spans from x1 to x2
    x = np.linspace(x1, x2, 50)  # Adjust the number of points as needed

    # Calculate the y values using the parabola equation
    y = a * (x - h) ** 2 + k
    return x, y
