# Integration with Lab Streaming Layer (LSL)

## LSL Input Streams

YAGA can read LSL streams and use them to control graphical and auditory objects. You can set up the LSL control with the methods **control[pos\|scale\|color\|state]WithLSLStream** and **controlWithLSLStream** for graphical objects and auditory objects, respectively. If supported by the objects, they can also be controlled by multiple LSL streams by using the methods **control[…]WithLSLStream<u>s</u>.** See [Control of Graphical Objects](paradigm_scripting.md#control-of-graphical-objects) and [Control of Auditory Objects](paradigm_scripting.md#control-of-auditory-objects) for details. [Signal processing](paradigm_scripting.md#signal-processing) of the LSL streams is also possible.

YAGA is agnostic to the signal source as long as the LSL signals are streamed with a regular sampling rate.

LSL streams can also be used as triggers for [script items](paradigm_scripting.md#script-items). In that case, the LSL streams must have an irregular sampling rate (aka event marker streams).

## LSL Output Streams

If a script item has a name set, an LSL event marker is generated when the script item is triggered. YAGA creates the LSL stream _yaga_ for this purpose, which contains the event markers. The marker itself is the script item name. _yaga_ is an LSL stream with an irregular sampling rate and a string data format. This allows YAGA trigger events to be recorded along with LSL data streams.

LSL input streams can also be relayed to LSL output streams. This is useful if graphical or auditory objects are controlled with processed LSL streams, and one wants to record the processed streams. To set up a stream relay use the method **relayLSLSignals** on the respective graphical or auditory object. For example:

``` Python
feedback = self.registerObject(GO.Ball())
feedback.controlPosWithLSLStream('streamA', channels=[0, 1])
feedback.relayLSLSignals(lsl_in_signals=['streamA'], channels=[[0, 1]], lsl_out_signal='yaga_streamA')
```

Set the parameter _lsl_in_signals_ to a list of LSL streams which should be relayed for the associated representation object. Set _channels_ to a list of channel indices for each relayed LSL stream (i.e., a list of lists). Set the LSL output stream name with _lsl_out_signal_. All relayed LSL streams are collected in one LSL output stream.

## 3<sup>rd</sup> party LSL Software

### Supported Devices

A large number of devices like bio-amplifiers, motion capture systems, eye trackers, or input devices are supported by LSL. See <https://labstreaminglayer.readthedocs.io/info/supported_devices.html> for a list of devices.

### Data Recording

The LSL streams can be saved to the hard disk in the [XDF format](https://github.com/sccn/xdf) using [LabRecorder](https://github.com/labstreaminglayer/App-LabRecorder). The data recording can be manually started and stopped in LabRecorder. Lab Recorder also supports remote control via the UDP port. YAGA supports Lab Recorder's remote control interface and can automatically set the XDF file name and path, and start and stop a recording.

To enable remote control in your paradigm file, you need to:

-   specify the root directory of the XDF files and a task name as class variables in your Paradigm class (_root_dir_, _task_name_)
-   set the parameter _lsl_recorder_remote_control_ to _True_ when you initialise the Paradigm’s parent class
-   optionally, you can specify the hostname and port of the Lab Recorder instance when you initialise the Paradigm’s parent class (_lsl_recorder_host_, _lsl_recorder_port_)

For example:

``` Python
class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('studies') / Path('StudyA')
    task_name = 'condition1'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True)
```

When you start YAGA, you need to additionally specify the subject code, session number and run number as this information is used to build the XDF file name and send to Lab Recorder:

`python yaga.py --paradigm YOURPARADIGM --subject ABC --session 1 --run 3`

In the above example, YAGA configures Lab Recorder to save all available LSL streams to the file _\studies\StudyA\ABC_S001\task_condition1_003.xdf_ in your home directory.

### Online Data Visualisation

The BrainVision LSL Viewer, developed by Brain Products GmbH, is a handy tool for inspecting and monitoring LSL streams and checking the signal quality.

See the websites:

-   <https://pressrelease.brainproducts.com/lsl-viewer>

-   https://www.brainproducts.com/downloads/more-software/#utilities

### Offline Data Visualization

[SigViewer](https://github.com/cbrnr/sigviewer) allows inspecting XDF files.

### Loading Data in Matlab

#### Matlab Importer

To load the XDF data files into Matlab use [Matlab Importer](https://github.com/xdf-modules/xdf-Matlab).

Here is some example code to load an XDF file in Matlab:



``` Matlab
xdf_data = load_xdf(‘data_file_1.xdf’);
get_stream_idx = @(stream_name, xdf) find(arrayfun(@(stream) strcmp(stream{1}.info.name, stream_name), xdf)); % helper function to get the stream index by the stream name

% get the YAGA events
yaga_idx = get_stream_idx('yaga', xdf_data);
yaga_events = xdf_data{yaga_idx}.time_series;
yaga_timestamps = xdf_data{yaga_idx}.time_stamps;

% get the data stream
datastream_idx = get_stream_idx('the-stream', xdf_data);
stream_fs = str2double(xdf_data{datastream_idx}.info.nominal_srate);
stream_data = xdf_data{datastream_idx}.time_series'; % \[samples x channels\]
stream_timestamps = xdf_data{datastream_idx}.time_stamps;
```

#### EEGlab

One can use [EEGlab](https://sccn.ucsd.edu/eeglab) to open XDF files and conduct extensive analyses. You must first install one of the following plugins via _File_ -> _Manage EEGLAB extensions_:

- xdfimport
- Mobilab

Note that only the _Mobilab_ plugin allows to resample multiple streams to a common sampling rate.
