import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO


class Paradigm(ParadigmBase):

    task_name = "demo"

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host="localhost")

        number_of_trials = 5
        pre_paradigm_interval = 3     # seconds
        post_paradigm_interval = 3    # seconds
        inter_trial_interval_min = 5  # seconds
        inter_trial_interval_max = 10 # seconds
        demo_task_duration = 5        # seconds

        # graphical objects
        instruction_text = self.registerObject(GO.Text("prepare for demo task", scale_x=0.1, scale_y=0.1, color="white"))
        countdown = self.registerObject(GO.Countdown(counter_start=demo_task_duration, scale_x=0.5, scale_y=0.5, color="white"))
        traffic_light_green = self.registerObject(GO.Image("traffic_light_green.png", scale_x=0.2, scale_y=0.2*1.7))
        traffic_light_yellow = self.registerObject(GO.Image("traffic_light_yellow.png", scale_x=0.2, scale_y=0.2*1.7))
        traffic_light_red = self.registerObject(GO.Image("traffic_light_red.png", scale_x=0.2, scale_y=0.2*1.68))


        # paradigm sequence definition
        self.script = []
        for trial_idx in range(number_of_trials):
            # the first trial has an absolute time trigger, the subsequent trials have a relative time trigger
            if trial_idx == 0:
                trial_start_time = pre_paradigm_interval
                trial_start_time_type = "abs"
                trial_start_time_ref = ""
            else:
                trial_start_time = np.random.uniform(inter_trial_interval_min, inter_trial_interval_max)
                trial_start_time_type = "rel"
                trial_start_time_ref = "trial_end"
            self.script.append(ScriptItem(name="trial_start", time=trial_start_time, time_type=trial_start_time_type, rel_name=trial_start_time_ref, actions=[instruction_text.activate]))
            self.script.append(ScriptItem(name="traffic_light_red", time=3, time_type="rel", rel_name="trial_start", actions=[instruction_text.deactivate, traffic_light_red.activate]))
            self.script.append(ScriptItem(name="traffic_light_yellow", time=5, time_type="rel", rel_name="trial_start", actions=[traffic_light_red.deactivate, traffic_light_yellow.activate]))
            self.script.append(ScriptItem(name="traffic_light_green", time=7, time_type="rel", rel_name="trial_start", actions=[traffic_light_yellow.deactivate, traffic_light_green.activate]))
            self.script.append(ScriptItem(name="countdown", time=9, time_type="rel", rel_name="trial_start", actions=[traffic_light_green.deactivate, countdown.activate]))
            self.script.append(ScriptItem(name="trial_end", wait_for_signal=GO.Countdown.COUNTDOWN_FINISHED, actions=[]))

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type="rel", rel_name="trial_end", actions=[]))
