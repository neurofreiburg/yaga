from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('jaime2023') / Path('data')
    task_name = 'trapezoid'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_event='trial_start', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.5)

        n_trials = 6
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 25
        inter_trial_interval_max = 35

        max_force = 0.22
        target_force_1 = 0.05
        target_force_2 = 0.1
        target_force_3 = 0.2

        pre_phase_duration = 3
        ramp_up_phase_duration = 5
        hold_phase_duration = 30
        ramp_down_phase_duration = 5
        post_phase_duration = 3

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)
        force_channel = 256

        info_text = self.registerObject(GO.Text('prepare for force ramp up & down', scale_x=0.1, scale_y=0.1, color='white'))
        bar_1 = self.registerObject(GO.BarWithRampTarget(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02,
                                                    high_value=max_force, pre_phase_duration=pre_phase_duration, ramp_up_phase_duration=ramp_up_phase_duration,
                                                    hold_phase_duration=hold_phase_duration, ramp_down_phase_duration=ramp_down_phase_duration,
                                                    post_phase_duration=post_phase_duration, ramp_value=target_force_1))
        bar_2 = self.registerObject(GO.BarWithRampTarget(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02,
                                                    high_value=max_force, pre_phase_duration=pre_phase_duration, ramp_up_phase_duration=ramp_up_phase_duration,
                                                    hold_phase_duration=hold_phase_duration, ramp_down_phase_duration=ramp_down_phase_duration,
                                                    post_phase_duration=post_phase_duration, ramp_value=target_force_2))
        bar_3 = self.registerObject(GO.BarWithRampTarget(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02,
                                                    high_value=max_force, pre_phase_duration=pre_phase_duration, ramp_up_phase_duration=ramp_up_phase_duration,
                                                    hold_phase_duration=hold_phase_duration, ramp_down_phase_duration=ramp_down_phase_duration,
                                                    post_phase_duration=post_phase_duration, ramp_value=target_force_3))
        attention_beep = self.registerObject(AO.Beep(beep_frequency=1000, beep_duration=0.5))
        
        # force feedback
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        butter_1 = SP.ButterFilter(4, 5)
        butter_2 = SP.ButterFilter(4, 5)
        butter_3 = SP.ButterFilter(4, 5)
        bar_1.controlStateWithLSLStream('quattrocento', channels=[force_channel])
        bar_1.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        bar_1.addSignalProcessingToLSLStream(butter_1, channels=[force_channel])
        bar_2.controlStateWithLSLStream('quattrocento', channels=[force_channel])
        bar_2.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        bar_2.addSignalProcessingToLSLStream(butter_2, channels=[force_channel])
        bar_3.controlStateWithLSLStream('quattrocento', channels=[force_channel])
        bar_3.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        bar_3.addSignalProcessingToLSLStream(butter_3, channels=[force_channel])

        # paradigm definition
        n_classes = 3
        assert n_trials % n_classes == 0, "number of trials must be a multiple of the number of classes (i.e. 3)"
        trial_classes = np.tile(np.arange(1, n_classes + 1), (int(n_trials/n_classes), 1)).reshape((-1))
        np.random.shuffle(trial_classes) # inplace
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[info_text.activate, attention_beep.beep])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[info_text.activate, attention_beep.beep])]

            trial_class = trial_classes[trial_idx]
            if trial_class == 1:
                bar = bar_1
                class_name = "force1"
            elif trial_class == 2:                
                bar = bar_2
                class_name = "force2"
            elif trial_class == 3:
                bar = bar_3
                class_name = "force3"
            trial_script_items.append(ScriptItem(name=class_name, time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, bar.activate, bar.startAnimation]))
            trial_script_items.append(ScriptItem(name='trial_end', wait_for_signal=GO.BarWithRampTarget.BAR_FINISHED, actions=[bar.deactivate]))
            self.script.extend(trial_script_items)

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
