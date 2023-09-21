from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('jaime2023') / Path('data')
    task_name = 'auditory_stim'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_event='stimulus', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.5)

        n_trials = 4
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 25
        inter_trial_interval_max = 35

        # max_force = 0.12 # used in the first test experiment
        # target_force = 0.1 # used in the first test experiment
        max_force = 0.22
        target_force = 0.05

        pre_phase_duration = 0
        post_phase_duration = 5
        n_stimuli_per_trial = 10
        inter_stimulus_time_min = 4
        inter_stimulus_time_max = 8

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)
        force_channel = 256

        info_text = self.registerObject(GO.Text('prepare for force increase', scale_x=0.1, scale_y=0.1, color='white'))
        bar = self.registerObject(GO.Bar(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02, high_value=max_force, target_value=target_force))
        attention_beep = self.registerObject(AO.Beep(beep_frequency=1000, beep_duration=0.5))
        stimulus = self.registerObject(AO.Beep(beep_frequency=2000, beep_amplitude=2, beep_duration=0.1, beep_channels='both', delay=0.2))

        # force feedback
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        butter = SP.ButterFilter(4, 5)
        bar.controlStateWithLSLStream('quattrocento', channels=[force_channel])
        bar.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        bar.addSignalProcessingToLSLStream(butter, channels=[force_channel])

        # paradigm definition
        self.script = []
        for trial_idx in range(n_trials):
            # trial start
            if trial_idx == 0:
                self.script.append(ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[attention_beep.beep, info_text.activate]))
            else:
                self.script.append(ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[attention_beep.beep, info_text.activate]))
            self.script.append(ScriptItem(name='show_bar', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, bar.activate]))

            # auditory stimuli
            current_stimulus_time = pre_phase_duration # stimulus time is relative to bar activation time (which includes a pre phase)
            for stimulus_idx in range(n_stimuli_per_trial):
                current_stimulus_time = current_stimulus_time + np.random.uniform(inter_stimulus_time_min, inter_stimulus_time_max)
                self.script.append(ScriptItem(name='stimulus', time=current_stimulus_time, time_type='rel', rel_name='show_bar', actions=[stimulus.beep]))

            # trial end
            self.script.append(ScriptItem(name='trial_end', time=post_phase_duration, time_type='rel', rel_name='stimulus', actions=[bar.deactivate]))

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
