﻿// MovingAverage.cpp : Defines the entry point for the application.
//

#include "MovingAverageHistory.h"

namespace py = pybind11;

MovingAverageHistory::MovingAverageHistory(const int history, const int threshold_t, const int thresholdManual)
{
	std::cout << "Initialized MovingAverage Instance of Moving average" << std::endl;
    this->history = history;
    std::cout << "Amount of Frames" << history << std::endl;
    this->thresholdType = static_cast<ThresholdType>(threshold_t);
    // Array of frames
    this->frames = new cv::Mat[history];
    if (threshold_t == ThresholdType::MANUAL)
    {
        this->thresholdManual = thresholdManual;
    }
    else
    {
        this->thresholdManual = 0;
    }
};

MovingAverageHistory::~MovingAverageHistory()
{
    delete[] this->frames;
}

void MovingAverageHistory::updateQueue(cv::Mat& frame)
{
    this->frames[this->currentIndex] = frame;
    uint8_t next_index = this->currentIndex + 1;
    this->currentIndex = next_index % this->history;
}


void MovingAverageHistory::calculateMedian()
{
    cv::Mat allFrames;
    // Concat all frames
    cv::vconcat(*this->frames, allFrames);
    cv::medianBlur(allFrames, this->median, 1);     
}

void MovingAverageHistory::thresholdFrame(cv::Mat& src, cv::Mat& dst)
{
    // Switch betweehn the thresholdtypes available
    switch (this->thresholdType)
    {
    case ThresholdType::ADAPTIVE:
        cv::adaptiveThreshold(src, dst, 255, cv::ADAPTIVE_THRESH_GAUSSIAN_C, cv::THRESH_BINARY, 11, -4);
        break;
    case ThresholdType::MANUAL:
        cv::threshold(src, dst, this->thresholdManual, 255, cv::THRESH_BINARY);
        break;
    default:
        break;
    }
    
}

py::array_t<uint8_t> MovingAverageHistory::apply(py::array_t<uint8_t>& frame) {
    cv::Mat cv_img;
    cv::Mat gray_img;
    cv::Mat diff_img;
    cv::Mat thresh;
    PyObject* frame_ptr = frame.ptr();

    try
    {
        // Convert np.array to OpenCV matrix
        this->ndarrayConverter.toMat(frame_ptr, cv_img);
        // Make an grayscale
        cv::cvtColor(cv_img, gray_img, cv::COLOR_BGR2GRAY);
        this->updateQueue(gray_img);
        // Calculate Median
        this->calculateMedian();
        cv::Mat background;
        cv::addWeighted(gray_img, 0.2, this->median, 0.8, 0, background);
        // Difference
        cv::absdiff(gray_img, background, diff_img);
        // make the threshold
        this->thresholdFrame(diff_img, thresh);
    }
    catch (const cv::Exception& e)
    {
        std::cerr << "OpenCV Error: " << e.what() << std::endl;
    }
    try {
        // Convert the matrix back
       auto ndArray =  this->ndarrayConverter.toNDArray(thresh);
       return py::reinterpret_borrow<py::array_t<uint8_t>>(ndArray);
    }
    catch (...)
    {
        std::cout << "Couldnt make the np array" << std::endl;
        return frame;
    }
}


PYBIND11_MODULE(moving_average_history_module, m)
{
    NDArrayConverter::init_numpy();
    m.doc() = "pybind11 example plugin"; // optional module docstring
    py::class_<MovingAverageHistory>(m, "MovingAverageHistory")
        .def(py::init<const int, const int, const int>(), "Initialize a MovingAverage with a specific length of history")
        .def("apply", &MovingAverageHistory::apply);
}
