import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        arrow_max_force = 5
        arrow_angle = 0

        # offset = 2.75e6 # this offset equals to the Forza offset
        offset = 2.758e6
        bar_range = 0.1e6

        # force feedback (only the angle of the force vector is provided as feedback!)
        arrow = self.registerObject(GO.Arrow(pos_y=0, angle=arrow_angle, arrow_length=1, high_value=arrow_max_force))
        cross = self.registerObject(GO.Cross(pos_y=0, line_width=0.01, scale_x=0.4, scale_y=0.4, color='black', depth=1))
        angle_text = self.registerObject(GO.Text('0', pos_y=0.7, scale_x=0.1, scale_y=0.1, color='white'))
        amplifier1_val_text = self.registerObject(GO.Text('0', pos_x=-1.4, pos_y=-0.85, scale_x=0.1, scale_y=0.1, color='white'))
        amplifier2_val_text = self.registerObject(GO.Text('0', pos_x=-0.9, pos_y=-0.85, scale_x=0.1, scale_y=0.1, color='white'))
        amplifier1_label_text = self.registerObject(GO.Text('Sensor 1', pos_x=-1.4, pos_y=0.2, scale_x=0.1, scale_y=0.1, color='white'))
        amplifier2_label_text = self.registerObject(GO.Text('Sensor 2', pos_x=-0.9, pos_y=0.2, scale_x=0.1, scale_y=0.1, color='white'))
        amplifier1_bar = self.registerObject(GO.Bar(pos_x=-1.4, pos_y=-0.7, bar_width=0.1, bar_height=0.8, target_width=0.2, target_color='red', low_value=offset-bar_range, high_value=offset+bar_range, target_value=offset))
        amplifier2_bar = self.registerObject(GO.Bar(pos_x=-0.9, pos_y=-0.7, bar_width=0.1, bar_height=0.8, target_width=0.2, target_color='red', low_value=offset-bar_range, high_value=offset+bar_range, target_value=offset))


        # f [kg] = (Vmeasured [muV] - offset [muV]) * 1e-6 * FS [kg] / (RO [V/V] * Gain [V/V])
        # f [kg] = (Vmeasured - 2.2e6) * 1e-6 * 2 / (0.005 * 200)
        # FS ... full scale
        # RO ... rated output
        # Gain ... 100 @ Forza
        scaler_force = SP.Scaler(scale=1e-6*2/(0.005*100), pre_offset=-offset)

        angle = SP.Angle()
        butter_angle = SP.ButterFilter(4, 1)
        angle_y_alignment = SP.Scaler(1, -90)

        scaler_amp = SP.Scaler(scale=1e-3, pre_offset=-offset)
        butter_amp1_text = SP.ButterFilter(4, 2)
        butter_amp2_text = SP.ButterFilter(4, 2)
        butter_amp1_bar = SP.ButterFilter(4, 1)
        butter_amp2_bar = SP.ButterFilter(4, 1)


        arrow.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        arrow.addSignalProcessingToLSLStream(scaler_force, channels=[64, 65])

        angle_text.controlStateWithLSLStream('quattrocento', channels=[64])
        angle_text.addSignalProcessingToLSLStream(scaler_force, channels=[64, 65])
        angle_text.addSignalProcessingToLSLStream(angle, channels=[64, 65])
        angle_text.addSignalProcessingToLSLStream(angle_y_alignment, channels=[64])
        angle_text.addSignalProcessingToLSLStream(butter_angle, channels=[64])

        amplifier1_val_text.controlStateWithLSLStream('quattrocento', channels=[64])
        amplifier1_val_text.addSignalProcessingToLSLStream(scaler_amp, channels=[64])
        amplifier1_val_text.addSignalProcessingToLSLStream(butter_amp1_text, channels=[64])

        amplifier2_val_text.controlStateWithLSLStream('quattrocento', channels=[65])
        amplifier2_val_text.addSignalProcessingToLSLStream(scaler_amp, channels=[65])
        amplifier2_val_text.addSignalProcessingToLSLStream(butter_amp2_text, channels=[65])

        amplifier1_bar.controlStateWithLSLStream('quattrocento', channels=[64])
        amplifier1_val_text.addSignalProcessingToLSLStream(butter_amp1_bar, channels=[64])
        amplifier2_bar.controlStateWithLSLStream('quattrocento', channels=[65])
        amplifier2_val_text.addSignalProcessingToLSLStream(butter_amp2_bar, channels=[65])

        arrow.activate()
        cross.activate()
        angle_text.activate()
        amplifier1_val_text.activate()
        amplifier2_val_text.activate()
        amplifier1_bar.activate()
        amplifier2_bar.activate()
        amplifier1_label_text.activate()
        amplifier2_label_text.activate()

        self.script = [ScriptItem(name='trial_start', time=0, actions=[]),
                       ScriptItem(name='trial_end', time=np.inf, actions=[])]
