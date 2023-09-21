from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'spike'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        info_text = self.registerObject(GO.Text('spike audio', scale_x=0.1, scale_y=0.1, color='white'))

        spikes_sound = self.registerObject(AO.SpikeSound(beep_frequencies=[2000, 800], beep_channels=['left', 'right'], beep_duration=0.02))
        spikes_sound.controlWithLSLStreams(['spikes'], channels=[0, 3], aggregation_mode='sum')

        self.script = [ScriptItem(name='trial_start', time=0, actions=[info_text.activate, spikes_sound.activate]),
                       ScriptItem(name='trial_end', time=600, time_type='abs', actions=[])]
