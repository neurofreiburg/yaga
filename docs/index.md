# YAGA Documentation

**YAGA** is a presentation and paradigm scripting program for research experiments focusing on behavioural and neuroscience experiments.

**Features:**

-   presentation of visual and auditory stimuli
-   scripting of the paradigm sequence
-   integration with the Lab Steaming Layer (LSL) system
-   online control of graphical and sound objects with LSL signal streams
-   online processing of LSL signal streams
-   simple but extensible signal processing capabilities
-   multiplatform capability (Windows/Mac/Linux) (Linux support is experimental)

YAGA is written in Python and is based on the _Panda3D_ game engine. It can implement various experimental paradigms with a so-called _paradigm file_.

The paradigm file specifies the sequence of screen instructions, cues or stimuli. Optionally, the paradigm file can configure the control of graphical and auditory objects with _Lab Streaming Layer_ (LSL) streams. For example, the x/y position of a cursor in target reaching experiment could be controlled with a two-channel LSL stream. YAGA can read LSL streams directly from amplifiers or intermediate signal processing applications. YAGA also allows internal signal processing of LSL streams. Processed LSL streams can be relayed as LSL output streams. Moreover, YAGA outputs the paradigm sequence as _LSL event marker_ to allow later time-locking to events like stimuli presentation.

All input streams, processed LSL streams, and the paradigm sequence can then be recorded while the LSL system handles time synchronisation between the streams. Together with LSL, YAGA allows the conducting of scientific experiments or the implementation of online control systems.

# Citing YAGA
When you use YAGA in your experiments, please cite the GitHub repository <https://github.com/neurofreiburg/yaga>.