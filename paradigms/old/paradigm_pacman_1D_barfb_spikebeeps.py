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
    task_name = 'pacman'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        trial_duration = 180

        target_force = 0.05
        max_force = 0.08
        force_visualization_filter_frq = 10
        mu_visualization_filter_frq = 3
        mu_upper_frq = 12;
        mu_lower_frq = 8;

        background = self.registerObject(GO.Image('background_2.jpg', depth=10, scale_x=1.78*1.08, scale_y=1.08))
        pacman = self.registerObject(Pacman(item_speed=0.15, item_generation_frequency=5, amplitude=1, frequency=[0.05, 0.15], noise_stddev=2.5, neg_feedback_type=None))
        bar = self.registerObject(GO.Bar(pos_x=-1.1, pos_y=-0.9, bar_width=0.08, bar_height=0.4, target_width=0.12, target_color='red', high_value=max_force))
        spikes_sound = self.registerObject(AO.SpikeSound(beep_frequencies=[2000], beep_channels=['both'], beep_duration=0.04, downsample=1, dynamic_frq=True, dynamic_frq_factor=20))

        spikes_sound.controlWithLSLStreams(['spikes'], channels=[int(paradigm_variables['var1'])], aggregation_mode='sum')

        # pacman.controlStateWithLSLStreams(['MouseControllerStream'], channels=[0])
        pacman.controlStateWithLSLStreams(['pop_rates'], channels=[0])

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)

        # MU feedback
        scaler_mu = SP.Scaler(scale=2/(mu_upper_frq-mu_lower_frq), pre_offset=-mu_lower_frq, post_offset=-1)
        butter_mu_vis = SP.ButterFilter(2, mu_visualization_filter_frq)
        # population rate
        pacman.addSignalProcessingToLSLStream(scaler_mu, channels=[0])
        pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[0])
        # mouse
        # pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[1])

        butter_bar = SP.ButterFilter(4, force_visualization_filter_frq)
        # bar.controlStateWithLSLStream('MouseControllerStream', channels=[1])
        # bar.addSignalProcessingToLSLStream(butter_bar, channels=[1])
        bar.controlStateWithLSLStream('quattrocento', channels=[64])
        bar.addSignalProcessingToLSLStream(max_normalization, channels=[64])
        bar.addSignalProcessingToLSLStream(butter_bar, channels=[64])

        background.activate()
        pacman.activate()
        # bar.activate()
        spikes_sound.activate()

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[pacman.start]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
