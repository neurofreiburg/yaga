from pathlib import Path
import numpy as np
from functools import partial
import random

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        exploration_mode = False

        target_center_x = 0
        target_center_y = 0
        target_radius = 0.6
        n_targets = 6

        workspace_size = 0.9

        # these parameters are used when exploration mode is off:
        n_trials = 10
        reach_timeout = 60 # [s]
        pre_paradigm_interval = 5 # [s]
        post_paradigm_interval = 5 # [s]
        inter_trial_interval = 15 # [s]

        workspace = self.registerObject(GO.Box(pos_x=0, pos_y=0, depth=1, scale_x=workspace_size, scale_y=workspace_size, color='gray'))
        targets = self.registerObject(GO.ReachTargets(pos_x=target_center_x, pos_y=target_center_y, radius=target_radius, target_size=0.2, number_of_targets=n_targets, start_target=False, dwell_time=2))

        targets.controlStateWithLSLStreams(['quattrocento'], channels=[2, 3])

        flappy_bird_controller = SP.FlappyBirdController(pos_increment=0.015, negative_vel=0.0003, switch_interval=0.25, x_max=1, y_max=1)
        map_x = SP.LinearMap(0, 1, -workspace_size, workspace_size)
        map_y = SP.LinearMap(0, 1, -workspace_size, workspace_size)

        targets.addSignalProcessingToLSLStream(flappy_bird_controller, channels=[2, 3])
        targets.addSignalProcessingToLSLStream(map_x, channels=2)
        targets.addSignalProcessingToLSLStream(map_y, channels=3)


        # build trial sequence
        if exploration_mode:
            self.script = [ScriptItem(name='trial_start', time=0, actions=[workspace.activate, targets.activate]),
                           ScriptItem(name='trial_end', time=300, time_type='rel', rel_name='trial_start', actions=[])]
        else:
            self.script = []
            for trial_idx in range(n_trials):
                target = random.randint(0, n_targets-1)
                if trial_idx == 0:
                    self.script.append(ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[workspace.activate, targets.activate, partial(targets.setActiveTarget, target)]))
                else:
                    self.script.append(ScriptItem(name='trial_start', time=inter_trial_interval, time_type='rel', rel_name='trial_end', actions=[workspace.activate, targets.activate, partial(targets.setActiveTarget, target)]))
                self.script.append(ScriptItem(name='trial_end', time=reach_timeout, time_type='rel', rel_name='trial_start', wait_for_signal=GO.ReachTargets.TARGET_REACHED, actions=[workspace.deactivate, targets.deactivate]))
            self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))