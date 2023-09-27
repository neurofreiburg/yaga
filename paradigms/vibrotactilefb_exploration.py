from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('vibrotacilefb') / Path('data')
    task_name = 'exploration'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        control_phase_duration = 10

        max_rate_mu_A = 1;
        max_rate_mu_B = 1;
        mu_A_channel_idx = 0;
        mu_B_channel_idx = 1;
        mu_baseline_filter_lowpass_frq = 3;

        # # lock force
        # middle_bar_target_value = 0.5
        # max_value_middle_bar = 1;
        # force_amp_voltage_offset = 2.758e6 # more reliable
        # # force_amp_voltage_offset = 2.7606e6 # (has sticker)
        # force_channel = 1

        # lock rate
        middle_bar_target_value = 0.5
        max_value_middle_bar = 1;

        MU_bar_height = 0.8
        MU_bar_pos_x = 0.5
        MU_bar_pos_y = -0.3
        smiley_scale = 0.15

        bar_mu_A = self.registerObject(GO.Bar(pos_x=-MU_bar_pos_x, pos_y=MU_bar_pos_y, bar_width=0.2, bar_height=MU_bar_height, target_width=0.35, target_height=0.02, target_color='white', low_value=0.0, high_value=max_rate_mu_A, target_value=0))
        bar_mu_B = self.registerObject(GO.Bar(pos_x=MU_bar_pos_x, pos_y=MU_bar_pos_y, bar_width=0.2, bar_height=MU_bar_height, target_width=0.35, target_height=0.02, target_color='white', low_value=0.0, high_value=max_rate_mu_B, target_value=0))
        bar_middle = self.registerObject(GO.Bar(pos_x=0, pos_y=-0.3, bar_width=0.15, bar_height=0.5, target_width=0.25, target_height=0.02, bar_color='gold', low_value=0.0, high_value=max_value_middle_bar, target_value=middle_bar_target_value))

        # MU rates feedback
        butter_A = SP.ButterFilter(4, mu_baseline_filter_lowpass_frq)
        butter_B = SP.ButterFilter(4, mu_baseline_filter_lowpass_frq)
        copy_A_to_B = SP.CopyChannel(mu_A_channel_idx, mu_B_channel_idx)
        copy_B_to_A = SP.CopyChannel(mu_B_channel_idx, mu_A_channel_idx)

        bar_mu_A.controlStateWithLSLStream('MouseControllerStream', channels=[mu_A_channel_idx, mu_B_channel_idx]) # this is a hack but it works: copy value from channel A to B, filter it, and use channel B for the baseline
        bar_mu_A.addSignalProcessingToLSLStream(copy_A_to_B)
        bar_mu_A.addSignalProcessingToLSLStream(butter_A, channels=[mu_B_channel_idx])

        bar_mu_B.controlStateWithLSLStream('MouseControllerStream', channels=[mu_B_channel_idx, mu_A_channel_idx]) # this is a hack but it works: copy value from channel A to B, filter it, and use channel B for the baseline
        bar_mu_B.addSignalProcessingToLSLStream(copy_B_to_A)
        bar_mu_B.addSignalProcessingToLSLStream(butter_B, channels=[mu_A_channel_idx])

        # # # lock force
        # butter_force = SP.ButterFilter(4, 5)
        # force_max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        # bar_middle.controlStateWithLSLStream('MouseControllerStream', channels=[force_channel])
        # bar_middle.addSignalProcessingToLSLStream(force_max_normalization, channels=[force_channel])
        # bar_middle.addSignalProcessingToLSLStream(butter_force, channels=[force_channel])

        # lock rate
        average_rate = SP.Mean()
        bar_middle.controlStateWithLSLStream('MouseControllerStream', channels=[mu_A_channel_idx])
        bar_middle.addSignalProcessingToLSLStream(average_rate, channels=[mu_A_channel_idx, mu_B_channel_idx])


        # sequence definition
        self.script = [
            ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[bar_mu_A.activate, bar_mu_B.activate, bar_middle.activate, bar_mu_A.target_node.hide, bar_mu_B.target_node.hide]),
            ScriptItem(name='trial_end', time=control_phase_duration, time_type='rel', rel_name='trial_start', actions=[bar_mu_A.deactivate, bar_mu_B.deactivate, bar_middle.deactivate]),
            ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])
            ]
