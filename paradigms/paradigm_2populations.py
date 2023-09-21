from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        scaler_upper_frq = 20; # 0:20 -> -1:1
        bandpass_upper_frq = 10;

        cross = self.registerObject(GO.Cross(scale_x=0.1, scale_y=0.1, color='white', depth=2))
        ball = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.05, scale_y=0.05, color='green', depth=0))

        # ball.controlPosWithLSLStream('mu_rate')
        ball.controlPosWithLSLStream('MouseControllerStream')

        scaler = SP.Scaler(2.0/scaler_upper_frq, 0, -1)
        butter = SP.ButterFilter(4, bandpass_upper_frq)
        ball.addSignalProcessingToLSLStream(scaler)
        ball.addSignalProcessingToLSLStream(butter)

        self.script = [ScriptItem(name='trial_start', time=0, actions=[cross.activate, ball.activate]),
                       ScriptItem(name='trial_end', time=np.inf, actions=[cross.activate, ball.activate])]
