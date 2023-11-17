import time

import numpy as np
import pygame
import logging
import cv2

from detector.game import Entity, Utils
import Config
from detector.computer_vision.Cam import OpenCVCapture, Recorder
from detector.computer_vision import BGS

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
game_logger = logging.getLogger("Game")


class Game:
    def __init__(self, record_on=False, with_webcam=False, show_fps=False):
        """
        The game, brings together all the items,
        Webcam is a Phone Webcam, in Config.py the url has to be set
        :param record_on: if recorder should be used or not
        :param with_webcam: Should the IP CAM be used
        """
        pygame.init()
        logging.info("Pygame init")
        pygame.display.set_caption(Config.CAPTION)
        pygame.mixer.init()

        self.current_time = time.time()

        self.point_sound = pygame.mixer.Sound(f"{Config.SOUND_DIR}points.wav")
        self.explosion_sound = pygame.mixer.Sound(f"{Config.SOUND_DIR}explosion.wav")
        self.point_sound.set_volume(0.5)

        self.running = True
        self.screen = pygame.display.set_mode(Config.SCREEN)
        self.screen_thresh = pygame.display.set_mode(Config.SCREEN)

        game_logger.info(f"Display: {Config.SCREEN}")

        self.clock = pygame.time.Clock()
        self.show_fps = show_fps
        self.fps_tick = 0

        # this games uses sprite_groups of pygame to manage easily all entities
        self.entity_sprite_group = pygame.sprite.Group()
        # only to display a half fruit, does not belong to any logic after that
        self.cut_entity_group = pygame.sprite.Group()
        self.cut_entities = []
        # to update remove or else, also a own list of all entities
        self.entities = []
        self.players = [
            Player((255, 0, 0), (10, 10), 50)
        ]

        self.player_sprite_group = pygame.sprite.Group()
        for player in self.players:
            self.player_sprite_group.add(player)

        game_logger.info(f"Initialized Players: {self.players}")

        # record tick = each frame will be named after this value
        self.record_tick = 0

        # our webcam instance
        self.cap = None
        if with_webcam:
            self.cap = OpenCVCapture(Config.IP_CAM,
                                     frame_processor=BGS.BackSubProcessors[
                                         BGS.BackSubTyp.MOVING_AVERAGE_C_WRAPPER])
            self.cap.start_fetching_thread()
            game_logger.info(f"Webcam with IP:{Config.IP_CAM}")
            if self.cap.frame_processor is not None:
                game_logger.info(f"Frame processor is set: {self.cap.frame_processor}")
        else:
            game_logger.info(f"No Webcam")

        # our recorder
        self.recorder = None
        if record_on:
            self.recorder = Recorder()
            game_logger.info(f"Recorder with Record directory:{self.recorder.record_dir}")
        else:
            game_logger.info(f"No Recorder")

    def key_manager(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # press 'esc' to quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def draw_fps(self):
        if self.show_fps:
            pos = (Config.SCREEN_WIDTH - 150, Config.SCREEN_HEIGHT - 75)
            black = (255, 255, 255)
            Utils.draw_text_on_screen(self.screen, f"FPS: {self.clock.get_fps().__floor__()}", pos, black)

    def calculate_average_frames_per_second(self):
        start = self.current_time
        end = time.time()
        return (end - start) / self.record_tick

    def run(self):
        while self.running:
            # simple exit check aka ESC or Exit
            self.key_manager()

            # Black screen without Webcam, else
            # pygame game will be filled with the image of the webcam
            if self.cap is not None:
                # cam is running in another thread,
                # its normal that at start no image is available
                if self.cap.get_ip_cam_img() is not None:
                    threshold = self.cap.get_ip_cam_img()
                    img_surface = pygame.surfarray.make_surface(threshold).convert()
                    self.screen.blit(img_surface, (0, 0))
                    try:
                        contours, _ = cv2.findContours(threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                        largest_contour = max(contours, key=cv2.contourArea)
                        player.update_pos(largest_contour, self.screen)
                    except:
                        "Bug To Solve"




            else:
                self.screen.fill((0, 0, 0))

            # spawn a certain amount of entity
            if len(self.entity_sprite_group) <= 1:
                entity = Entity.get_random_entity()
                # add the entity to both groups, sprite and the intern game group
                self.entity_sprite_group.add(entity)
                self.entities.append(entity)

            for player in self.players:
                player.update_score_board(self.screen)

            # update entities
            for entity in self.entities:
                # remove if delete is set
                if entity.delete:
                    self.entities.remove(entity)
                    self.entity_sprite_group.remove(entity)
                else:
                    if entity.free2catch:
                        # check for collision
                        for player in self.players:
                            if entity.rect.colliderect(player.rect):
                                if entity.points > 0:
                                    self.point_sound.play()
                                else:
                                    self.explosion_sound.play()
                                player.update_points(entity.points)
                                entity.delete = True
                    entity.update()

            # pygame will draw all entities by itself
            # as long as they are in a sprite group
            self.entity_sprite_group.draw(self.screen)
            self.player_sprite_group.draw(self.screen)

            # update the recorders counter
            if self.recorder is not None:
                self.record_tick += 1
                self.recorder.record(self.screen, self.record_tick)

            # tick tick
            self.draw_fps()
            self.clock.tick(Config.FPS)
            self.fps_tick += 1
            # update display last
            pygame.display.update()

        # frames of the recorder will be saved at the end of the game
        if self.recorder is not None:
            self.recorder.convert_to_video()
        if self.recorder:
            print(f"Average Frames: {self.calculate_average_frames_per_second()}")
            pygame.quit()


class Player(pygame.sprite.Sprite):
    def __init__(self, color, score_board_pos, size):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(".././res/Assets/basket_64.png")
        self.rect = self.image.get_rect()
        self.points = 0
        self.color = color
        self.score_board_pos = score_board_pos

        self.pos = (0, 0)
        self.rect[0], self.rect[1] = self.pos[0], self.pos[1]
        self.size = size

    def update_points(self, points):
        self.points += points

    def update_score_board(self, screen):
        Utils.draw_text_on_screen(screen, f'Score: {self.points}', self.score_board_pos, self.color)

    def update_pos(self, contour, screen):
        y, x, w, h = cv2.boundingRect(contour)
        pygame.draw.rect(screen, (0, 255, 0), (x, y, w, h), 2)
        mid_x = x + w // 2 - self.size // 2
        mid_y = y + h // 2 - self.size // 2
        self.rect.x = mid_x
        self.rect.y = mid_y


game = Game(record_on=True, with_webcam=True, show_fps=True)
game.run()
