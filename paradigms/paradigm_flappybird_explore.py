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

        rect_length = 0.9

        ball = self.registerObject(GO.Ball(pos_x=0, pos_y=0, scale_x=0.05, scale_y=0.05, color='green', depth=0))
        rect = self.registerObject(GO.Box(pos_x=0, pos_y=0, depth=-1, scale_x=rect_length, scale_y=rect_length, color='white'))

        ball.controlPosWithLSLStream('quattrocento', channels=[2, 3])

        flappy_bird_controller = SP.FlappyBirdController(pos_increment=0.015, negative_vel=0.0003, switch_interval=0.15, x_max=1, y_max=1)
        scaler = SP.Scaler(2.0/scaler_upper_frq, 0, -1)
        map_x = SP.LinearMap(0, 1, -rect_length, rect_length)
        map_y = SP.LinearMap(0, 1, -rect_length, rect_length)
        ball.addSignalProcessingToLSLStream(flappy_bird_controller, channels=[2, 3])
        ball.addSignalProcessingToLSLStream(map_x, channels=2)
        ball.addSignalProcessingToLSLStream(map_y, channels=3)

        self.script = [ScriptItem(name='trial_start', time=0, actions=[ball.activate, rect.activate]),
                       ScriptItem(name='trial_end', time=np.inf, actions=[ball.deactivate, rect.deactivate])]
