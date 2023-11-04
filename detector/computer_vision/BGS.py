import threading

import cv2
import numpy as np
from enum import Enum
from collections import deque
from concurrent.futures import ThreadPoolExecutor


class BackSubTyp(Enum):
    MOG_OPEN_CV = 0
    KNN_OPEN_CV = 1
    SELF_IMPLEMENTED_BACK_SUB = 2
    MOVING_AVERAGE = 3


class BackSubProcessor:
    def __init__(self, sampling_rate=-1, n_frames=0):
        self.processed_frame = None
        self._current_frame = None
        self._queue_changed = False
        self._frame_queue = deque()
        self._filter_executor = ThreadPoolExecutor(max_workers=2)
        self._sampling_rate = sampling_rate
        self._sampling_ticks = 0
        self._n_frames = n_frames
        self._calculation_lock = threading.Lock()
        self._calculation_event = threading.Event()
        self._calculated_value = 0
        self._threshold = 0
        self._thresh_ticker = 0
        self._thresh_ticks2_new_thresh = 15

    def _update_queue(self, frame):
        previous_length = len(self._frame_queue)
        if self._sampling_rate < 0:
            pass
        elif self._sampling_rate == 0:
            self._frame_queue.append(frame)
        elif self._sampling_rate > 0:
            if self._sampling_ticks % self._sampling_rate == 0:
                self._frame_queue.append(frame)
                self._sampling_ticks = 0
            else:
                self._sampling_ticks += 1
        if previous_length < len(self._frame_queue):
            self._queue_changed = True
        else:
            self._queue_changed = False
        print(previous_length)
        if len(self._frame_queue) > 10:
            self._frame_queue.popleft()

    def apply(self, frame):
        self._current_frame = frame
        self._update_queue(frame)
        self._thresh_ticker += 1
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

    def _frame(self, frame):
        self._thresh_ticker += 1
        # print(self._thresh_ticker)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # if self._thresh_ticker >= self._thresh_ticks2_new_thresh:
        #    self._thresh_ticker = 0
        #    self._threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -5)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        # thresh = cv2.bitwise_and(thresh, self._threshold)
        return thresh


class MogOpenCV(BackSubProcessor):
    def __init__(self):
        super().__init__()
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=10, detectShadows=False)

    def _apply_filter(self, frame):
        return self.backSub.apply(frame)


class KnnOpenCV(BackSubProcessor):
    def __init__(self):
        super().__init__()
        self.backSub = cv2.createBackgroundSubtractorKNN(history=10, detectShadows=False)

    def _apply_filter(self, frame):
        return self.backSub.apply(frame)


class MovingAverage(BackSubProcessor):
    def __init__(self, sampling_rate=0, n_frames=10, omega_a=0.1, omega_i=0.9, omega_c=0.5):
        super().__init__(sampling_rate=sampling_rate, n_frames=n_frames)
        self._omega_a = omega_a
        self._omega_i = omega_i
        self._omega_c = omega_c

    def weighted(self):
        pass

    def unweighted(self):
        pass

    def _apply_filter(self, frame):
        # if self._queue_changed:
        self._calculated_value = np.median(self._frame_queue, axis=0).astype(np.uint8)

        result_frame = cv2.absdiff(frame, self._calculated_value)

        return self._frame(result_frame)


class ExperimentalFilterType(Enum):
    MOVING_AVERAGE = 0
    WEIGHTED_MOVING_AVERAGE = 1
    TEMPORAL_MEDIAN_FILTER = 2
    WEIGHTED_MEDIAN_FILTER = 3


class SimpleAverageFunctions(BackSubProcessor):

    def __init__(self, experimental_filter_typ, n_frames, sampling_rate, omega_a=0.2, omega_i=0.8,
                 omega_c=0.5):
        super().__init__(sampling_rate=sampling_rate, n_frames=n_frames)

        self._omega_a = omega_a
        self._omega_i = omega_i
        self._omega_c = omega_c

        self._threshold = 0
        self.thresh_calculated = 0
        self._thresh_ticker = 0
        self._thresh_ticks2_new_thresh = 15

        self._calculated_value = 0

        self._filter_type = {
            ExperimentalFilterType.MOVING_AVERAGE: self._simple_moving_average,
            ExperimentalFilterType.WEIGHTED_MOVING_AVERAGE: self._moving_average_by_cv_modern_approach,
            ExperimentalFilterType.TEMPORAL_MEDIAN_FILTER: self._simple_temporal_median_filter,
            ExperimentalFilterType.WEIGHTED_MEDIAN_FILTER: self._weighted_median_filter
        }.get(experimental_filter_typ)

    def _make_frame_with_threshold(self, frame):
        self._thresh_ticker += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if self._thresh_ticker == self._thresh_ticks2_new_thresh:
            self._thresh_ticker = 0
            self._threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -4)
        # _, thresh2 = cv2.threshold(gray, 125, 255, cv2.THRESH_BINARY_INV)
        # thresh = cv2.bitwise_and(thresh, self._threshold)
        return thresh

    def __frame(self, frame):
        return self._filter_executor.submit(self._make_frame_with_threshold,
                                            frame).result()

    def _simple_temporal_median_filter(self, _):
        return np.median(self._frame_queue, axis=0).astype(np.uint8)

    def _weighted_median_filter(self, frame):
        median = np.median(self._frame_queue, axis=0).astype(np.uint8)
        return ((self._omega_a * frame + self._omega_i * median) / self._omega_c).astype(np.uint8)

    def _moving_average_by_cv_modern_approach(self, frame):
        mean = np.mean(self._frame_queue, axis=0).astype(np.uint8)
        return ((self._omega_a * frame + self._omega_i * mean) / self._omega_c).astype(np.uint8)

    def _simple_moving_average(self, _):
        return np.mean(self._frame_queue, axis=0).astype(np.uint8)

    def _apply_filter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if self._queue_changed:
            self._calculated_value = self._filter_type(gray)
        result_frame = cv2.absdiff(self._calculated_value, gray)
        return self.__frame(result_frame)


"""
    def apply(self, frame):
        self._current_frame = frame
        self._update_queue(frame)
        # self._kde(frame)
        self.calculate_values()
        result_frame = cv2.absdiff(frame, self._calculated_value)
        self.processed_frame = self.__frame(result_frame)
"""

self_implemented = SimpleAverageFunctions(
    ExperimentalFilterType.TEMPORAL_MEDIAN_FILTER,
    sampling_rate=10,
    n_frames=10
)

BackSubProcessors = {
    BackSubTyp.MOG_OPEN_CV: MogOpenCV(),
    BackSubTyp.KNN_OPEN_CV: KnnOpenCV(),
    BackSubTyp.SELF_IMPLEMENTED_BACK_SUB: self_implemented,
    BackSubTyp.MOVING_AVERAGE: MovingAverage(sampling_rate=0, n_frames=10)
}
