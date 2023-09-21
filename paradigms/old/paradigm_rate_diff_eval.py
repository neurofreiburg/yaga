from pathlib import Path
import numpy as np
from functools import partial
import random

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'ratediff_eval'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        diff_lowpass_frq = 5 # [Hz]
        force_lowpass_frq = 10 # [Hz]

        target_force = 0.02
        target_force_range = 0.01
        target_y_pos = 0.6

        # test: MU A: 11 Hz; MU B: 8.3 Hz
        expected_rate_difference = 0 # channel_0 - channel_1
        expected_difference_range = 3 # -range/2 -> blue; 0 -> white; +range/2 -> red

        n_trials = 10
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 5
        inter_trial_interval_max = 10
        eval_duration = 10 # [s]

        target_height = target_y_pos/target_force*target_force_range*0.5
        target_width = 0.5

        class1 = self.registerObject(GO.Text("<", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='blue'))
        class2 = self.registerObject(GO.Text(">", pos_x=0, pos_y=0, scale_x=0.7, scale_y=0.7, color='red'))
        cross = self.registerObject(GO.Cross(scale_x=0.1, scale_y=0.1, color='white', depth=2))
        target = self.registerObject(GO.Box(pos_x=0, pos_y=target_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        ball = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.05, scale_y=0.05, color='lime', depth=0))

        # ball.controlPosWithLSLStream('quattrocento', channels=[65, 64]) # force signal
        # ball.controlPosWithLSLStream('quattrocento', channels=[1, 0]) # EMG signal
        # ball.controlColorWithLSLStream('pop_rates', channel=0)
        # ball.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        ball.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64]) # rate diff + force signal
        # ball.controlPosWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 0]) # rate diff + EMG signal

        # map MU rate difference to [-1, 1]: subtract channel 1 (MU B) from channel 0 (MU A), and convert result to range -1/1
        butter_diff = SP.ButterFilter(2, diff_lowpass_frq)
        invert_channel = SP.Scaler(scale=-1)
        sum_channels = SP.Sum()
        # convert_range = SP.Scaler(scale=2/expected_difference_range, pre_offset=-expected_rate_difference) # for color mapping ([-diff range/2, dff range/2] -> [-1, 1])
        # range_limit = SP.Limit(min_val=-1, max_val=1)
        convert_range = SP.Scaler(scale=target_width*2/expected_difference_range, pre_offset=-expected_rate_difference) # for x-position mapping ([-diff range/2, diff range/2] -> [-target_width, target_width])
        range_limit = SP.Limit(min_val=-target_width, max_val=target_width)
        ball.addSignalProcessingToLSLStream(invert_channel, channels=[1], lsl_stream_name='pop_rates')
        ball.addSignalProcessingToLSLStream(sum_channels, channels=[0, 1], lsl_stream_name='pop_rates')
        ball.addSignalProcessingToLSLStream(butter_diff, channels=[0], lsl_stream_name='pop_rates')
        ball.addSignalProcessingToLSLStream(convert_range, channels=[0], lsl_stream_name='pop_rates')
        ball.addSignalProcessingToLSLStream(range_limit, channels=[0], lsl_stream_name='pop_rates')

        # ball processing for force feedback
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)
        butter_force = SP.ButterFilter(2, force_lowpass_frq)
        map_force = SP.LinearMap(0, target_force, 0, target_y_pos)
        constant = SP.Constant(0)
        ball.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        ball.addSignalProcessingToLSLStream(butter_force, channels=[64], lsl_stream_name='quattrocento')
        ball.addSignalProcessingToLSLStream(map_force, channels=[64], lsl_stream_name='quattrocento')
        ball.addSignalProcessingToLSLStream(constant, channels=[65], lsl_stream_name='quattrocento')

        # ball processing for EMG feedback
        # max_normalization = SP.MaxAvgPowerNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', range(0,64), prefilter_cutoff_frqs=[50, 500])
        # butter_force = SP.ButterFilter(2, force_lowpass_frq)
        # map_force = SP.LinearMap(0, target_force, 0, target_y_pos)
        # constant = SP.Constant(0)
        # ball.addSignalProcessingToLSLStream(max_normalization, channels=range(0, 64), lsl_stream_name='quattrocento')
        # ball.addSignalProcessingToLSLStream(butter_force, channels=[0], lsl_stream_name='quattrocento')
        # ball.addSignalProcessingToLSLStream(map_force, channels=[0], lsl_stream_name='quattrocento')
        # ball.addSignalProcessingToLSLStream(constant, channels=[1], lsl_stream_name='quattrocento')


        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]

            trial_class = random.randint(1,2);
            if trial_class == 1:
                class_item = class1
            elif trial_class == 2:
                class_item = class2

            trial_script_items.extend([ScriptItem(name='class' + str(trial_class), time=0, time_type='rel', rel_name='trial_start', actions=[class_item.activate]),
                                        ScriptItem(name='eval_start', time=3, time_type='rel', rel_name='trial_start', actions=[class_item.deactivate, cross.activate, target.activate, ball.activate]),
                                        ScriptItem(name='trial_end', time=eval_duration, time_type='rel', rel_name='eval_start', actions=[cross.deactivate, target.deactivate, ball.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
