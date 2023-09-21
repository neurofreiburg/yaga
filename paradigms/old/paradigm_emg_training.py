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
    task_name = 'emgtraining'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        pre_paradigm_interval = 3
        post_paradigm_interval = 3
        trial_duration = 180

        emg_lower_limit = 0
        emg_upper_limit = 0.005
        emg_power_visualization_filter_frq = 5;

        unit_vis = self.registerObject(GO.SpikeVis(pos_x=-0.2, pos_y=0, depth=0, number_of_units=1, size=0.2, active_color='lime', inactive_color='gray'))
        spikes_sound = self.registerObject(AO.SpikeSound(beep_frequencies=[1500], beep_channels=['both'], beep_duration=0.04, dynamic_frq=False, dynamic_frq_factor=100, dynamic_mov_avg=None, dynamic_exp_avg_alpha=0.8))
        emg_bar = self.registerObject(GO.Bar(pos_x=0.2, pos_y=-0.4, bar_width=0.15, bar_height=0.8, bar_color='red', low_value=emg_lower_limit, high_value=emg_upper_limit))

        relative_power = SP.MaxAvgPowerNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', range(0,64), prefilter_cutoff_frqs=[50, 500])
        butter_power_vis = SP.ButterFilter(2, emg_power_visualization_filter_frq)

        unit_vis.controlStateWithLSLStreams(['spikes'], channels=[int(paradigm_variables['var1'])], aggregation_mode='sum')
        spikes_sound.controlWithLSLStreams(['spikes'], channels=[int(paradigm_variables['var1'])], aggregation_mode='sum')

        emg_bar.controlStateWithLSLStream('quattrocento', channels=[0])
        emg_bar.addSignalProcessingToLSLStream(relative_power, channels=range(0, 64))
        emg_bar.addSignalProcessingToLSLStream(butter_power_vis, channels=[0])

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[spikes_sound.activate, unit_vis.activate, emg_bar.activate]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[spikes_sound.deactivate, unit_vis.deactivate, emg_bar.deactivate]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
