// MovingAverage.cpp : Defines the entry point for the application.
//

#include "MovingAverage.h"

namespace py = pybind11;

MovingAverage::MovingAverage(const int threshold_t, const int thresholdManual)
{
	std::cout << "Initialized MovingAverage Instance of Moving average" << std::endl;
    this->thresholdType = static_cast<ThresholdType>(threshold_t);

    if (threshold_t == ThresholdType::MANUAL)
    {
        this->thresholdManual = thresholdManual;
    }
    else
    {
        this->thresholdManual = 0;
    }
};

MovingAverage::~MovingAverage()
{
}

void MovingAverage::thresholdFrame(cv::Mat& src, cv::Mat& dst)
{
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

py::array_t<uint8_t> MovingAverage::apply(py::array_t<uint8_t>& frame) {
    PyObject* frame_ptr = frame.ptr();

    try
    {
        // Convert np.array to OpenCV matrix
        this->ndarrayConverter.toMat(frame_ptr, this->currentFrame);
        cv::cvtColor(this->currentFrame.clone(), this->gray_img, cv::COLOR_BGR2GRAY);

        // Check if initialization has been done
        if (!isInit)
        {
            this->background = this->gray_img.clone();
            isInit = true;
        }

        // Set weight
        cv::addWeighted(this->gray_img, 0.1, this->background, 0.9, 0, this->background);

        // Difference
        cv::absdiff(this->gray_img, this->background, this->subtracted);

        // Make the threshold
        this->thresholdFrame(this->subtracted, this->subtracted);
    }
    catch (const cv::Exception& e)
    {
        std::cerr << "OpenCV Error: " << e.what() << std::endl;
    }
    try {
        // Convert the matrix back
       auto ndArray =  this->ndarrayConverter.toNDArray(this->subtracted);
       return py::reinterpret_borrow<py::array_t<uint8_t>>(ndArray);
    }
    catch (...)
    {
        std::cout << "Couldn't make the np array" << std::endl;
        return frame;
    }
}



PYBIND11_MODULE(moving_average_module, m)
{
    NDArrayConverter::init_numpy();
    m.doc() = "pybind11 example plugin"; // optional module docstring
    // Convert cpp class to python class
    py::class_<MovingAverage>(m, "MovingAverage")
        .def(py::init<const int, const int>(), "Initialize a MovingAverage with a specific length of history")
        .def("apply", &MovingAverage::apply);
}
