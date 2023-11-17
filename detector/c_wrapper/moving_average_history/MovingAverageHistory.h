// CWrapperProject.h : Include file for standard system include files,
// or project-specific include files.

#pragma once

// C++ includes
#include <iostream>
#include <algorithm>

// OpenCV includes
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp>

// Pybind11 Includes
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <pybind11/cast.h>
#include <pybind11/stl_bind.h>
#include <pybind11/pytypes.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>

// Local includes
#include "./numpy_converter/ndarray_converter.h"

namespace py = pybind11;

/*
 * Simple enum to distinguish between threshold types.
 */
enum ThresholdType {
    ADAPTIVE = 0,
    MANUAL = 1,
    OTSU = 2
};

/*
 * Background suppressor to separate the foreground from the background.
 */
class MovingAverageHistory {
private:
    // Our frames
    cv::Mat* frames;
    cv::Mat median;

    // Index of "history"
    uint8_t currentIndex = 0;

    // The variant of the threshold
    ThresholdType thresholdType;
    uint8_t thresholdManual;

    // Const values that should not change after first initialization
    size_t history;

    // Converter from: https://github.com/edmBernard/pybind11_opencv_numpy
    NDArrayConverter ndarrayConverter;

    /**
     * Update the queue with a new frame from a Python script.
     *
     * @param frame: A converted OpenCV Mat, typically using NDArrayConverter.
     */
    void updateQueue(cv::Mat& frame);

    /**
     * Calculate the current median with all frames.
     */
    void calculateMedian();

    /**
     * Apply thresholding to an image.
     *
     * @param src: Image to be thresholded.
     * @param dst: Resulting thresholded image.
     */
    void thresholdFrame(cv::Mat& src, cv::Mat& dst);

public:
    /**
     * The MovingAverage Constructor.
     *
     * @param history: How many frames should be used for background subtraction.
     * @param thresholdType: Type of the threshold, see ThresholdType enum.
     * @param manualThreshold: If the user sets the threshold manually, we need a manual threshold;
     *                        otherwise, it will be set to zero.
     */
    MovingAverageHistory(const int history, const int thresholdType, const int manualThreshold);
    ~MovingAverageHistory();

    /**
     * Main function called from Python.
     * Takes an image, calculates the rest, and returns a threshold image.
     *
     * @param frame: A numpy frame as a pybind11 array.
     *
     * @return A numpy frame for the Python application. On Error the same frame that was passed
     * 
     */
    py::array_t<uint8_t> apply(py::array_t<uint8_t>& frame);
};
