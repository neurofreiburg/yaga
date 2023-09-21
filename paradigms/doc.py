from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables)


        text = self.registerObject(GO.Text('text', pos_y=-0.25, scale_x=1, scale_y=1, color='white'))
        ball = self.registerObject(GO.Ball(scale_x=0.6, scale_y=0.6, color="white"))
        box = self.registerObject(GO.Box(scale_x=0.6, scale_y=0.6, color="white"))
        cross = self.registerObject(GO.Cross(scale_x=0.5, scale_y=0.5, color="white"))
        rnd = self.registerObject(GO.RandomNumber([0, 10], pos_y=-0.3, scale_x=1, scale_y=1, color="white"))
        count = self.registerObject(GO.Countdown(counter_interval=100, pos_y=-0.3, scale_x=1, scale_y=1, color="white"))

        bar = self.registerObject(GO.Bar(pos_y=-0.7, bar_width=0.4, bar_height=1.4, frame_width=0.025, target_width=0.6, target_height=0.025, high_value=1, target_value=0.8))
        arrow = self.registerObject(GO.Arrow(target_value=0.25, pos_y=-0.65, arrow_length=1, line_width=0.05, head_size=0.2, target_size=0.15))

        spikevis = self.registerObject(GO.SpikeVis(number_of_units=2, size=0.35, spacing=1.5))
        targets = self.registerObject(GO.ReachTargets(radius=0.75, target_rotation=0, number_of_targets=8, target_size=0.15, cursor_size=0.05, target_active_color='lime'))

        # text.activate()
        # ball.activate()
        # box.activate()
        # cross.activate()
        # rnd.activate()
        # count.activate()

        # arrow.activate()
        # bar.activate()
        # bar.bar_node.setScale(bar.bar_width/2, 1, 0.2)
        # bar.bar_node.setZ(0.2)

        # spikevis.activate()
        # spikevis.units[0].setColor(spikevis.active_color)

        targets.activate()
        targets.targets[1].setColor(targets.target_active_color)
        targets.cursor.setPos(0.2, 0, 0.2)

        self.script = [ScriptItem(name='trial_start', time=30, time_type='abs', actions=[])]
        # for trial_idx in range(n_trials):
        #     if trial_idx == 0:
        #         trial_script_items = [Scri1ptItem(name='trial_start', time=pre_paradigm_interval, actions=[])]
        #     else:
        #         trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[])]
        #     trial_script_items.extend([ScriptItem(name='info_text', time=0, time_type='rel', rel_name='trial_start', actions=[info_text.activate]),
        #                                 ScriptItem(name='traffic_light_red', time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, traffic_light_red.activate]),
        #                                 ScriptItem(name='traffic_light_yellow', time=5, time_type='rel', rel_name='trial_start', actions=[traffic_light_red.deactivate, traffic_light_yellow.activate]),
        #                                 ScriptItem(name='traffic_light_green', time=7, time_type='rel', rel_name='trial_start', actions=[traffic_light_yellow.deactivate, traffic_light_green.activate]),
        #                                 ScriptItem(name='start_ramp', time=9, time_type='rel', rel_name='trial_start', actions=[traffic_light_green.deactivate, bar.activate, bar.startAnimation]),
        #                                 ScriptItem(name='trial_end', wait_for_signal=GO.BarWithRampTarget.BAR_FINISHED, actions=[bar.deactivate])])
            # self.script.extend(trial_script_items)
        # self.script.append(ScriptItem(time=30, time_type='rel', rel_name='trial_end', actions=[]))
