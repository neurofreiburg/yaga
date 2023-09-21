from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'sinus_training'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        n_trials = 2
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 10
        inter_trial_interval_max = 10

        # max_force = 0.07
        # target_force = 0.035
        max_force = 0.09
        target_force = 0.04
        sinus_frequency = 0.1
        sinus_amplitude = 0.03

        pre_phase_duration = 3
        ramp_up_phase_duration = 5
        sinus_phase_duration = 20
        ramp_down_phase_duration = 5
        post_phase_duration = 3

        info_text = self.registerObject(GO.Text('prepare for force ramp up & down', scale_x=0.1, scale_y=0.1, color='white'))
        traffic_light_green = self.registerObject(GO.Image('traffic_light_green.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_yellow = self.registerObject(GO.Image('traffic_light_yellow.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_red = self.registerObject(GO.Image('traffic_light_red.png', scale_x=0.2, scale_y=0.2*1.68))
        bar = self.registerObject(GO.BarWithSinusTarget(pos_y=-0.2, bar_width=0.2, bar_height=0.8, target_width=0.35, target_height=0.02,
                                                    high_value=max_force, pre_phase_duration=pre_phase_duration, ramp_up_phase_duration=ramp_up_phase_duration,
                                                    sinus_phase_duration=sinus_phase_duration, sinus_frequency=sinus_frequency, sinus_amplitude=sinus_amplitude,
                                                    ramp_down_phase_duration=ramp_down_phase_duration, post_phase_duration=post_phase_duration, ramp_value=target_force))




        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)
        butter = SP.ButterFilter(4, 5)
        bar.controlStateWithLSLStream('quattrocento', channels=[64])
        bar.addSignalProcessingToLSLStream(max_normalization, channels=[64])
        bar.addSignalProcessingToLSLStream(butter, channels=[64])

        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]
            trial_script_items.extend([ScriptItem(name='info_text', time=0, time_type='rel', rel_name='trial_start', actions=[info_text.activate]),
                                        ScriptItem(name='traffic_light_red', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, traffic_light_red.activate]),
                                        ScriptItem(name='traffic_light_yellow', time=5, time_type='rel', rel_name='trial_start', actions=[traffic_light_red.deactivate, traffic_light_yellow.activate]),
                                        ScriptItem(name='traffic_light_greeb', time=7, time_type='rel', rel_name='trial_start', actions=[traffic_light_yellow.deactivate, traffic_light_green.activate]),
                                        ScriptItem(name='start_ramp', time=9, time_type='rel', rel_name='trial_start', actions=[traffic_light_green.deactivate, bar.activate, bar.startAnimation]),
                                        ScriptItem(name='trial_end', wait_for_signal=GO.BarWithSinusTarget.BAR_FINISHED, actions=[bar.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
