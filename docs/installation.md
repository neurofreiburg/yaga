# Installation

YAGA supports Linux, Mac or Windows (tested with macOS 13, Windows 10; Linux support is experimental). YAGA requires Python version \>= 3.9. To install Python on Windows, you can use the _Anaconda Individual Edition_ from (<https://www.anaconda.com>). The following Python packages are required:

-   numpy
-   scipy
-   panda3d
-   pmw
-   pylsl
-   pyxdf
-   rtmixer
-   nidaqmx

You can install the packages with the command _conda_. When a package is not available via _conda_, you can use the package installer _pip_ (which can be installed with _conda_).

If you require sound output, you need to install _PortAudio_. In Linux, you can use your local package manager to install _PortAudio_; on Mac, you can use _Homebrew_. In Windows, _PortAudio_ is included in the _sounddevice_ library, which is a dependency of _rtmixer_.

YAGA itself does not require any particular installation step. Simply copy all files and directories to a destination of your choice.
