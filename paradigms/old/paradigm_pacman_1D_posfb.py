from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
from yaga_modules.pacman import Pacman
import yaga_modules.graphic_objects as GO
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

        # target_force = 0.04
        target_force = 0.05
        max_force_difference = 0.005
        # target_force = 0.5
        # max_force_difference = 0.1
        force_visualization_filter_frq = 10
        mu_visualization_filter_frq = 3
        # mu_upper_frq = 11;
        # mu_lower_frq = 8;
        mu_upper_frq = 12;
        mu_lower_frq = 8;

        background = self.registerObject(GO.Image('background_2.jpg', depth=10, scale_x=1.78*1.08, scale_y=1.08))
        pacman = self.registerObject(Pacman(item_speed=0.15, item_generation_frequency=5, amplitude=1, frequency=[0.05, 0.15], noise_stddev=2.5, neg_feedback_type='pos'))

        # pacman.controlStateWithLSLStream('MouseControllerStream', channels=[1, 0])
        pacman.controlStateWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64])

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)

        # MU feedback
        scaler_mu = SP.Scaler(scale=2/(mu_upper_frq-mu_lower_frq), pre_offset=-mu_lower_frq, post_offset=-1)
        butter_mu_vis = SP.ButterFilter(2, mu_visualization_filter_frq)
        # population rate
        pacman.addSignalProcessingToLSLStream(scaler_mu, channels=[0], lsl_stream_name='pop_rates')
        pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[0], lsl_stream_name='pop_rates')
        # mouse
        # pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[1], lsl_stream_name='MouseControllerStream')

        # negative feedback
        scaler_force = SP.Scaler(scale=1/max_force_difference, pre_offset=-target_force)
        butter_force_vis = SP.ButterFilter(2, force_visualization_filter_frq)
        # force
        pacman.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(scaler_force, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(butter_force_vis, channels=[64], lsl_stream_name='quattrocento')
        # mouse
        # pacman.addSignalProcessingToLSLStream(scaler_force, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(butter_force_vis, channels=[0], lsl_stream_name='MouseControllerStream')

        background.activate()
        pacman.activate()


        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[pacman.start]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
