import os

# Pygame Screen Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN = [SCREEN_WIDTH, SCREEN_HEIGHT]
FPS = 30
CAPTION = "Fruit Cut"

# Parabola parameters, explained in Entity.py in @calculate_random_parabola
SCREEN_MIN_WIDTH_FRUIT = 150
SCREEN_MIN_HEIGHT_FRUIT = 100
SCREEN_MAX_HEIGHT_FRUIT = 200

# Webcam URL
IP_CAM = "http://192.168.178.58:8080"

# Assets to the fruits, relativ
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..\\..\\res\\Assets\\"
                                                     "fruit-ninja-assets-master_"
                                                     "extended_40\\")

# Dir to the Captured Videos, relativ
RECORD_DIR = os.path.join(os.path.dirname(__file__), "..\\..\\res\\Capture\\")
