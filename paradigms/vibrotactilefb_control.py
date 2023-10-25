from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('vibrotacilefb') / Path('data')
    task_name = 'control'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        n_trials = 10
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 3
        inter_trial_interval_max = 7
        cue_time_min = 10
        cue_time_max = 10
        control_phase_duration = 5

        max_rate_mu_A = 1;
        max_rate_mu_B = 1;
        mu_A_channel_idx = 0;
        mu_B_channel_idx = 1;
        mu_baseline_filter_lowpass_frq = 3;
        mu_baseline_mov_avg_window = 5; # alternative

        mu_stream_name = 'MouseControllerStream'

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
        smiley_pos_offset = 0.25

        bar_mu_A = self.registerObject(GO.Bar(pos_x=-MU_bar_pos_x, pos_y=MU_bar_pos_y, bar_width=0.2, bar_height=MU_bar_height, target_width=0.35, target_height=0.02, target_color='white', low_value=0.0, high_value=max_rate_mu_A, target_value=0, target_online_control=False))
        bar_mu_B = self.registerObject(GO.Bar(pos_x=MU_bar_pos_x, pos_y=MU_bar_pos_y, bar_width=0.2, bar_height=MU_bar_height, target_width=0.35, target_height=0.02, target_color='white', low_value=0.0, high_value=max_rate_mu_B, target_value=0, target_online_control=False))
        bar_middle = self.registerObject(GO.Bar(pos_x=0, pos_y=-0.3, bar_width=0.15, bar_height=0.5, target_width=0.25, target_height=0.02, bar_color='gold', low_value=0.0, high_value=max_value_middle_bar, target_value=middle_bar_target_value))
        attention_beep = self.registerObject(AO.Beep(beep_frequency=2000, beep_amplitude=1, beep_duration=0.2))
        target_A_up = self.registerObject(GO.Image('smiley.png', pos_x=-MU_bar_pos_x, pos_y=MU_bar_pos_y+MU_bar_height+smiley_pos_offset, scale_x=smiley_scale, scale_y=smiley_scale))
        target_A_down = self.registerObject(GO.Image('smiley.png', pos_x=-MU_bar_pos_x, pos_y=MU_bar_pos_y-smiley_pos_offset, scale_x=smiley_scale, scale_y=smiley_scale))
        target_B_up = self.registerObject(GO.Image('smiley.png', pos_x=MU_bar_pos_x, pos_y=MU_bar_pos_y+MU_bar_height+smiley_pos_offset, scale_x=smiley_scale, scale_y=smiley_scale))
        target_B_down = self.registerObject(GO.Image('smiley.png', pos_x=MU_bar_pos_x, pos_y=MU_bar_pos_y-smiley_pos_offset, scale_x=smiley_scale, scale_y=smiley_scale))


        # MU rates feedback
        # filter_A = SP.ButterFilter(4, mu_baseline_filter_lowpass_frq)
        # filter_B = SP.ButterFilter(4, mu_baseline_filter_lowpass_frq)
        filter_A = SP.MovAvg(mu_baseline_mov_avg_window)
        filter_B = SP.MovAvg(mu_baseline_mov_avg_window)
        copy_A_to_B = SP.CopyChannel(mu_A_channel_idx, mu_B_channel_idx)
        copy_B_to_A = SP.CopyChannel(mu_B_channel_idx, mu_A_channel_idx)

        bar_mu_A.controlStateWithLSLStream(mu_stream_name, channels=[mu_A_channel_idx, mu_B_channel_idx]) # this is a hack but it works: copy value from channel A to B, filter channel B, and use channel B for the baseline
        bar_mu_A.addSignalProcessingToLSLStream(copy_A_to_B)
        bar_mu_A.addSignalProcessingToLSLStream(filter_A, channels=[mu_B_channel_idx])

        bar_mu_B.controlStateWithLSLStream(mu_stream_name, channels=[mu_B_channel_idx, mu_A_channel_idx]) # this is a hack but it works: copy value from channel B to A, filter channel A, and use channel A for the baseline
        bar_mu_B.addSignalProcessingToLSLStream(copy_B_to_A)
        bar_mu_B.addSignalProcessingToLSLStream(filter_B, channels=[mu_A_channel_idx])

        # # lock force
        # butter_force = SP.ButterFilter(4, 5)
        # force_max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        # bar_middle.controlStateWithLSLStream('MouseControllerStream', channels=[force_channel])
        # bar_middle.addSignalProcessingToLSLStream(force_max_normalization, channels=[force_channel])
        # bar_middle.addSignalProcessingToLSLStream(butter_force, channels=[force_channel])

        # lock rate
        average_rate = SP.Mean()
        bar_middle.controlStateWithLSLStream(mu_stream_name, channels=[mu_A_channel_idx])
        bar_middle.addSignalProcessingToLSLStream(average_rate, channels=[mu_A_channel_idx, mu_B_channel_idx])


        # sequence definition
        assert n_trials % 2 == 0, "number of trials must be a multiple of the number of classes (i.e. 2)"
        # this code ensure a guaranted 50/50 ratio of class occurances
        trial_classes = np.tile(np.arange(1, 3), (int(n_trials/2), 1)).reshape((-1))
        np.random.shuffle(trial_classes) # inplace

        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_start_time = pre_paradigm_interval
                trial_start_time_type = "abs"
                trial_start_time_ref = ""
            else:
                trial_start_time = np.random.uniform(inter_trial_interval_min, inter_trial_interval_max)
                trial_start_time_type = "rel"
                trial_start_time_ref = "trial_end"
            self.script.append(ScriptItem(name='trial_start', time=trial_start_time, time_type=trial_start_time_type, rel_name=trial_start_time_ref, actions=[attention_beep.beep, bar_mu_A.activate, bar_mu_B.activate, bar_middle.activate, bar_mu_A.target_node.hide, bar_mu_B.target_node.hide]))

            trial_class = trial_classes[trial_idx]
            if trial_class == 1:
                smiley_A = target_A_up
                smiley_B = target_B_down
                class_name = "cond1"
            elif trial_class == 2:
                smiley_A = target_A_down
                smiley_B = target_B_up
                class_name = "cond2"

            cue_time = np.random.uniform(cue_time_min, cue_time_max)
            self.script.append(ScriptItem(name=class_name, time=cue_time, time_type='rel', rel_name='trial_start', actions=[bar_middle.deactivate, bar_mu_A.updateTargetValueFromLSLStream, bar_mu_B.updateTargetValueFromLSLStream, bar_mu_A.target_node.show, bar_mu_B.target_node.show, smiley_A.activate, smiley_B.activate]))
            self.script.append(ScriptItem(name='trial_end', time=cue_time+control_phase_duration, time_type='rel', rel_name='trial_start', actions=[bar_mu_A.deactivate, bar_mu_B.deactivate, smiley_A.deactivate, smiley_B.deactivate]))

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
