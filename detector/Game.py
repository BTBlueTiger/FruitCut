import pygame

from detector.computer_vision.Cam import OpenCVCapture
from detector.game import Config, Entity, Utils

from detector.computer_vision.Cam import Recorder


class Game:
    def __init__(self, record_on=False, with_webcam=False):
        """
        The game, brings together all the items,
        Webcam is a Phone Webcam, in Config.py the url has to be set
        :param record_on: if recorder should be used or not
        :param with_webcam: Should the IP CAM be used
        """
        pygame.init()
        pygame.display.set_caption(Config.CAPTION)
        pygame.mixer.init()
        self.point_sound = pygame.mixer.Sound(f"{Config.SOUND_DIR}points.wav")
        self.explosion_sound = pygame.mixer.Sound(f"{Config.SOUND_DIR}explosion.wav")
        self.point_sound.set_volume(0.5)

        self.running = True
        self.screen = pygame.display.set_mode(Config.SCREEN)
        self.clock = pygame.time.Clock()

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

        # record tick = each frame will be named after this value
        self.record_tick = 0

        # our webcam instance
        self.cap = None
        if with_webcam:
            self.cap = OpenCVCapture(Config.IP_CAM)
            self.cap.start_fetching_thread()

        # our recorder
        self.recorder = None
        if record_on:
            self.recorder = Recorder()

    def key_manager(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # press 'esc' to quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def run(self):
        while self.running:
            # simple exit check aka ESC or Exit
            self.key_manager()

            # Black screen without Webcam, else
            # pygame game will be filled with the image of the webcam
            if self.cap is not None:
                # cam is running in another thread,
                # its normal that at start no image is available
                if self.cap.get_ip_cam_img():
                    self.screen.blit(self.cap.get_ip_cam_img(), (0, 0))
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
                player.update_mouse(pygame.mouse.get_pos())

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
            self.clock.tick(Config.FPS)
            # update display last
            pygame.display.update()

        # frames of the recorder will be saved at the end of the game
        if self.recorder is not None:
            self.recorder.convert_to_video()
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
        # -- add Text on screen (e.g. score)
        text_font = pygame.font.SysFont("arial", 26)
        score_board = text_font.render(f'Score: {self.points}', True, self.color)
        screen.blit(score_board, self.score_board_pos)

    def update_mouse(self, pos):
        self.rect.update(pos[0] - self.size // 2, pos[1] - self.size // 2, self.size, self.size)


game = Game(record_on=False, with_webcam=False)
game.run()
