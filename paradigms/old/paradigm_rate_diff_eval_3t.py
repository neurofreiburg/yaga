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
    task_name = 'ratediff_eval'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        diff_fb_lowpass_frq = 5 # [Hz]
        force_fb_lowpass_frq = 10 # [Hz]
        integrated_fb_highpass_frq = 0.05 # [Hz]

        target_1_force = 0.025
        target_2_force = 0.0325
        target_3_force = 0.04
        targets_force_range = 0.004
        target_1_y_pos = 0.3

        expected_rate_difference = 0.8 # channel_0 - channel_1
        expected_difference_range = 6 # -range/2 -> blue; 0 -> white; +range/2 -> red

        n_trials = 10
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 5
        inter_trial_interval_max = 10
        eval_duration = 10 # [s]
        # inter_trial_interval_min = 1
        # inter_trial_interval_max = 1
        # eval_duration = 1 # [s]

        start_y_pos = -0.3
        y_per_force = (target_1_y_pos - start_y_pos)/target_1_force
        target_2_y_pos = start_y_pos + y_per_force*target_2_force
        target_3_y_pos = start_y_pos + y_per_force*target_3_force
        target_height = y_per_force*targets_force_range*0.5
        target_width = 0.5

        class1 = self.registerObject(GO.Text("\u2199", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # lower left
        class2 = self.registerObject(GO.Text("\u2198", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # lower right
        class3 = self.registerObject(GO.Text("\u2190", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # middle left
        class4 = self.registerObject(GO.Text("\u2192", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # middle right
        class5 = self.registerObject(GO.Text("\u2196", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # upper left
        class6 = self.registerObject(GO.Text("\u2197", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='white')) # upper right
        cross = self.registerObject(GO.Cross(pos_y=start_y_pos, scale_x=0.1, scale_y=0.1, color='white', depth=2))
        force_target_1 = self.registerObject(GO.Box(pos_x=0, pos_y=target_1_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        force_target_2 = self.registerObject(GO.Box(pos_x=0, pos_y=target_2_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        force_target_3 = self.registerObject(GO.Box(pos_x=0, pos_y=target_3_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        # integrated_feedback = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.05, scale_y=0.05, color='white'))
        direct_feedback = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.03, scale_y=0.03, color='lime'))

        # direct_feedback.controlPosWithLSLStream('quattrocento', channels=[65, 64]) # force signal
        # direct_feedback.controlPosWithLSLStream('quattrocento', channels=[1, 0]) # EMG signal
        # direct_feedback.controlColorWithLSLStream('pop_rates', channel=0)
        # direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        # direct_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 0]) # rate diff + EMG signal

        # integrated_feedback.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal

        direct_feedback.relayLSLSignals(lsl_in_signals=['pop_rates', 'quattrocento'], channels=[[0], [64]], lsl_out_signal='direct_fb')
        # integrated_feedback.relayLSLSignals(lsl_in_signals=['pop_rates', 'quattrocento'], channels=[[0], [64]], lsl_out_signal='integrated_fb')


        # direct feedback: map MU rate difference to [-1, 1] (i.e. subtract channel 1 (MU B) from channel 0 (MU A), and convert result to range -1/1)
        butter_diff = SP.ButterFilter(2, diff_fb_lowpass_frq)
        invert_channel = SP.Scaler(scale=-1)
        sum_channels = SP.Sum()
        # convert_range = SP.Scaler(scale=2/expected_difference_range, pre_offset=-expected_rate_difference) # for color mapping ([-diff range/2, dff range/2] -> [-1, 1])
        # range_limit = SP.Limit(min_val=-1, max_val=1)
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
        map_force = SP.LinearMap(0, target_1_force, start_y_pos, target_1_y_pos)
        constant = SP.Constant(0)
        direct_feedback.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(butter_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(map_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(constant, channels=[65], lsl_stream_name='quattrocento')

        # direct feedback processing (EMG power feedback)
        # max_normalization = SP.MaxAvgPowerNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', range(0,64), prefilter_cutoff_frqs=[50, 500])
        # butter_force = SP.ButterFilter(2, force_fb_lowpass_frq)
        # map_force = SP.LinearMap(0, target_force, 0, target_y_pos)
        # constant = SP.Constant(0)
        # direct_feedback.addSignalProcessingToLSLStream(max_normalization, channels=range(0, 64), lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(butter_force, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(map_force, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(constant, channels=[1], lsl_stream_name='quattrocento')

        # # integrated feedback (integrate MU rate difference signal)
        # int_butter = SP.ButterFilter(2, integrated_fb_highpass_frq, filter_type='highpass')
        # int_invert_channel = SP.Scaler(scale=-1)
        # int_sum_channels = SP.Sum()
        # # int_convert_range = SP.Scaler(scale=2/expected_difference_range, pre_offset=-expected_rate_difference) # for color mapping ([-diff range/2, dff range/2] -> [-1, 1])
        # # int_range_limit = SP.Limit(min_val=-1, max_val=1)
        # int_convert_range = SP.Scaler(scale=target_width*2/expected_difference_range, pre_offset=-expected_rate_difference) # for x-position mapping ([-diff range/2, diff range/2] -> [-target_width, target_width])
        # int_range_limit = SP.Limit(min_val=-target_width, max_val=target_width)
        # int_integrator = SP.Integrate(factor=0.01)
        # integrated_feedback.addSignalProcessingToLSLStream(int_invert_channel, channels=[1], lsl_stream_name='pop_rates')
        # integrated_feedback.addSignalProcessingToLSLStream(int_sum_channels, channels=[0, 1], lsl_stream_name='pop_rates')
        # integrated_feedback.addSignalProcessingToLSLStream(int_convert_range, channels=[0], lsl_stream_name='pop_rates')
        # integrated_feedback.addSignalProcessingToLSLStream(int_range_limit, channels=[0], lsl_stream_name='pop_rates')
        # integrated_feedback.addSignalProcessingToLSLStream(int_integrator, channels=[0], lsl_stream_name='pop_rates')
        # integrated_feedback.addSignalProcessingToLSLStream(int_butter, channels=[0], lsl_stream_name='pop_rates')

        # # integrated feedback (force control)
        # int_max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)
        # int_butter_force = SP.ButterFilter(2, force_fb_lowpass_frq)
        # int_map_force = SP.LinearMap(0, target_1_force, start_y_pos, target_1_y_pos)
        # int_constant = SP.Constant(0)
        # integrated_feedback.addSignalProcessingToLSLStream(int_max_normalization, channels=[64], lsl_stream_name='quattrocento')
        # integrated_feedback.addSignalProcessingToLSLStream(int_butter_force, channels=[64], lsl_stream_name='quattrocento')
        # integrated_feedback.addSignalProcessingToLSLStream(int_map_force, channels=[64], lsl_stream_name='quattrocento')
        # integrated_feedback.addSignalProcessingToLSLStream(int_constant, channels=[65], lsl_stream_name='quattrocento')


        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]

            trial_class = random.randint(1,6);
            if trial_class == 1:
                class_item = class1
            elif trial_class == 2:
                class_item = class2
            elif trial_class == 3:
                class_item = class3
            elif trial_class == 4:
                class_item = class4
            elif trial_class == 5:
                class_item = class5
            elif trial_class == 6:
                class_item = class6

            trial_script_items.extend([ScriptItem(name='class' + str(trial_class), time=0, time_type='rel', rel_name='trial_start', actions=[class_item.activate]),
                                        ScriptItem(name='eval_start', time=3, time_type='rel', rel_name='trial_start', actions=[class_item.deactivate, cross.activate, force_target_1.activate, force_target_2.activate, force_target_3.activate, direct_feedback.activate]),
                                        ScriptItem(name='trial_end', time=eval_duration, time_type='rel', rel_name='eval_start', actions=[cross.deactivate, force_target_1.deactivate, force_target_2.deactivate, force_target_3.deactivate, direct_feedback.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
