import os

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN = [SCREEN_WIDTH, SCREEN_HEIGHT]
FPS = 30
CAPTION = "Fruit Cut"

# Parabola parameters, explained in ./detector/Game/Utils.py in @calculate_random_parabola
SCREEN_MIN_WIDTH_FRUIT = 150
SCREEN_MIN_HEIGHT_FRUIT = 100
SCREEN_MAX_HEIGHT_FRUIT = 200

# Webcam URL
IP_CAM = "http://192.168.107.68:8080"

ASSET_DIR = os.path.join(os.path.dirname(__file__), "../res/Assets\\")

# Assets to the fruits, relativ
TEXTURE_DIR = os.path.join(os.path.dirname(__file__), f"{ASSET_DIR}"
                                                      "fruit-ninja-assets-master_"
                                                      "extended_40\\")

SOUND_DIR = os.path.join(os.path.dirname(__file__), f"{ASSET_DIR}"
                                                    "sounds\\")

# Dir to the Captured Videos, relativ
RECORD_DIR = os.path.join(os.path.dirname(__file__), "../res/Capture\\")

FONT_SIZE = 26
FONT_FAMILY = "corbel"
