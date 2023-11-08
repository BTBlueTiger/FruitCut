import threading

import cv2
import numpy as np
from enum import Enum
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import Config
import pybind11
from computer_vision.Release import moving_average_module


class BackSubTyp(Enum):
    MOG_OPEN_CV = 0
    KNN_OPEN_CV = 1
    SELF_IMPLEMENTED_BACK_SUB = 2
    MOVING_AVERAGE = 3


class ThreshHoldTyp(Enum):
    ADAPTIV = 0
    OTSU = 1
    MANUAL = 2


class ThreshCalculationTyp(Enum):
    MEDIAN = 0
    MEDIAN_WEIGHTED = 1
    MEAN = 2
    MEAN_WEIGHTED = 3


class BackSubProcessor:
    def __init__(self, history=10, sampling_rate=1):
        self.processed_frame = None
        self._calculation_lock = threading.Lock()
        self._calculation_event = threading.Event()
        self._current_frame = None
        self._history = history
        self._sampling_rate = sampling_rate

        """
        self._queue_changed = False
        self._frame_queue = deque(maxlen=n_frames)
        self._filter_executor = ThreadPoolExecutor(max_workers=2)
        self._sampling_rate = sampling_rate
        self._sampling_ticks = 0
        self._n_frames = n_frames
        self._calculated_value = 0
        self._threshold = 0
        self._thresh_ticker = 0
        self._thresh_ticks2_new_thresh = 15  #
        self.mv = moving_average_module.MovingAverage(10)
        """

    def apply(self, frame):
        self._current_frame = frame
        self._calculation_event.set()

    def start_calculation_thread(self):
        _calculation_thread = threading.Thread(target=self._calculate)
        _calculation_thread.daemon = True
        _calculation_thread.start()

    def _calculate(self):
        while True:
            self._calculation_event.wait()  # Wait for the event to be set
            self._calculation_event.clear()  # Clear the event
            with self._calculation_lock:
                self.processed_frame = self._apply_filter(self._current_frame)

    def _apply_filter(self, frame):
        raise NotImplementedError("Subclasses must implement _apply_filter")


class MogOpenCV(BackSubProcessor):
    def __init__(self, history=10):
        super().__init__(history=history)
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=self._history, detectShadows=False)

    def _apply_filter(self, frame):
        return self.backSub.apply(frame)


class KnnOpenCV(BackSubProcessor):
    def __init__(self, history=10):
        super().__init__(history=history)
        self.backSub = cv2.createBackgroundSubtractorKNN(history=self._history, detectShadows=False)

    def _apply_filter(self, frame):
        return self.backSub.apply(frame)


class MovingAverage(BackSubProcessor):

    def __init__(self, history=10):
        super().__init__(history=history)
        self.backSub = moving_average_module.MovingAverage(history)

    def _apply_filter(self, frame):
        frame = np.array(frame, dtype=np.uint8)
        self.backSub.apply(frame)
        print("Hello")
        return frame


class MovingAverages(BackSubProcessor):
    def __init__(self, sampling_rate=0, history=10, omega_a=.2, omega_i=.8, omega_c=.5,
                 calculation_type=ThreshCalculationTyp.MEDIAN_WEIGHTED,
                 thresholding_typ=ThreshHoldTyp.ADAPTIV, treshhold_manual=120):
        super().__init__(history=history)
        self._omega_a = omega_a
        self._omega_i = omega_i
        self._omega_c = omega_c
        self._threshold_typ = thresholding_typ
        self._threshold = treshhold_manual
        self._calculation_typ = calculation_type

    def __frame(self, frame):
        if self._threshold_typ == ThreshHoldTyp.ADAPTIV:
            thresh = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -2)
        elif self._threshold_typ == ThreshHoldTyp.OTSU:
            if self._thresh_ticker == self._thresh_ticks2_new_thresh:
                self._thresh_ticker = 0
                self._thresh_ticker += 1
                thresh, _ = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        elif self._threshold_typ == ThreshHoldTyp.MANUAL:
            _, thresh = cv2.threshold(frame, self._threshold, 255, cv2.THRESH_BINARY)
        return thresh

    def _median_filter(self, _):
        return np.median(self._frame_queue, axis=0).astype(np.uint8)

    def _weighted_median_filter(self, frame):
        median = np.median(self._frame_queue, axis=0).astype(np.uint8)
        background = np.multiply(self._omega_a, frame) + np.multiply(self._omega_i, median)
        return np.divide(background, self._omega_c).astype(np.uint8)

    def _mean_filter(self, _):
        return np.mean(self._frame_queue, axis=0).astype(np.uint8)

    def _weighted_mean_filter(self, frame):
        mean = np.mean(self._frame_queue, axis=0).astype(np.uint8)
        background = np.multiply(self._omega_a, frame) + np.multiply(self._omega_i, mean)
        return np.divide(background, self._omega_c).astype(np.uint8)

    def _apply_filter(self, frame):
        if self._calculation_typ == ThreshCalculationTyp.MEDIAN:
            self._calculated_value = self._median_filter(frame)
        elif self._calculation_typ == ThreshCalculationTyp.MEDIAN_WEIGHTED:
            self._calculated_value = self._weighted_median_filter(frame)
        elif self._calculation_typ == ThreshCalculationTyp.MEAN:
            self._calculated_value = self._mean_filter(frame)
        elif self._calculation_typ == ThreshCalculationTyp.MEAN_WEIGHTED:
            self._calculated_value = self._weighted_mean_filter(frame)
        result_frame = cv2.absdiff(self._calculated_value, frame)
        return self.__frame(result_frame)


BackSubProcessors = {
    BackSubTyp.MOG_OPEN_CV: MogOpenCV(),
    BackSubTyp.KNN_OPEN_CV: KnnOpenCV(),
    BackSubTyp.MOVING_AVERAGE: MovingAverage(10)
}

"""
class GMM(BackSubProcessor):

    def __init__(self, sampling_rate=0, n_frames=10, learning_rate=.01, threshold=.25):
        super().__init__(sampling_rate=sampling_rate, n_frames=n_frames)
        self.bg_models = []
        self.is_initialized = False

    def initialize(self):
        for i in range(Config.SCREEN_HEIGHT):
            row = []
            for j in range(Config.SCREEN_WIDTH):
                row.append({
                    "weight": np.full(self._n_frames, 1.0 / self._n_frames),
                    "means": np.zeros(self._n_frames),
                    "var": np.ones(self._n_frames)
                })
            self.bg_models.append(row)

    def _apply_filter(self, frame):
        pass
        
    
moving_average = MovingAverages(
    sampling_rate=0,
    n_frames=10,
    omega_a=.2,
    omega_i=.8,
    omega_c=.5,
    calculation_type=ThreshCalculationTyp.MEDIAN_WEIGHTED,
    thresholding_typ=ThreshHoldTyp.OTSU,
    treshhold_manual=130
)
"""
