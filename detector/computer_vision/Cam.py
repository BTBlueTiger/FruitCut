import os

import pygame
import requests
import cv2
import numpy as np
import threading

from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

from detector import Config


class OpenCVCapture:

    def __init__(self, url, frame_processor=None):
        """
        Uses a URL that belongs to an IP webcam.
        (Within the used project via the APP IP Webcam
        by @Pavel Khlebovich from the Android Store).
        :param url: url to the desired Webcam
        """
        self.url = url
        self.image = None
        self.lock = threading.Lock()  # Create a lock to protect access to self.image
        self.frame_processor = frame_processor
        self.frame_processor.start_calculation_thread()

    def get_ip_cam_img(self):
        """
        Gets the image from a separate thread.
        :return: a edited image as pygame surface
        """
        if self.image is not None:
            return self.image

    def fetch_image_thread(self):
        while True:
            # Request the webcam for a jpg

            request = requests.get(f"{self.url}/shot.jpg")
            # Decode the image
            img_arr = np.frombuffer(request.content, dtype=np.uint8)

            img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)  # Use cv2.IMREAD_COLOR for a color image

            # Resize to match the Config
            img = cv2.resize(img, (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))

            # Change the channels and rotate the image to fit the game

            img = np.rot90(img)

            if self.frame_processor is not None:
                self.frame_processor.apply(img)
                processed = self.frame_processor.processed_frame
                if processed is not None:
                    img = self.frame_processor.processed_frame
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)



            # Lock accesses to self.image to prevent race conditions
            with self.lock:
                self.image = img

    def start_fetching_thread(self):
        """
            Create and start a thread to fetch the image
        """
        image_thread = threading.Thread(target=self.fetch_image_thread)
        image_thread.daemon = True
        image_thread.start()


class Recorder:
    def __init__(self):
        """
            game recorder that saves individual frames via Pygame.
            Converts the frames into a video when finished properly.
            Each new game gets its own folder.
        """
        self.record_dir = self.create_new_record_dir()

    @staticmethod
    def create_new_record_dir() -> str:
        """
        :return: string of the new dir for frames and afterwards the video
        """
        # counting existing dirs to evaluate the next dir number
        existing_dirs = [int(name) for name in os.listdir(Config.RECORD_DIR) if name.isdigit()]
        if existing_dirs:
            new_dir_number = max(existing_dirs) + 1
        else:
            new_dir_number = 1
        # creating the new dir via os and using its path as return value
        new_record_dir = os.path.join(Config.RECORD_DIR, str(new_dir_number))
        os.makedirs(new_record_dir)
        return new_record_dir

    def record(self, screen, tick) -> None:
        """
        Saves each frame
        :param screen: which is recorded
        :param tick: to name each frame
        """
        pygame.image.save(screen, f"{self.record_dir}/{tick}.bmp")

    def convert_to_video(self) -> None:
        """
        Converts after pygame quit all frames in the folder to a .mp4 file
        :return:
        """
        # each .bmp file
        frames = sorted(os.listdir(self.record_dir), key=lambda x: int(os.path.splitext(x)[0]))

        print(frames)
        # create VideoClip
        clip = ImageSequenceClip([os.path.join(self.record_dir, frame) for frame in frames], fps=30)
        # write video clip
        clip.write_videofile(f"{self.record_dir}/_Fruit_Ninja.mp4", codec='libx264')
        clip.close()
