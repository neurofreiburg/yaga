from pathlib import Path
import numpy as np
from functools import partial
import random

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'hf_mod_exp'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        force_fb_lowpass_frq = 3 # [Hz]
        band_frqs = [35, 60] # [Hz]
        power_lowpass_frq = 1 # [Hz]
        target_force = 0.05
        targets_force_range = 0.01
        target_y_pos = 0.5

        bandpower_offset = 1e3
        bandpower_range = 6e3 # -range/2 <-> +range/2

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        trial_duration = 180 # [s]

        start_y_pos = -0.3
        y_per_force = (target_y_pos - start_y_pos)/target_force
        target_height = y_per_force*targets_force_range*0.5
        target_width = 0.5

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)

        cross = self.registerObject(GO.Cross(pos_y=start_y_pos, scale_x=0.1, scale_y=0.1, color='white', depth=2))
        force_target = self.registerObject(GO.Box(pos_x=0, pos_y=target_y_pos, scale_x=target_width, scale_y=target_height, color='gray'))
        direct_feedback = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.03, scale_y=0.03, color='lime'))

        direct_feedback.controlPosWithLSLStream('quattrocento', channels=[0, 64]) # EMG-GFP + force signal

        direct_feedback.relayLSLSignals(lsl_in_signals=['quattrocento'], channels=[[0, 64]], lsl_out_signal='direct_fb')

        # # direct feedback: map EMG-GFP rate difference to [-target_width, target_width]
        # gfp_hp = SP.ButterFilter(4, gfp_highpass_frq, filter_type='highpass')
        # carrier_bp = SP.ButterFilter(6, carrier_bandpass_frqs, filter_type='bandpass')
        # envelope_lp = SP.ButterFilter(4, envelope_lowpass_frq, filter_type='lowpass')
        # envelope_power = SP.Power(2)
        # gfp = SP.StdDev()
        # convert_range = SP.Scaler(scale=target_width*2/demod_signal_range, pre_offset=-demod_signal_offset) # for x-position mapping ([-demod_signal_range/2, demod_signal_range/2] -> [-target_width, target_width])
        # range_limit = SP.Limit(min_val=-target_width, max_val=target_width)
        # emg_channel_list = list(range(64))
        # # bad_emg_channels = 21
        # # emg_channel_list.remove(bad_emg_channels)
        # direct_feedback.addSignalProcessingToLSLStream(gfp_hp, channels=emg_channel_list, lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(gfp, channels=emg_channel_list, lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(carrier_bp, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(envelope_power, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(envelope_lp, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(convert_range, channels=[0], lsl_stream_name='quattrocento')
        # direct_feedback.addSignalProcessingToLSLStream(range_limit, channels=[0], lsl_stream_name='quattrocento')

        # direct feedback: map EMG bandpower to [-target_width target_width]
        mean_emg = SP.Mean()
        band_filter = SP.ButterFilter(4, band_frqs, filter_type='bandpass')
        power_filter = SP.ButterFilter(2, power_lowpass_frq, filter_type='lowpass')
        power = SP.Power(2)
        convert_range = SP.Scaler(scale=target_width*2/bandpower_range, pre_offset=-bandpower_offset) # for x-position mapping ([-demod_signal_range/2, demod_signal_range/2] -> [-target_width, target_width])
        range_limit = SP.Limit(min_val=-target_width, max_val=target_width)
        emg_channel_list = list(range(64))
        # bad_emg_channels = 21
        # emg_channel_list.remove(bad_emg_channels)
        direct_feedback.addSignalProcessingToLSLStream(mean_emg, channels=emg_channel_list, lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(band_filter, channels=[0], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(power, channels=[0], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(power_filter, channels=[0], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(convert_range, channels=[0], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(range_limit, channels=[0], lsl_stream_name='quattrocento')

        # direct feedback processing (force feedback)
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], force_amp_voltage_offset)
        butter_force = SP.ButterFilter(2, force_fb_lowpass_frq)
        map_force = SP.LinearMap(0, target_force, start_y_pos, target_y_pos)
        force_range_limit = SP.Limit(min_val=start_y_pos, max_val=1)
        constant = SP.Constant(0)
        direct_feedback.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(butter_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(map_force, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(force_range_limit, channels=[64], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(constant, channels=[65], lsl_stream_name='quattrocento')

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[cross.activate, force_target.activate, direct_feedback.activate]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cross.deactivate, force_target.deactivate, direct_feedback.deactivate]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
