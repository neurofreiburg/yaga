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
    task_name = 'hf_mod_eval'

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

        n_trials = 16
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 3
        inter_trial_interval_max = 7
        cue_delay = 5 # [s]
        trial_duration = 12 # [s]

        start_y_pos = -0.3
        y_per_force = (target_y_pos - start_y_pos)/target_force
        target_height = y_per_force*targets_force_range*0.5
        target_width = 0.5

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)

        cue_y_pos = (target_y_pos - start_y_pos)/2 + start_y_pos
        left_cue = self.registerObject(GO.Text("\u2190", pos_x=0, pos_y=cue_y_pos, scale_x=0.25, scale_y=0.25, color='white')) # arrow left
        right_cue = self.registerObject(GO.Text("\u2192", pos_x=0, pos_y=cue_y_pos, scale_x=0.25, scale_y=0.25, color='white')) # arrow right

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

        n_classes = 2
        assert n_trials % n_classes == 0, "number of trials must be a multiple of number of classes (i.e. 2)"
        trial_classes = np.tile(np.arange(1, n_classes + 1), (int(n_trials/n_classes), 1)).reshape((-1))
        np.random.shuffle(trial_classes) # inplace
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]

            trial_class = trial_classes[trial_idx]
            if trial_class == 1:
                # rest
                cue = left_cue
                class_name = 'class_rest'
            elif trial_class == 2:
                # task
                cue = right_cue
                class_name = 'class_task'


            trial_script_items.extend([ScriptItem(name=class_name, time=0, time_type='rel', rel_name='trial_start', actions=[cross.activate, force_target.activate, direct_feedback.activate]),
                                        ScriptItem(name='cue', time=cue_delay, time_type='rel', rel_name='trial_start', actions=[cue.activate]),
                                        ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cue.deactivate, cross.deactivate, force_target.deactivate, direct_feedback.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
