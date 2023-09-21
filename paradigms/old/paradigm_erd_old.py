from pathlib import Path
import numpy as np
from functools import partial
import random
import codecs

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'erd'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        max_force = 0.07
        low_target_force = 0.0
        high_target_force = 0.05

        n_trials = 20
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 3
        inter_trial_interval_max = 6
        cue_delay = 4 # [s]
        trial_duration = 9 # [s]

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)

        rest_cue = self.registerObject(GO.Text("rest", pos_x=0, pos_y=0.7, scale_x=0.25, scale_y=0.25, color='white'))
        task_cue = self.registerObject(GO.Text("MI", pos_x=0, pos_y=0.7, scale_x=0.25, scale_y=0.25, color='white'))
        bar = self.registerObject(GO.Bar(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02, bar_color='lime', target_color='red', high_value=max_force, target_value=0))

        # force feedback
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], force_amp_voltage_offset)
        butter = SP.ButterFilter(4, 3)
        bar.controlStateWithLSLStream('quattrocento', channels=[64])
        bar.addSignalProcessingToLSLStream(max_normalization, channels=[64])
        bar.addSignalProcessingToLSLStream(butter, channels=[64])

        n_classes = 4
        assert n_trials % n_classes == 0, "number of trials must be a multiple of number of classes (i.e. 4)"
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
                # low target + rest
                cue = rest_cue
                bar_target_value = low_target_force
                class_name = 'class_low_rest'
            elif trial_class == 2:
                # low target + task
                cue = task_cue
                bar_target_value = low_target_force
                class_name = 'class_low_task'
            elif trial_class == 3:
                # high target + rest
                cue = rest_cue
                bar_target_value = high_target_force
                class_name = 'class_high_rest'
            elif trial_class == 4:
                # high target + task
                cue = task_cue
                bar_target_value = high_target_force
                class_name = 'class_high_task'

            trial_script_items.extend([ScriptItem(name=class_name, time=0, time_type='rel', rel_name='trial_start', actions=[partial(bar.updateTargetValue, bar_target_value), bar.activate]),
                                        ScriptItem(name='cue', time=cue_delay, time_type='rel', rel_name='trial_start', actions=[cue.activate]),
                                        ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cue.deactivate, bar.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
