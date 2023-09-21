from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'sinus'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        n_trials = 3
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 40
        inter_trial_interval_max = 50

        max_force = 0.2
        target_force = 0.1
        sinus_frequency = 0.2
        sinus_amplitude = 0.05
        arrow_angle = -37

        pre_phase_duration = 3
        ramp_up_phase_duration = 5
        sinus_phase_duration =30
        ramp_down_phase_duration = 5
        post_phase_duration = 3

        info_text = self.registerObject(GO.Text('prepare for force ramp up & down', scale_x=0.1, scale_y=0.1, color='white'))
        traffic_light_green = self.registerObject(GO.Image('traffic_light_green.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_yellow = self.registerObject(GO.Image('traffic_light_yellow.png', scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_red = self.registerObject(GO.Image('traffic_light_red.png', scale_x=0.2, scale_y=0.2*1.68))
        cross = self.registerObject(GO.Cross(pos_y=-0.2, scale_x=0.1, scale_y=0.1, color='black', depth=2))
        arrow = self.registerObject(GO.ArrowWithSinusTarget(pos_y=-0.2, angle=arrow_angle, arrow_length=1, target_size=0.1, hold_target_size=0.1,
                                                    low_value=0, high_value=max_force, pre_phase_duration=pre_phase_duration, ramp_up_phase_duration=ramp_up_phase_duration,
                                                    sinus_phase_duration=sinus_phase_duration, sinus_frequency=sinus_frequency, sinus_amplitude=sinus_amplitude, ramp_down_phase_duration=ramp_down_phase_duration,
                                                    post_phase_duration=post_phase_duration, start_value=0, ramp_value=target_force))

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64, 65], 2.761e6)
        butter = SP.ButterFilter(4, 5)
        arrow.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        arrow.addSignalProcessingToLSLStream(max_normalization, channels=[64, 65])
        arrow.addSignalProcessingToLSLStream(butter, channels=[64, 65])

        # butter = SP.ButterFilter(4, 1)
        # arrow.addSignalProcessingToLSLStream(butter, channels=[64, 65])

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
                                        ScriptItem(name='start_ramp', time=9, time_type='rel', rel_name='trial_start', actions=[traffic_light_green.deactivate, cross.activate, arrow.activate, arrow.startAnimation]),
                                        ScriptItem(name='trial_end', wait_for_signal=GO.ArrowWithSinusTarget.ARROW_FINISHED, actions=[cross.deactivate, arrow.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
