import random
from enum import Enum

import pygame

from detector.game import Config
from detector.game.Utils import calculate_random_parabola


class Entity(pygame.sprite.Sprite):
    def __init__(self, image, x_values, y_values, speed, points):
        """
        Every entity that has ever existed should inherit from this.
        Every entity inheriting from this can be rendered by pygame and will be updated by the game.
        These entities have "x" and "y" values. It has an array of x and y values. This array represents a parabola of
        their path on the screen.

        Future "cut" units have yet to override this behavior.
        :param x_values: represents each x value on its parabolic way
        :param y_values:represents each y value on its parabolic way
        :param speed: should in future configure speed of types
        """
        self.points = points
        self.image_name = image
        self.image = pygame.image.load(f"{Config.TEXTURE_DIR}{image}.png")
        pygame.sprite.Sprite.__init__(self)
        self.rect = self.image.get_rect()
        self.x_values, self.y_values = x_values, y_values
        # Every entity has its own ticker for its x and y values
        self.current_tick = 0
        self.rect.x, self.rect.y = x_values[0], y_values[0]
        self.previous_y = 0
        self.speed = speed
        # if set true this entity will be removed from the main game sprite group and its entity list
        self.delete = False
        self.collision = False
        self.free2catch = False

    def getImage(self):
        return self.image

    def update(self) -> None:
        """
        updates the internal rect matching to its parabolic way or set delete true
        if for the moment its way is coming to an end
        :return: Nothing
        """
        self.current_tick += 1
        if len(self.x_values) <= self.current_tick or \
                len(self.y_values) <= self.current_tick:
            self.delete = True
        elif self.collision:
            self.delete = True
        else:
            previous_y = self.rect[1]
            self.rect[0] = self.x_values[self.current_tick]
            self.rect[1] = self.y_values[self.current_tick]
            if previous_y < self.rect[1]:
                self.free2catch = True


class HitEnemy(Entity):
    """DEPRECATED AT THIS MOMENT"""

    def __init__(self, image, x_values, y_values, speed, part):
        """
        FUTURE: Bombs or split Fruits that should not be noted anymore

        Should not be called from other than Entity itself!
        Only Represent "images" from the cuttet Fruit or the exploding Bomb
        """
        super().__init__(f"{image}_half_{part}", x_values, y_values, speed)


class EntityTyp(Enum):
    APPLE = "apple"
    ORANGE = "orange"
    BANANA = "banana"
    COCONUT = "coconut"
    WATERMELON = "watermelon"
    PINEAPPLE = "pineapple"
    BOMB = "bomb"


ENTITY_CONFIG = {
    "apple": {"points": 7, "speed": 3},
    "orange": {"points": 4, "speed": 4},
    "banana": {"points": 3, "speed": 5},
    "coconut": {"points": 2, "speed": 2},
    "watermelon": {"points": 1, "speed": 6},
    "pineapple": {"points": 10, "speed": 1},
    "bomb": {"points": -5, "speed": 3},
}


def get_random_entity():
    rand_entity = random.choice(list(EntityTyp))
    entity_name = rand_entity.value
    concrete_entity = ENTITY_CONFIG[entity_name]
    speed = concrete_entity["speed"]
    points = concrete_entity["points"]
    parabola_array = calculate_random_parabola(speed)
    return Entity(entity_name, parabola_array[0], parabola_array[1], speed, points)
