from pathlib import Path
import numpy as np
from functools import partial
import random

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'ratediff_expV2'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        diff_fb_lowpass_frq = 3 # [Hz]
        force_fb_lowpass_frq = 3 # [Hz]

        target_force = 0.04
        targets_force_range = 0.005
        target_y_pos = 0.5

        expected_rate_difference = 0.5 # channel_0 - channel_1
        expected_difference_range = 5 # -range/2 <-> +range/2

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        trial_duration = 180 # [s]

        start_y_pos = -0.3
        y_per_force = (target_y_pos - start_y_pos)/target_force
        target_height = y_per_force*targets_force_range*0.5
        target_width = 0.5

        cross = self.registerObject(GO.Cross(pos_y=start_y_pos, scale_x=0.1, scale_y=0.1, color='white', depth=2))
        force_target = self.registerObject(GO.Box(pos_x=0, pos_y=target_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        direct_feedback = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.03, scale_y=0.03, color='lime'))

        # direct_feedback.controlPosWithLSLStream('quattrocento', channels=[65, 64]) # force signal
        # direct_feedback.controlPosWithLSLStream('quattrocento', channels=[1, 0]) # EMG signal
        # direct_feedback.controlColorWithLSLStream('pop_rates', channel=0)
        # direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        # direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 0]) # rate diff + EMG signal

        direct_feedback.relayLSLSignals(lsl_in_signals=['pop_rates', 'quattrocento'], channels=[[0], [64]], lsl_out_signal='direct_fb')

        # direct feedback: map MU rate difference to [-target_width, target_width]
        butter_diff = SP.ButterFilter(2, diff_fb_lowpass_frq)
        invert_channel = SP.Scaler(scale=-1)
        sum_channels = SP.Sum()
        convert_range = SP.Scaler(scale=target_width*2/expected_difference_range, pre_offset=-expected_rate_difference) # for x-position mapping ([-diff range/2, diff range/2] -> [-target_width, target_width])
        range_limit = SP.Limit(min_val=-target_width, max_val=target_width)
        direct_feedback.addSignalProcessingToLSLStream(invert_channel, channels=[1], lsl_stream_name='pop_rates')
        direct_feedback.addSignalProcessingToLSLStream(sum_channels, channels=[0, 1], lsl_stream_name='pop_rates')
        direct_feedback.addSignalProcessingToLSLStream(butter_diff, channels=[0], lsl_stream_name='pop_rates')
        direct_feedback.addSignalProcessingToLSLStream(convert_range, channels=[0], lsl_stream_name='pop_rates')
        direct_feedback.addSignalProcessingToLSLStream(range_limit, channels=[0], lsl_stream_name='pop_rates')

        # direct feedback processing (force feedback)
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)
        butter_force = SP.ButterFilter(2, force_fb_lowpass_frq)
        map_force = SP.LinearMap(0, target_force, start_y_pos, target_y_pos)
        constant = SP.Constant(0)
        direct_feedback.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(butter_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(map_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(constant, channels=[65], lsl_stream_name='quattrocento')

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[cross.activate, force_target.activate, direct_feedback.activate]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cross.deactivate, force_target.deactivate, direct_feedback.deactivate]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
