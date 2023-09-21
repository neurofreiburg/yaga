from pathlib import Path
import numpy as np
from functools import partial
import random
import codecs

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('studies') / Path('cimod') / Path('data')
    # root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'cimod'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.1)

        force_fb_lowpass_frq = 3 # [Hz]
        target_force = 0.08
        targets_force_range = 0.01
        target_y_pos = 0.5
        cue_relative_y_pos = 0.2

        n_trials = 24
        pre_paradigm_interval = 3
        post_paradigm_interval = 3
        finish_beep_delay = 2
        inter_trial_interval_min = 4
        inter_trial_interval_max = 6
        cue_delay = 5 # [s]
        trial_duration = 10 # [s]
        math_random_number_interval = [10, 100];

        start_y_pos = -0.3
        y_per_force = (target_y_pos - start_y_pos)/target_force
        target_height = y_per_force*targets_force_range*0.5
        target_width = target_height

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)

        # cues positioned below force target
        rest_cue_low = self.registerObject(GO.Text("rest", pos_x=0, pos_y=target_y_pos-0.9*cue_relative_y_pos-0.1/2, scale_x=0.2, scale_y=0.2, color='white'))
        foot_cue_low = self.registerObject(GO.Image("foot_task.png", pos_x=0, pos_y=target_y_pos-cue_relative_y_pos, scale_x=0.12, scale_y=None))
        hand_cue_low = self.registerObject(GO.Image("hands_task.png", pos_x=0, pos_y=target_y_pos-cue_relative_y_pos, scale_x=0.35, scale_y=None))
        math_cue_low = self.registerObject(GO.RandomNumber(interval=math_random_number_interval, pos_x=0, pos_y=target_y_pos-0.9*cue_relative_y_pos-0.1/2, scale_x=0.2, scale_y=0.2, color='white'))
        # cues positioned above force target
        rest_cue_high = self.registerObject(GO.Text("rest", pos_x=0, pos_y=target_y_pos+0.9*cue_relative_y_pos-0.1/2, scale_x=0.2, scale_y=0.2, color='white'))
        foot_cue_high = self.registerObject(GO.Image("foot_task.png", pos_x=0, pos_y=target_y_pos+cue_relative_y_pos, scale_x=0.12, scale_y=None))
        hand_cue_high = self.registerObject(GO.Image("hands_task.png", pos_x=0, pos_y=target_y_pos+cue_relative_y_pos, scale_x=0.35, scale_y=None))
        math_cue_high = self.registerObject(GO.RandomNumber(interval=math_random_number_interval, pos_x=0, pos_y=0.9*target_y_pos+cue_relative_y_pos-0.1/2, scale_x=0.2, scale_y=0.2, color='white'))

        start = self.registerObject(GO.Box(pos_y=start_y_pos, scale_x=0.1, scale_y=0.005, color='white', depth=2))
        force_target = self.registerObject(GO.Box(pos_x=0, pos_y=target_y_pos, scale_x=target_width, scale_y=target_height, color='white'))
        direct_feedback = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.03, scale_y=0.03, color='lime'))
        sound = self.registerObject(AO.Beep())
        finish_sound = self.registerObject(AO.Beep(beep_frequency=400, beep_duration=1))

        direct_feedback.controlPosWithLSLStream('quattrocento', channels=[81, 80]) # x-position = dummy channel (set to 0); y-position = force signal

        # direct feedback processing (force feedback)
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [80], force_amp_voltage_offset)
        butter_force = SP.ButterFilter(2, force_fb_lowpass_frq)
        map_force = SP.LinearMap(0, target_force, start_y_pos, target_y_pos)
        force_range_limit = SP.Limit(min_val=start_y_pos, max_val=1)
        constant = SP.Constant(0)
        direct_feedback.addSignalProcessingToLSLStream(max_normalization, channels=[80], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(butter_force, channels=[80], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(map_force, channels=[80], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(force_range_limit, channels=[80], lsl_stream_name='quattrocento')
        direct_feedback.addSignalProcessingToLSLStream(constant, channels=[81], lsl_stream_name='quattrocento')

        n_classes = 8 # 4 classes x 2 positions
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
                cue = rest_cue_low
                class_name = 'class_rest_low'
            elif trial_class == 2:
                cue = foot_cue_low
                class_name = 'class_foot_low'
            elif trial_class == 3:
                cue = hand_cue_low
                class_name = 'class_hand_low'
            elif trial_class == 4:
                cue = math_cue_low
                class_name = 'class_math_low'
            elif trial_class == 5:
                cue = rest_cue_high
                class_name = 'class_rest_high'
            elif trial_class == 6:
                cue = foot_cue_high
                class_name = 'class_foot_high'
            elif trial_class == 7:
                cue = hand_cue_high
                class_name = 'class_hand_high'
            elif trial_class == 8:
                cue = math_cue_high
                class_name = 'class_math_high'

            trial_script_items.extend([ScriptItem(name=class_name, time=0, time_type='rel', rel_name='trial_start', actions=[start.activate, force_target.activate, direct_feedback.activate, sound.beep]),
                                        ScriptItem(name='cue', time=cue_delay, time_type='rel', rel_name='trial_start', actions=[cue.activate]),
                                        ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[cue.deactivate, start.deactivate, force_target.deactivate, direct_feedback.deactivate])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=finish_beep_delay, time_type='rel', rel_name='trial_end', actions=[finish_sound.beep]))
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
