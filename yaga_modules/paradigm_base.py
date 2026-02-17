from collections import namedtuple
from pathlib import Path
import sys
import time
import socket
import pylsl
import pymonctl


ScriptItem = namedtuple('ScriptItem', ('name', 'time', 'time_type', 'rel_name', 'wait_for_signal', 'wait_for_lsl_marker', 'actions'), defaults=(None, None, 'abs', None, None, None, None))


class ParadigmBase:

    def __init__(self, paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost', lsl_recorder_port=22345,
                 nidaqmx_trigger_line=None, nidaqmx_trigger_event='trial_start', nidaqmx_trigger_high_duration=0.1,
                 nidaqmx_analog_input_channels=None, nidaqmx_analog_input_min_vals=None, nidaqmx_analog_input_max_vals=None):
        if nidaqmx_analog_input_channels is None:
           nidaqmx_analog_input_channels = []
        self.interface_objects = []
        self.script = None
        self.signals = {}
        self.lsl_markers = {}
        self.lsl_marker_inlet = None
        self.lsl_marker_channel = None
        self.lsl_recorder_remote_control = lsl_recorder_remote_control
        self.lsl_recorder_host = lsl_recorder_host
        self.lsl_recorder_port = lsl_recorder_port
        self.nidaqmx_trigger_event = nidaqmx_trigger_event
        self.nidaqmx_trigger_line = nidaqmx_trigger_line
        self.nidaqmx_trigger_high_duration = nidaqmx_trigger_high_duration
        if not (len(nidaqmx_analog_input_channels) == len(nidaqmx_analog_input_min_vals) == len(nidaqmx_analog_input_max_vals)):
           raise Exception('the lists "nidaqmx_analog_input_channels", "nidaqmx_analog_input_min_vals", and "nidaqmx_analog_input_max_vals" must have the same length')
        self.nidaqmx_analog_input_channels = nidaqmx_analog_input_channels
        self.nidaqmx_analog_input_min_vals = nidaqmx_analog_input_min_vals
        self.nidaqmx_analog_input_max_vals = nidaqmx_analog_input_max_vals
        self.paradigm_variables = paradigm_variables

        # we need to create the LSL outlet here (instead of YAGA:initTask) so that the initialization code of the paradigm child has access to it
        if nidaqmx_analog_input_channels:
            lsl_nidaq_info = pylsl.StreamInfo('yaga_nidaq', 'Timeseries', len(nidaqmx_analog_input_channels), pymonctl.getPrimary().frequency, 'float32', "yaga_nidaq")
            self.lsl_nidaq_outlet = pylsl.StreamOutlet(lsl_nidaq_info)
        else:
            self.lsl_nidaq_outlet = None

    def registerObject(self, object):
        self.interface_objects.append(object)
        return object

    def setSignal(self, signal):
        if signal:
            self.signals[signal] = True

    def removeSignal(self, signal):
        self.signals[signal] = False

    def checkForSignal(self, signal):
        return self.signals.get(signal, False)

    def listenForLSLMarkers(self, lsl_stream_name, lsl_marker_channel=0):
        print('connecting to LSL stream %s...' % lsl_stream_name)
        lsl_info = pylsl.resolve_byprop('name', lsl_stream_name, timeout=15)
        if not lsl_info:
            raise Exception('timeout: LSL stream "%s" not found' % lsl_stream_name)
        if len(lsl_info) > 1:
            raise Exception('found more than one LSL stream with name "%s"' % lsl_stream_name)
        self.lsl_marker_inlet = pylsl.StreamInlet(lsl_info[0], recover=True)
        self.lsl_marker_channel = lsl_marker_channel
        print('connected')

    def readLSLMarkers(self):
        if self.lsl_marker_inlet:
            while(True):
                sample, _ = self.lsl_marker_inlet.pull_sample(timeout=0.0)
                if sample == None:
                    break
                else:
                    self.lsl_markers[sample[self.lsl_marker_channel]] = True

    def checkForLSLMarker(self, lsl_marker):
        return self.lsl_markers.get(lsl_marker, False)

    def removeLSLMarker(self, lsl_marker):
        self.lsl_markers[lsl_marker] = False

    def startLSLRecorder(self):
        if self.lsl_recorder_remote_control:
            try:
                self.root_dir
                self.task_name
            except:
                raise Exception('"root_dir" or "task_name" is not defined as a class variable')

            if not 'subject' in self.paradigm_variables:
                raise Exception('Command line parameter "--subject" is not specified. See help with "-?".')
            if not 'session' in self.paradigm_variables:
                raise Exception('Command line parameter "--session" is not specified. See help with "-?".')
            if not 'run' in self.paradigm_variables:
                raise Exception('Command line parameter "--run" is not specified. See help with "-?".')
            subject = self.paradigm_variables['subject']
            session = self.paradigm_variables['session']
            run = self.paradigm_variables['run']

            # build file used to store LSL data
            file = Path('%s_S%.3d' % (subject, session)) / Path('task_%s_run_%.3d.xdf' % (self.task_name, run))

            print('starting LSL recorder')
            try:
                s = socket.create_connection((self.lsl_recorder_host, self.lsl_recorder_port))
                time.sleep(2) # wait for all LSL outlets to be announced
                s.sendall("update\n".encode())
                time.sleep(1) # needed for LabRecorder
                s.sendall("select all\n".encode())
                time.sleep(1) # needed for LabRecorder
                s.sendall(("filename {root:%s} {template:%s}\n" % (self.root_dir, file)).encode())
                time.sleep(1) # needed for LabRecorder
                s.sendall("start\n".encode())
                time.sleep(1) # needed for LabRecorder
                s.sendall("start\n".encode())
            except ConnectionRefusedError as err:
                print('ERROR: cannot connect to LSL recorder at %s:%d' % (self.lsl_recorder_host, self.lsl_recorder_port))
                sys.exit()
            print('connected')

    def stopLSLRecorder(self):
        if self.lsl_recorder_remote_control:
            print('stopping LSL recorder')
            try:
                s = socket.create_connection((self.lsl_recorder_host, self.lsl_recorder_port))
                s.sendall(b"stop\n")
            except ConnectionRefusedError as err:
                print('ERROR: cannot connect to LSL recorder at %s:%d' % (self.lsl_recorder_host, self.lsl_recorder_port))
                sys.exit()
