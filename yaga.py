#!/usr/bin/env python

"""
    YAGA is a paradigm presentation program for neuroscience experiments

    Copyright (C) 2023 patrick@ofner.science

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from importlib import import_module
import sys
import getopt
import math
import pylsl
from panda3d.core import WindowProperties, loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task



#%% set FPS
# FPS = 130
# from panda3d.core import loadPrcFileData
# configVars = """
# sync-video 0
# """
# loadPrcFileData("", configVars)
# from panda3d.core import ClockObject
# globalClock = ClockObject.getGlobalClock()
# globalClock.setMode(ClockObject.MLimited)
# globalClock.setFrameRate(FPS)


#%% parse command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], 'hmp:', ['help', 'maximize', 'paradigm=', 'subject=', 'session=', 'run=', 'var1=', 'var2=', 'var3='])
except getopt.GetoptError as err:
    print(err)
    print('use -h or --help to see available options')
    sys.exit(2)

maximize_window = False
paradigm_file = None

class CommandlineDict(dict):
    def __missing__(self, key):
        print('dictionary containing paradigm variables has no data for key "%s". Did you specify all required command line arguments? See %s --help for supported command line arguments.' % (key, sys.argv[0].removeprefix('./').removeprefix('.\\')))
        sys.exit(2)
paradigm_variables = CommandlineDict()

for opt, arg in opts:
    if opt in ('-h', '--help'):
        print('\n' + sys.argv[0].removeprefix('./').removeprefix('.\\') + ' -p PARADIGM [-m] [--subject STRING] [--session NUMBER] [--run NUMBER] [-h]\n')
        print('-p, --paradigm\t... paradigm file')
        print('-m, --maximize\t... maximize window')
        print('-h, --help\t... show help')
        print('\nthe following parameters can be used in the paradigm file to build, e.g., filenames or as general purpose variables:')
        print('--subject\t... subject code')
        print('--session\t... session number')
        print('--run\t\t... run number')
        print('--var1\t\t... general purpose variable 1')
        print('--var2\t\t... general purpose variable 2')
        print('--var3\t\t... general purpose variable 3')
        sys.exit(0)
    elif opt in ('-p', '--paradigm'):
        paradigm_file = arg.removesuffix('.py').removeprefix('./').removeprefix('.\\')
    elif opt in ('-m', '--maximize'):
        maximize_window = True
    elif opt == '--subject':
        paradigm_variables['subject'] = arg
    elif opt == '--session':
        if not arg.isdigit():
            print('session must be a number')
            sys.exit(2)
        paradigm_variables['session'] = int(arg)
    elif opt == '--run':
        if not arg.isdigit():
            print('run must be a number')
            sys.exit(2)
        paradigm_variables['run'] = int(arg)
    elif opt == '--var1':
        paradigm_variables['var1'] = arg
    elif opt == '--var2':
        paradigm_variables['var2'] = arg
    elif opt == '--var3':
        paradigm_variables['var3'] = arg
    else:
        raise Exception('unknown command line option: %s' % opt)

if paradigm_file is None:
    print('no paradigm file specified, see command line parameters with: "' + sys.argv[0].removeprefix('./').removeprefix('.\\') + ' --help"')
    sys.exit(2)
try:
    paradigm = import_module('.' + paradigm_file, 'paradigms')
except ImportError as err:
    print('error when loading paradigm file "%s": %s' % (paradigm_file, err))
    sys.exit(1)


#%% main class running yaga
class YAGA(ShowBase):

    def __init__(self, paradigm_variables, maximize_window=False):
        loadPrcFileData('', 'background-color 0.40 0.40 0.40')

        ShowBase.__init__(self)

        self.frame_script_items = []
        self.script_item_execution_times = {}
        self.start_time = None
        self.frame_signals = []

        display_width = base.pipe.getDisplayWidth()
        display_height = base.pipe.getDisplayHeight()
        base.disableMouse()
        base.setFrameRateMeter(False)
        props = WindowProperties()
        props.setUndecorated(False)
        props.setTitle('yaga')
        props.setCursorHidden(True)
        if maximize_window:
            props.setUndecorated(True)
            props.setSize(display_width, display_height)
            props.setFixedSize(True)
        else:
            props.setSize(int(display_width/2), int(display_height/2))
        base.win.requestProperties(props)

        # set up event handlers
        self.accept('escape', self.quit)
        self.accept('quit', self.quit)

        # run initialization code in a seperate one-time task (after the igloop) to prevent problems with the fullscreen mode
        self.task = taskMgr.add(self.initTask, 'initTask', sort=200)

    def initTask(self, task):

        # set up outgoing LSL stream for markers
        lsl_info = pylsl.StreamInfo('yaga', 'Markers', 1, pylsl.IRREGULAR_RATE, pylsl.cf_string, 'yaga_markers')
        self.lsl_marker_outlet = pylsl.StreamOutlet(lsl_info)

        # load paradigm
        self.paradigm = paradigm.Paradigm(paradigm_variables)

        # set-up NI-DAQmx
        if self.paradigm.nidaqmx_trigger_line:
            import nidaqmx
            try:
                self.nidaqmx_task = nidaqmx.Task('trigger')
                self.nidaqmx_task.do_channels.add_do_chan(self.paradigm.nidaqmx_trigger_line)

                # # initialize trigger port to low
                self.nidaqmx_task.start()
                self.nidaqmx_line_value = False
                self.nidaqmx_task.write(self.nidaqmx_line_value)
                self.nidaqmx_task.stop()
                self.nidaqmx_high_onset = 0
            except nidaqmx.DaqError as err:
                raise Exception('NI-DAQmx error: "%s"' % err)
        else:
            self.nidaqmx_task = None
            self.nidaqmx_line_value = None
            self.nidaqmx_high_onset = None

        # start LSL recorder (this is the most time intensive operation -> several seconds)
        self.paradigm.startLSLRecorder()

        # add main tasks
        # sort parameter: task with lower value execute sooner. "updateStates" should be the last task, so that all informations are available to the task. sort value must be between 1 and 19
        self.task = taskMgr.add(self.runScript, 'runScript', sort=1)
        self.task = taskMgr.add(self.readLSL, 'readLSL', sort=2)
        self.task = taskMgr.add(self.updateStates, 'updateStates', sort=3)

        # task for frame-synced execution time-related code (i.e. logging scipt item execution times and sending LSL events); this task has a high sort value so that it runs after the screen update task
        self.task = taskMgr.add(self.maintainExecutedScriptItems, 'maintainExecutedScriptItems', sort=100)

        return Task.done

    def runScript(self, task):
        if not self.start_time:
            self.start_time = pylsl.local_clock()
        time = pylsl.local_clock() - self.start_time

        script = self.paradigm.script
        self.frame_script_items = []
        run_actions = False
        if len(script) > 0:

            # check if it is time to activate a ScriptItem
            if script[0].time != None:
                assert isinstance(script[0].time, (int, float)), 'field "time" must be a number'
                if script[0].time_type == 'abs':
                    if time >= script[0].time:
                        run_actions = True
                elif script[0].time_type == 'rel':
                    if time >= self.script_item_execution_times.get(script[0].rel_name, math.inf) - self.start_time + script[0].time:
                        run_actions = True
                else:
                    raise Exception('field "time_type" is not supported: "%s"' % script[0].time_type)

            # if ScriptItem is waiting for a signal, check for it
            if script[0].wait_for_signal and self.paradigm.checkForSignal(script[0].wait_for_signal):
                run_actions = True
                self.paradigm.removeSignal(script[0].wait_for_signal)

            # if ScriptItem is waiting for an LSL marker, check for it
            if script[0].wait_for_lsl_marker and self.paradigm.checkForLSLMarker(script[0].wait_for_lsl_marker):
                run_actions = True
                self.paradigm.removeLSLMarker(script[0].wait_for_lsl_marker)

            if run_actions:
                # execute ScriptItem's actions
                for action in script[0].actions:
                    action()

                # save script item names for later when they are send via LSL
                if script[0].name:
                    assert isinstance(script[0].name, str), 'field "name" must be "None" or a string'
                    self.frame_script_items.append(script[0].name)

                # delete ScriptItem
                script.pop(0)

        else:
            messenger.send('quit')

        return Task.cont

    def maintainExecutedScriptItems(self, task):
        # this task should run immediately after the screen update
        local_time = pylsl.local_clock()

        # reset NI-DAQmx output to low
        if self.nidaqmx_task and self.nidaqmx_line_value and local_time - self.nidaqmx_high_onset >= self.paradigm.nidaqmx_high_duration:
            self.nidaqmx_task.start()
            self.nidaqmx_line_value = False
            self.nidaqmx_task.write(self.nidaqmx_line_value)
            self.nidaqmx_task.stop()

        # handle script items run within this frame
        for script_item_name in self.frame_script_items:
            # send script item as an LSL marker
            self.lsl_marker_outlet.push_sample([script_item_name], timestamp=local_time, pushthrough=True)

            # set NI-DAQmx output to high when the specified event/ScriptItem occurs
            if self.nidaqmx_task and script_item_name == self.paradigm.nidaqmx_event:
                self.nidaqmx_task.start()
                self.nidaqmx_line_value = True
                self.nidaqmx_task.write(self.nidaqmx_line_value)
                self.nidaqmx_task.stop()
                self.nidaqmx_high_onset = local_time

            # log execution time of script item
            self.script_item_execution_times[script_item_name] = local_time

        # handle signals yielded within this frame
        for signal in self.frame_signals:
            # send signal as an LSL marker
            self.lsl_marker_outlet.push_sample([signal], timestamp=local_time, pushthrough=True)

        return Task.cont

    def readLSL(self, task):
        # update interface objects linked to an LSL stream
        for interface_object in self.paradigm.interface_objects:
            interface_object.readLSLStream()

        # read LSL markers
        self.paradigm.readLSLMarkers()

        return Task.cont

    def updateStates(self, task):
        local_time = pylsl.local_clock()
        self.frame_signals = []
        for interface_object in self.paradigm.interface_objects:
            signal = interface_object.updateState(local_time)
            if signal:
                self.frame_signals.append(signal)
                self.paradigm.setSignal(signal)

        return Task.cont

    def quit(self):
        self.paradigm.stopLSLRecorder()
        print(taskMgr)
        sys.exit()


app = YAGA(paradigm_variables, maximize_window)
app.run()
