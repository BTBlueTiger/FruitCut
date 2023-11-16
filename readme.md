# FruitCut
### Eigentlich jetzt viel mehr FruitCaught
####  OpenCV, Numpy und Pybind11 basierendes Computer Vision Spiel

## Kurzbeschreibung:
Fange Früchte mit dir als Fänger.
Da wo du stehst befindet sich ein Korb in der Mitte deines Umrisses
Aber pass auf das du nicht von den Bomben erwischt wirst

#### Viele Einstellungen werden in ./detector/Config.py gesetzt

## Benötigt:
Eine IP Webcam \
Wird über "IP_CAM" in ./detector/Config.py gesetzt


### Zum Builden:
1. CMake
2. Python
3. In diesem Repo VCPKG als Toolchain

### Mit VCPKG
```
./vcpkg install pybind11 opencv4 Python3
```

## Bauen von C++ Abhängigen Komponenten

```
mkdir build
cd build
```
Windows:
```
cmake.exe ../detector/c_wrapper -DCMAKE_TOOLCHAIN_FILE="<PATH_TO_VCPKG_DIR>/scripts/buildsystems/vcpkg.cmake"
```
Linux:
```
cmake ../detector/c_wrapper -DCMAKE_TOOLCHAIN_FILE="<PATH_TO_VCPKG_DIR>/scripts/buildsystems/vcpkg.cmake"
```
Letzter Schritt:
```
cmake --build . --config Release
```

Mit Pycharm lässt sich das Spiel nun einfach starten.
Mit nur Python gibt es noch ein paar Import Schwierigkeiten

### Python Libraries:
_Auch in requirements.txt zu sehen_

- numpy~=1.26.1
- pygame~=2.5.2
- opencv-python~=4.8.1.78
- setuptools~=65.5.0
- requests~=2.31.0 (Für die IP Webcam)
- moviepy~=1.0.3 (Umwandeln von Frames zu einem Video)

## Achtung:
Ohne **IP Webcam** zur Zeit nicht möglich.
Jedes Handy kann aber als IP Webcam fungieren mit der gleichnamigen App IP Webcam von **Pavel Khebovich**

# Ordner res:
 - In Res werden die Videos und Frames unter Capture gespeichert
 - Hier werden auch die Assets gespeichert
 - Unter PDF's sind die Folien als PDF gespeichert
 - Research soll Paper in Zusammenhang mit den einzelnen Meilensteinen sammeln


Dank an das Repo [https://github.com/edmBernard/pybind11_opencv_numpy.git](https://github.com/edmBernard/pybind11_opencv_numpy.git)
Es half sehr beim wrappen und auch der NDArrayConverter wird genutzt
