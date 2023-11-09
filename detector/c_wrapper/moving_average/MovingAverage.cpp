// CWrapperProject.cpp : Defines the entry point for the application.
//

#include "MovingAverage.h"

namespace py = pybind11;

MovingAverage::MovingAverage(const int history)
{
	std::cout << "Initialized MovingAverage Instance of CWrapperProject" << std::endl;
    this->history = history;
};

MovingAverage::~MovingAverage()
{

}

void MovingAverage::update_queue(cv::Mat& frame)
{
    this->frame_deque.push_back(frame);
    if (this->frame_deque.size() > this->history)
    {
        this->frame_deque.pop_front();
    }
    std::cout << this->frame_deque.size() << std::endl;
}

py::array_t<uint8_t> MovingAverage::apply(py::array_t<uint8_t>& frame) {
    cv::Mat cv_img;
    cv::Mat gray_img;
    PyObject* frame_ptr = frame.ptr();
    try
    {
        this->ndarrayConverter.toMat(frame_ptr, cv_img);
        cv::cvtColor(cv_img, gray_img, cv::COLOR_BGR2GRAY);
    }
    catch (const cv::Exception& e)
    {
        std::cerr << "OpenCV Error: " << e.what() << std::endl;
    }
    try {
       auto ndArray =  this->ndarrayConverter.toNDArray(gray_img);
       return py::reinterpret_borrow<py::array_t<uint8_t>>(ndArray);
    }
    catch (...)
    {
        std::cout << "Couldnt make the np array" << std::endl;
        return frame;
    }
}


/*
py::array_t<uint8_t> MovingAverage::apply(py::array_t<uint8_t>& frame) {
    // Convert numpy array aka py::array_t to cv::Mat
    auto buf = frame.request();
    int rows = buf.shape[0];
    int cols = buf.shape[1];
    // Create a cv:Mat out of the frame from Python's np.array
    cv::Mat bgr(rows, cols, CV_8U, buf.ptr);

    // Convert to grayscale
    cv::Mat grayScaleImg;
    cv::cvtColor(bgr, grayScaleImg, cv::COLOR_BGR2GRAY);

    cv::Mat thresh;
    cv::threshold(grayScaleImg, thresh, 120, 255, cv::THRESH_BINARY);

    this->update_queue(grayScaleImg);

    // Convert cv::Mat to a NumPy array aka py::array_t
    auto dtype = py::dtype::of<uint8_t>();
    py::array_t<uint8_t> result({ grayScaleImg.rows, grayScaleImg.cols });

    auto result_ptr = result.mutable_unchecked();
    for (int i = 0; i < thresh.rows; ++i) {
        for (int j = 0; j < thresh.cols; ++j) {
            result_ptr(i, j) = thresh.at<uint8_t>(i, j);
        }
    }

    return result;
}
*/




PYBIND11_MODULE(moving_average_module, m)
{
    NDArrayConverter::init_numpy();

    m.doc() = "pybind11 example plugin"; // optional module docstring
    py::class_<MovingAverage>(m, "MovingAverage")
        .def(py::init<const int>(), "Initialize a MovingAverage with a specific length of history")
        .def("apply", &MovingAverage::apply);
}