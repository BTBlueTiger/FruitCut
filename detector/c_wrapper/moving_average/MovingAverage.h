// CWrapperProject.h : Include file for standard system include files,
// or project specific include files.

#pragma once

//C++ includes
#include <iostream>

//OpenCV includes
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp>

//Pybind11 Includes
#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <pybind11/cast.h>
#include <pybind11/stl_bind.h>
#include <pybind11/pytypes.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>

//Local includes
#include "./numpy_converter/ndarray_converter.h"

namespace py = pybind11;

class MovingAverage {
private:

	std::deque<cv::Mat> frame_deque;
	int history;
	NDArrayConverter ndarrayConverter;

	void update_queue(cv::Mat& frame);
	void calculate_median();

public:
	MovingAverage(const int history);
	~MovingAverage();

	py::array_t<uint8_t> apply(py::array_t<uint8_t>& frame);
	
};

// TODO: Reference additional headers your program requires here.
