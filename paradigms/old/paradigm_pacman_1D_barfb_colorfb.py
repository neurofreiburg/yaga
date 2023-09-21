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

        target_force = 0.05
        max_force = 0.08
        bar_filter_frq = 10
        force_diff_filter_frq = 3
        force_visualization_filter_frq = 0.5
        mu_visualization_filter_frq = 3
        mu_upper_frq = 12;
        mu_lower_frq = 8;

        background = self.registerObject(GO.Image('background_2.jpg', depth=10, scale_x=1.78*1.08, scale_y=1.08))
        pacman = self.registerObject(Pacman(item_speed=0.15, item_generation_frequency=5, amplitude=1, frequency=[0.05, 0.15], noise_stddev=2.5, neg_feedback_type='color'))
        bar = self.registerObject(GO.Bar(pos_x=-1.1, pos_y=-0.9, bar_width=0.08, bar_height=0.4, target_width=0.12, target_color='red', high_value=max_force, target_value=target_force))

        # pacman.controlStateWithLSLStream('MouseControllerStream', channels=[1, 0])
        pacman.controlStateWithLSLStreams(['pop_rates', 'quattrocento'], channels=[0, 64])

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)

        butter_bar = SP.ButterFilter(4, bar_filter_frq)
        # bar.controlStateWithLSLStream('MouseControllerStream', channels=[1])
        # bar.addSignalProcessingToLSLStream(butter_bar, channels=[1])
        bar.controlStateWithLSLStream('quattrocento', channels=64)
        bar.addSignalProcessingToLSLStream(max_normalization, channels=[64])
        bar.addSignalProcessingToLSLStream(butter_bar, channels=[64])


        # MU feedback
        butter_mu_vis = SP.ButterFilter(2, mu_visualization_filter_frq)
        # population rate
        scaler_mu = SP.Scaler(scale=2/(mu_upper_frq-mu_lower_frq), pre_offset=-mu_lower_frq, post_offset=-1)
        pacman.addSignalProcessingToLSLStream(scaler_mu, channels=[0], lsl_stream_name='pop_rates')
        pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[0], lsl_stream_name='pop_rates')
        # mouse
        # pacman.addSignalProcessingToLSLStream(butter_mu_vis, channels=[1], lsl_stream_name='MouseControllerStream')

        # mouse force feedback
        # scaler_force = SP.Scaler(20)
        butter_force_diff = SP.ButterFilter(4, force_diff_filter_frq)
        butter_force_vis = SP.ButterFilter(2, force_visualization_filter_frq)
        math_diff = SP.Diff()
        math_norm = SP.EuclidNorm()
        # pacman.addSignalProcessingToLSLStream(scaler_force, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(butter_force_diff, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(math_diff, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(math_norm, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(butter_force_vis, channels=[0], lsl_stream_name='MouseControllerStream')
        # pacman.addSignalProcessingToLSLStream(scaler_force, channels=[0], lsl_stream_name='MouseControllerStream')

        # real force feedback
        scaler_force = SP.Scaler(200000)
        pacman.addSignalProcessingToLSLStream(max_normalization, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(scaler_force, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(butter_force_diff, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(math_diff, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(math_norm, channels=[64], lsl_stream_name='quattrocento')
        pacman.addSignalProcessingToLSLStream(butter_force_vis, channels=[64], lsl_stream_name='quattrocento')

        background.activate()
        bar.activate()
        pacman.activate()

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[pacman.start]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
