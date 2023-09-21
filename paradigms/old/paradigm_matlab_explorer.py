from pathlib import Path

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO


class Paradigm(ParadigmBase):

    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'explorer'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        trial_duration = 10

        task_text = self.registerObject(GO.Text('explore', scale_x=0.1, scale_y=0.1, color='black'))
        task_background = self.registerObject(GO.Box(depth=1, scale_x=0.5, scale_y=0.5, color='lime'))


        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[task_background.activate, task_text.activate]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[task_background.deactivate, task_text.deactivate]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
