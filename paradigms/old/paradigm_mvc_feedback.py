from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'mvc'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        n_trials = 3
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 5
        inter_trial_interval_max = 10
        mvc_duration = 5

        arrow_max_force = 10
        arrow_angle = -18

        info_text = self.registerObject(GO.Text('prepare for maximum contraction', pos_y=0.5, scale_x=0.1, scale_y=0.1, color='white'))
        countdown = self.registerObject(GO.Countdown(counter_start=mvc_duration, pos_y=0.4, scale_x=0.5, scale_y=0.5, color='white'))
        traffic_light_green = self.registerObject(GO.Image('traffic_light_green.png', pos_y=0.6, scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_yellow = self.registerObject(GO.Image('traffic_light_yellow.png', pos_y=0.6, scale_x=0.2, scale_y=0.2*1.68))
        traffic_light_red = self.registerObject(GO.Image('traffic_light_red.png', pos_y=0.6, scale_x=0.2, scale_y=0.2*1.68))


        # force feedback (only the angle of the force vector is provided as feedback!)
        arrow = self.registerObject(GO.Arrow(pos_y=-0.9, angle=arrow_angle, arrow_length=1.2, high_value=arrow_max_force))
        cross = self.registerObject(GO.Cross(pos_y=-0.9, line_width=0.01, scale_x=0.4, scale_y=0.4, color='black', depth=1))
        line = self.registerObject(GO.Box(pos_y=-0.4, scale_x=0.01, scale_y=0.6, color='red', depth=1))

        # f [kg] = (Vmeasured [muV] - offset [muV]) * 1e-6 * FS [kg] / (RO [V/V] * Gain [V/V])
        # f [kg] = (Vmeasured - 2.2e6) * 1e-6 * 2 / (0.005 * 200)
        # FS ... full scale
        # RO ... rated output
        # Gain ... 200 @ Forza
        scaler = SP.Scaler(scale=2*1e-6/(0.005*200), pre_offset=-2.758e6)

        arrow.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        arrow.addSignalProcessingToLSLStream(scaler, channels=[64, 65])
        arrow.activate()
        cross.activate()
        line.activate()

        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]
            trial_script_items.extend([ScriptItem(name='info_text', time=0, time_type='rel', rel_name='trial_start', actions=[info_text.activate]),
                                       ScriptItem(name='traffic_light_red', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, traffic_light_red.activate]),
                                       ScriptItem(name='traffic_light_yellow', time=5, time_type='rel', rel_name='trial_start', actions=[traffic_light_red.deactivate, traffic_light_yellow.activate]),
                                       ScriptItem(name='traffic_light_greeb', time=7, time_type='rel', rel_name='trial_start', actions=[traffic_light_yellow.deactivate, traffic_light_green.activate]),
                                       ScriptItem(name='start_counter', time=9, time_type='rel', rel_name='trial_start', actions=[traffic_light_green.deactivate, countdown.activate]),
                                       ScriptItem(name='trial_end', wait_for_signal=GO.Countdown.COUNTDOWN_FINISHED, actions=[])])
            self.script.extend(trial_script_items)
        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
