from pathlib import Path
import numpy as np
from functools import partial
import random
import codecs

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('studies') / Path('cimod') / Path('data')
    # root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'triggertest'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.5)

        n_trials = 100
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 1
        inter_trial_interval_max = 1
        cue_delay = 0 # [s]
        trial_duration = 0 # [s]
        math_random_number_interval = [50, 1000];

        start_y_pos = -0.3

        rest_cue = self.registerObject(GO.Text("rest", pos_x=0, pos_y=0.25, scale_x=0.2, scale_y=0.2, color='white'))
        foot_cue = self.registerObject(GO.Image("foot_task.png", pos_x=0, pos_y=0.25, scale_x=0.12, scale_y=None))
        hand_cue = self.registerObject(GO.Image("hands_task.png", pos_x=0, pos_y=0.25, scale_x=0.35, scale_y=None))
        math_cue = self.registerObject(GO.RandomNumber(interval=math_random_number_interval, pos_x=0, pos_y=0.25, scale_x=0.2, scale_y=0.2, color='white'))

        start = self.registerObject(GO.Box(pos_y=start_y_pos, scale_x=0.1, scale_y=0.005, color='white', depth=2))
        sound = self.registerObject(AO.Beep())

        n_classes = 4
        assert n_trials % n_classes == 0, "number of trials must be a multiple of number of classes (i.e. 2)"
        trial_classes = np.tile(np.arange(1, n_classes + 1), (int(n_trials/n_classes), 1)).reshape((-1))
        np.random.shuffle(trial_classes) # inplace
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]

            trial_class = trial_classes[trial_idx]
            if trial_class == 1:
                cue = rest_cue
                class_name = 'class_rest'
            elif trial_class == 2:
                cue = foot_cue
                class_name = 'class_foot'
            elif trial_class == 3:
                cue = hand_cue
                class_name = 'class_hand'
            elif trial_class == 4:
                cue = math_cue
                class_name = 'class_math'

            trial_script_items.extend([ScriptItem(name=class_name, time=0, time_type='rel', rel_name='trial_start', actions=[start.activate, sound.beep]),
                                        ScriptItem(name='cue', time=cue_delay, time_type='rel', rel_name='trial_start', actions=[cue.activate]),
                                        ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cue.deactivate, start.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
