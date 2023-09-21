from pathlib import Path
import numpy as np
from functools import partial
import random

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'targetreach'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        mu_x_target_min_frq = 8 # [Hz]
        mu_x_target_max_frq = 14 # [Hz]
        mu_y_target_min_frq = 6 # [Hz]
        mu_y_target_max_frq = 12 # [Hz]

        mu_x_start_frq = 3 # [Hz]
        mu_y_start_frq = 3 # [Hz]

        target_center_x = 0.25
        target_center_y = 0.25
        target_radius = 0.6

        mu_lowpass_frq = 4 # [Hz]

        n_targets = 8

        exploration_mode = True

        # these parameters are used when exploration mode is off:
        n_trials = 10
        reach_timeout = 60 # [s]
        pre_paradigm_interval = 5 # [s]
        post_paradigm_interval = 5 # [s]
        inter_trial_interval = 15 # [s]

        # calculate screen coordinates of start position
        x_screen_unit_per_hz = 2*target_radius / (mu_x_target_max_frq - mu_x_target_min_frq)
        y_screen_unit_per_hz = 2*target_radius / (mu_y_target_max_frq - mu_y_target_min_frq)
        start_x_pos = (target_center_x - target_radius) - (mu_x_target_min_frq - mu_x_start_frq)*x_screen_unit_per_hz # left target minus difference between target and start position
        start_y_pos = (target_center_y - target_radius) - (mu_y_target_min_frq - mu_y_start_frq)*y_screen_unit_per_hz # lower target minus difference between target and start position

        targets = self.registerObject(GO.ReachTargets(pos_x=target_center_x, pos_y=target_center_y, radius=target_radius, target_size=0.2, number_of_targets=n_targets, start_target=False, dwell_time=2))
        target_center_marker = self.registerObject(GO.Cross(pos_x=target_center_x, pos_y=target_center_y, scale_x=0.1, scale_y=0.1, depth=2))
        start_position_marker = self.registerObject(GO.Cross(pos_x=start_x_pos, pos_y=start_y_pos, scale_x=0.1, scale_y=0.1, color='black', depth=2))

        # targets.controlStateWithLSLStream('MouseControllerStream', channels=[0, 1])
        targets.controlStateWithLSLStreams(['pop_rates'], channels=[0, 1])

        # processing: (1) filter, (2) limit, and (3) map firing rates to screen coordinates
        butter_mu = SP.ButterFilter(2, mu_lowpass_frq)
        x_limit = SP.Limit(min_val=mu_x_start_frq)
        y_limit = SP.Limit(min_val=mu_y_start_frq)
        x_map = SP.LinearMap(mu_x_target_min_frq, mu_x_target_max_frq, target_center_x - target_radius, target_center_x + target_radius)
        y_map = SP.LinearMap(mu_y_target_min_frq, mu_y_target_max_frq, target_center_y - target_radius, target_center_y + target_radius)
        targets.addSignalProcessingToLSLStream(butter_mu, channels=[0, 1])
        targets.addSignalProcessingToLSLStream(x_limit, channels=[0])
        targets.addSignalProcessingToLSLStream(y_limit, channels=[1])
        targets.addSignalProcessingToLSLStream(x_map, channels=[0])
        targets.addSignalProcessingToLSLStream(y_map, channels=[1])

        # build trial sequence
        if exploration_mode:
            self.script = [ScriptItem(name='trial_start', time=0, actions=[start_position_marker.activate, targets.activate, target_center_marker.activate]),
                           ScriptItem(name='trial_end', time=300, time_type='rel', rel_name='trial_start', actions=[])]
        else:
            self.script = []
            for trial_idx in range(n_trials):
                target = random.randint(0, n_targets-1)
                if trial_idx == 0:
                    self.script.append(ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[start_position_marker.activate, targets.activate, partial(targets.setActiveTarget, target)]))
                else:
                    self.script.append(ScriptItem(name='trial_start', time=inter_trial_interval, time_type='rel', rel_name='trial_end', actions=[start_position_marker.activate, targets.activate, partial(targets.setActiveTarget, target)]))
                self.script.append(ScriptItem(name='trial_end', time=reach_timeout, time_type='rel', rel_name='trial_start', wait_for_signal=GO.ReachTargets.TARGET_REACHED, actions=[start_position_marker.deactivate, targets.deactivate]))
            self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
