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

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'sndtriggtest'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.5)
        # super().__init__(paradigm_variables, lsl_recorder_remote_control=False)

        n_trials = 200
        pre_paradigm_interval = 15
        post_paradigm_interval = 5
        inter_trial_interval_min = 0.5
        inter_trial_interval_max = 1.5
        trial_duration = 1 # [s]

        box = self.registerObject(GO.Box(pos_y=0, scale_x=0.1, scale_y=0.1, color='white'))
        sound = self.registerObject(AO.Beep(beep_frequency=2000, beep_amplitude=2, beep_duration=0.1, beep_channels='both', delay=0.2))

        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[box.activate, sound.beep])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[box.activate, sound.beep])]

            trial_script_items.extend([ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[box.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
