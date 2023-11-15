import threading
from enum import Enum
from typing import Any

import cv2
import numpy as np
from numpy import dtype
from numpy.core import generic
from numpy.core.records import ndarray

from build.Release import moving_average_module


class BackSubTyp(Enum):
    """
    Simple class to distinguish between the background subtraction types
    """
    MOG_OPEN_CV = 0
    KNN_OPEN_CV = 1
    MOVING_AVERAGE_PYTHON = 2
    MOVING_AVERAGE_C_WRAPPER = 3


class ThreshHoldTyp(Enum):
    """Simple class to distinguish between the threshold types"""
    ADAPTIV = 0
    MANUAL = 1
    OTSU = 2


class ThreshCalculationTyp(Enum):
    MEDIAN = 0
    MEDIAN_WEIGHTED = 1
    MEAN = 2
    MEAN_WEIGHTED = 3


class BackSubProcessor:
    def __init__(self, history: int = 10, sampling_rate: int = 1):
        """
        Parent Class of Back Sub Processors
        Each processor creates its own thread
        Sequence of a normal calculation:
        1. apply(frame) to set the next frame.
        2. _calculate() A function that waits for an event to start
        the correct calculation.
        Prevents so-called race conditions.
        In addition, self._calculation_lock is used.
        3. processed.frame, our finished image is generated with the help of _apply_filter().
        Each processor must overwrite _apply_filter.
        The OpenCV use their apply method here.
        Other subclasses can use the threads in a similar way. Or extend the methods to save frames in apply,
        for example.
        :param history: The number of frames to consider for background calculation
        :param sampling_rate: The rate at which frames are sampled for background calculation
        """
        self.processed_frame = None
        self._calculation_lock = threading.Lock()
        self._calculation_event = threading.Event()
        self._current_frame = None
        self._history = history
        self._sampling_rate = sampling_rate

    def apply(self, frame):
        """
        Each processor sets the current frame here
        and signals the calculation thread to start
        """
        self._current_frame = frame
        self._calculation_event.set()

    def start_calculation_thread(self):
        # Simple starting the calculation thread
        _calculation_thread = threading.Thread(target=self._calculate)
        _calculation_thread.daemon = True
        _calculation_thread.start()

    def _calculate(self):
        while True:
            self._calculation_event.wait()  # Wait for the event to be set
            self._calculation_event.clear()  # Clear the event
            with self._calculation_lock:
                self.processed_frame = self._apply_filter(self._current_frame)

    def _apply_filter(self, frame) -> ndarray[Any, dtype[generic]]:
        """
        Should return ndarray[Any, dtype[generic]]
        or simple the processed Frame!
        Will raise a NotImplementedError
        """
        raise NotImplementedError("Subclasses must implement _apply_filter")


class MogOpenCV(BackSubProcessor):
    def __init__(self, history=10):
        """
        Simple MOG implementation of open cv
        """
        super().__init__(history=history)
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=self._history, detectShadows=False)

    def _apply_filter(self, frame):
        return self.backSub.apply(frame)


class KnnOpenCV(BackSubProcessor):
    def __init__(self, history=10):
        super().__init__(history=history)
        self.backSub = cv2.createBackgroundSubtractorKNN(history=self._history, detectShadows=False)

    def _apply_filter(self, frame):
        """
        Simple KNN implementation of open cv
        """
        return self.backSub.apply(frame)


class MovingAverageCWrapper(BackSubProcessor):
    def __init__(self, history):
        """
        Self implemented c wrapped moving average
        cv2.createBackgroundSubtractor Style
        """
        super().__init__(history=history)
        self.backSub = moving_average_module.MovingAverage(history, ThreshHoldTyp.MANUAL.value, 20)

    def _apply_filter(self, frame) -> ndarray[Any, dtype[generic]]:
        """
        returns a py::array_t<uint8_t> -> ndarray[Any, dtype[generic]]
        """
        return self.backSub.apply(frame)


class MovingAveragePython(BackSubProcessor):
    def __init__(self, history=10, omega_a=.2, omega_i=.8, omega_c=.5,
                 calculation_type=ThreshCalculationTyp.MEDIAN_WEIGHTED,
                 thresholding_typ=ThreshHoldTyp.ADAPTIV, threshold_manual=120):
        super().__init__(history=history)
        self._omega_a = omega_a
        self._omega_i = omega_i
        self._omega_c = omega_c
        self._threshold_typ = thresholding_typ
        self._threshold = threshold_manual
        self._calculation_typ = calculation_type
        self._frame_queue = []

    def __frame(self, frame):
        if self._threshold_typ == ThreshHoldTyp.ADAPTIV:
            thresh = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -2)
        else:
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
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self._frame_queue.append(frame)
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


# BackSubProcessor Dictionary
BackSubProcessors = {
    BackSubTyp.MOG_OPEN_CV: MogOpenCV(),
    BackSubTyp.KNN_OPEN_CV: KnnOpenCV(),
    BackSubTyp.MOVING_AVERAGE_C_WRAPPER: MovingAverageCWrapper(1000),
    BackSubTyp.MOVING_AVERAGE_PYTHON: MovingAveragePython()
}
