# Installation

## Requirements

YAGA supports Linux, Mac or Windows (tested with macOS 13, Windows 10; Linux support is experimental). YAGA requires Python version \>= 3.9 (older versions do not work). To install Python on Windows, you can use the _Anaconda Individual Edition_ from (<https://www.anaconda.com>). The following Python packages are required:

-   numpy
-   scipy
-   panda3d
-   pmw
-   pylsl
-   pyxdf
-   rtmixer
-   nidaqmx

You can install the packages with the typical package managers _conda_ or _pip_.

If you require sound output, you need to install _PortAudio_. In Linux, you can use your local package manager to install _PortAudio_; on Mac, you can use _Homebrew_. In Windows, _PortAudio_ is included in the _sounddevice_ library, which is a dependency of _rtmixer_.

## Download

You can download the latest YAGA release from [GitHub](https://github.com/neurofreiburg/yaga/releases/latest). YAGA does not require any special installation steps. Copy the ZIP or TAR.GZ file to the desired directory and unpack it.
