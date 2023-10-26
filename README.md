# YAGA

**YAGA** is a presentation and paradigm scripting program for research experiments focusing on behavioural and neuroscience experiments.

**Features:**

-   presentation of visual and auditory stimuli
-   scripting of the paradigm sequence
-   integration with the Lab Steaming Layer (LSL) system
-   online control of graphical and sound objects with LSL streams
-   online processing of LSL streams
-   simple but extensible signal processing capabilities
-   multiplatform capability (Windows/Mac/Linux) (Linux support is experimental)

YAGA is written in Python and is based on the _Panda3D_ game engine. It can implement various experimental paradigms with a so-called _paradigm file_.

The paradigm file specifies the sequence of screen instructions, cues or stimuli. LSL _event markers_ can be sent to allow later time-locking to events such as stimulus presentation. LSL stream can also be used to control graphical or auditory objects. For example, the cursor position in target reaching task can be controlled with an LSL stream. YAGA can read LSL streams directly from amplifiers or intermediate signal processing applications. YAGA also allows signal processing of LSL streams.

All LSL streams can be recorded, with the LSL system ensuring the time synchronisation between the streams. Together with LSL, YAGA allows you to conduct scientific experiments or implement online control systems.

# Getting Help

* [read the docs](https://yaga.readthedocs.io)
* check open & closed [GitHub issues](https://github.com/neurofreiburg/yaga/issues)
* create a new [GitHub issue](https://github.com/neurofreiburg/yaga/issues)

# License

YAGA is released under the [GPLv3 license](license.md).

# Citing YAGA

If you use YAGA in your experiments, please cite the GitHub repository <https://github.com/neurofreiburg/yaga>.

# Contact

To get in touch with the developers, contact Patrick Ofner <patrick@ofner.science>, [Bernstein Center Freiburg](https://www.bcf.uni-freiburg.de) @ University of Freiburg.

# Acknowledgements

YAGA was supported by the EU FET Open project [NIMA](https://nima-project.eu).
