from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
from yaga_modules.pacman import Pacman
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'twounits'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        pre_paradigm_interval = 3
        post_paradigm_interval = 3
        trial_duration = 180

        unit_vis = self.registerObject(GO.SpikeVis(pos_x=0, pos_y=0, depth=0, number_of_units=2, size=0.2, spacing=1, active_color='lime', inactive_color='gray'))
        spikes_sound = self.registerObject(AO.SpikeSound(beep_frequencies=[2000, 2500], beep_channels=['left', 'right'], beep_duration=0.04, dynamic_frq=False, dynamic_frq_factor=100, dynamic_mov_avg=None, dynamic_exp_avg_alpha=0.5))

        unit_vis.controlStateWithLSLStreams(['spikes'], channels=[int(paradigm_variables['var1']), int(paradigm_variables['var2'])], aggregation_mode='sum')
        spikes_sound.controlWithLSLStreams(['spikes'], channels=[int(paradigm_variables['var1']), int(paradigm_variables['var2'])], aggregation_mode='sum')

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[spikes_sound.activate, unit_vis.activate]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[spikes_sound.deactivate, unit_vis.deactivate]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
