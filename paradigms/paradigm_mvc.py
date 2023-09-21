from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO


class Paradigm(ParadigmBase):

    task_name = 'mvc'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        n_trials = 3
        pre_paradigm_interval = 3
        post_paradigm_interval = 3
        inter_trial_interval_min = 10
        inter_trial_interval_max = 10
        mvc_duration = 5

        info_text = self.registerObject(GO.Text('prepare for maximum contraction', scale_x=0.1, scale_y=0.1, color='white'))
        countdown = self.registerObject(GO.Countdown(counter_start=mvc_duration, scale_x=0.5, scale_y=0.5, color='white'))
        traffic_light_green = self.registerObject(GO.Image('traffic_light_green.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_yellow = self.registerObject(GO.Image('traffic_light_yellow.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_red = self.registerObject(GO.Image('traffic_light_red.png', scale_x=0.2, scale_y=0.2*1.68))

        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]
            trial_script_items.extend([ScriptItem(name='info_text', time=0, time_type='rel', rel_name='trial_start', actions=[info_text.activate]),
                                       ScriptItem(name='traffic_light_red', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, traffic_light_red.activate]),
                                       ScriptItem(name='traffic_light_yellow', time=5, time_type='rel', rel_name='trial_start', actions=[traffic_light_red.deactivate, traffic_light_yellow.activate]),
                                       ScriptItem(name='traffic_light_green', time=7, time_type='rel', rel_name='trial_start', actions=[traffic_light_yellow.deactivate, traffic_light_green.activate]),
                                       ScriptItem(name='start_counter', time=9, time_type='rel', rel_name='trial_start', actions=[traffic_light_green.deactivate, countdown.activate]),
                                       ScriptItem(name='trial_end', wait_for_signal=GO.Countdown.COUNTDOWN_FINISHED, actions=[])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
