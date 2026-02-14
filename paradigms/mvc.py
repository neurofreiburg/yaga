from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.audio_objects as AO
import yaga_modules.graphic_objects as GO


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('studies') / Path('test') / Path('data')
    task_name = 'mvc'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        n_trials = 3
        pre_paradigm_interval = 3
        post_paradigm_interval = 3
        inter_trial_interval_min = 15
        inter_trial_interval_max = 15
        mvc_duration = 5

        info_text = self.registerObject(GO.Text('prepare for maximum contraction', scale_x=0.1, scale_y=0.1, color='white'))
        countdown = self.registerObject(GO.Countdown(counter_start=mvc_duration, scale_x=0.5, scale_y=0.5, color='white'))
        attention_beep = self.registerObject(AO.Beep(beep_frequency=2000, beep_amplitude=1, beep_duration=0.2))


        # sequence definition
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_start_time = pre_paradigm_interval
                trial_start_time_type = "abs"
                trial_start_time_ref = ""
            else:
                trial_start_time = np.random.uniform(inter_trial_interval_min, inter_trial_interval_max)
                trial_start_time_type = "rel"
                trial_start_time_ref = "trial_end"
            self.script.append(ScriptItem(name='trial_start', time=trial_start_time, time_type=trial_start_time_type, rel_name=trial_start_time_ref, actions=[attention_beep.beep, info_text.activate]))

            self.script.append(ScriptItem(name='start_counter', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, countdown.activate]))
            self.script.append(ScriptItem(name='trial_end', wait_for_signal=GO.Countdown.COUNTDOWN_FINISHED, actions=[]))

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
