from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'diff_feedbback'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        max_force = 0.2
        max_diff = 1e-3
        arrow_angle = -35

        arrow_left = self.registerObject(GO.Arrow(pos_x=-0.8, pos_y=0.4, angle=arrow_angle, arrow_length=0.5, high_value=max_diff))
        cross_left = self.registerObject(GO.Cross(pos_x=-0.8, pos_y=0.4, line_width=0.01, scale_x=0.4, scale_y=0.4, color='black', depth=1))

        arrow_right = self.registerObject(GO.Arrow(pos_x=0.8, pos_y=0.4, angle=arrow_angle, arrow_length=0.5, high_value=max_force))
        cross_right = self.registerObject(GO.Cross(pos_x=0.8, pos_y=0.4, line_width=0.01, scale_x=0.4, scale_y=0.4, color='black', depth=1))

        bar_left = self.registerObject(GO.Bar(pos_x=-0.8, pos_y=-0.9, bar_width=0.2, bar_height=0.8, high_value=max_diff))
        bar_right = self.registerObject(GO.Bar(pos_x=0.8, pos_y=-0.9, bar_width=0.2, bar_height=0.8, high_value=max_force))

        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64, 65], 2.758e6)

        # f [kg] = (Vmeasured [muV] - offset [muV]) * 1e-6 * FS [kg] / (RO [V/V] * Gain [V/V])
        # f [kg] = (Vmeasured - 2.75e6) * 1e-6 * 2 / (0.005 * 100)
        # FS ... full scale
        # RO ... rated output
        # Gain ... 100 @ Forza
        scaler = SP.Scaler(scale=1e-6*2/(0.005*100), pre_offset=-2.75e6)

        butter_diff_arrow = SP.ButterFilter(4, 2)
        butter_diff_bar = SP.ButterFilter(4, 2)
        butter_abs_arrow = SP.ButterFilter(4, 2)
        butter_abs_bar = SP.ButterFilter(4, 2)

        math_diff = SP.Diff()
        math_abs = SP.Abs()
        math_norm = SP.EuclidNorm()

        arrow_left.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        arrow_left.addSignalProcessingToLSLStream(scaler, channels=[64, 65])
        arrow_left.addSignalProcessingToLSLStream(butter_diff_arrow, channels=[64, 65])
        arrow_left.addSignalProcessingToLSLStream(math_diff, channels=[64, 65])

        arrow_right.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        # arrow_right.addSignalProcessingToLSLStream(scaler, channels=[64, 65])
        arrow_right.addSignalProcessingToLSLStream(max_normalization, channels=[64, 65])
        arrow_right.addSignalProcessingToLSLStream(butter_abs_arrow, channels=[64, 65])

        bar_left.controlStateWithLSLStream('quattrocento', channels=[64])
        bar_left.addSignalProcessingToLSLStream(scaler, channels=[64, 65])
        bar_left.addSignalProcessingToLSLStream(butter_diff_bar, channels=[64, 65])
        bar_left.addSignalProcessingToLSLStream(math_diff, channels=[64, 65])
        bar_left.addSignalProcessingToLSLStream(math_norm, channels=[64, 65])

        bar_right.controlStateWithLSLStream('quattrocento', channels=[64])
        # bar_right.addSignalProcessingToLSLStream(scaler, channels=[64, 65])
        bar_right.addSignalProcessingToLSLStream(max_normalization, channels=[64, 65])
        bar_right.addSignalProcessingToLSLStream(math_norm, channels=[64, 65])
        bar_right.addSignalProcessingToLSLStream(butter_abs_bar, channels=[64, 65])

        arrow_left.activate()
        cross_left.activate()
        arrow_right.activate()
        cross_right.activate()
        bar_left.activate()
        bar_right.activate()

        self.script = [ScriptItem(name='trial_start', time=0, actions=[]),
                       ScriptItem(name='trial_end', time=np.inf, actions=[])]
