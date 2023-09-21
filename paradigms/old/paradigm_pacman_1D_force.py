from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
from yaga_modules.pacman import Pacman
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'warmup'

    def __init__(self, paradigm_variables):

        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost')

        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        trial_duration = 180

        pacman_visualization_filter_frq = 2
        # pacman_upper_force = 0.1;
        # pacman_lower_force = 0.02;
        pacman_upper_force = 0.055;
        pacman_lower_force = 0.045;

        background = self.registerObject(GO.Image('background_2.jpg', depth=10, scale_x=1.78*1.08, scale_y=1.08))
        pacman = self.registerObject(Pacman(item_speed=0.15, item_generation_frequency=5, amplitude=1, frequency=[0.05, 0.15], noise_stddev=2.5, neg_feedback_type=None))

        # pacman.controlStateWithLSLStreams(['MouseControllerStream'], channels=[0])
        pacman.controlStateWithLSLStreams(['quattrocento'], channels=[64])

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64], 2.758e6)

        # Pacman force control
        butter_pacman_vis = SP.ButterFilter(2, pacman_visualization_filter_frq)
        scaler_pacman = SP.Scaler(scale=2/(pacman_upper_force-pacman_lower_force), pre_offset=-pacman_lower_force, post_offset=-1)
        pacman.addSignalProcessingToLSLStream(max_normalization, channels=[64])
        pacman.addSignalProcessingToLSLStream(scaler_pacman, channels=[64])
        pacman.addSignalProcessingToLSLStream(butter_pacman_vis, channels=[64])

        background.activate()
        pacman.activate()

        self.script = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[pacman.start]),
                       ScriptItem(name='trial_end', time=trial_duration, time_type='rel', rel_name='trial_start', actions=[]),
                       ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[])]
