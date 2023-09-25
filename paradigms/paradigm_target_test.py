from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        fb = self.registerObject(GO.Bar(pos_y=-0.7, bar_width=0.4, bar_height=1.4, frame_width=0.025, target_width=0.6, target_height=0.025, high_value=1, target_value=0.8, target_online_control=False))
        # fb = self.registerObject(GO.Arrow(target_value=0.25, pos_y=-0.65, arrow_length=1, line_width=0.05, head_size=0.2, target_size=0.15, target_online_control=False))


        # fb.controlStateWithLSLStream('MouseControllerStream', channels=[0,0,1])
        fb.controlStateWithLSLStreams(['MouseControllerStream', 'MouseControllerStream'], channels=[0,1])
        fb.activate()

        self.script = [ScriptItem(name='trial_start', time=5, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ScriptItem(name='trial_start', time=10, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ScriptItem(name='trial_start', time=15, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ScriptItem(name='trial_start', time=20, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ScriptItem(name='trial_start', time=30, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ScriptItem(name='trial_start', time=60, time_type='abs', actions=[fb.updateTargetValueFromLSLStream]),
                       ]
