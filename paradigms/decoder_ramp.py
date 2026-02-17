from pathlib import Path
import numpy as np
from functools import partial

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
from yaga_modules.pacman import Pacman
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('test') / Path('data')
    task_name = 'decoder_ramp'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost', #nidaqmx_trigger_line='Dev1/port1/line3',
                         nidaqmx_analog_input_channels=["Dev1/ai1", "Dev1/ai2"], nidaqmx_analog_input_min_vals=[-5, -10], nidaqmx_analog_input_max_vals=[5, 10])

        # trial configuration
        n_trials = 2
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 45
        inter_trial_interval_max = 45

        # ramp configuration (low (rest) -> up -> high (hold) -> down -> low)
        ramp_low_interval = 3
        ramp_up_interval = 10
        ramp_high_interval = 30
        ramp_down_interval = 10
        ramp_hold_force = 0.1

        # force sensor configuration
        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)
        force_channel = 1

        # Pacman configuration
        pacman_low_y_pos = -0.8
        pacman_high_y_pos = 0.5
        pacman_delay = 5 # time delay between dots entering the screen and reaching the pacman
        pacman_item_generation_frequency = 15 # for 1 Hz
        initial_distance_to_pacman = 1.8 - (-1.4) # dot generation x-position minus Pacman x-position; positions are had-coded in Pacman class


        info_text = self.registerObject(GO.Text('prepare for force tracking', scale_x=0.1, scale_y=0.1, color='white'))
        pacman = self.registerObject(Pacman(item_speed=initial_distance_to_pacman/pacman_delay, item_generator='ramp', item_generation_frequency=pacman_item_generation_frequency, phase_duration=[ramp_low_interval, ramp_up_interval, ramp_high_interval, ramp_down_interval, ramp_low_interval], phase_value=[pacman_low_y_pos, pacman_high_y_pos]))
        attention_beep = self.registerObject(AO.Beep())

        # Pacman force control
        #max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        butter = SP.ButterFilter(4, 5)
        map_y = SP.LinearMap(0, ramp_hold_force, pacman_low_y_pos, pacman_high_y_pos)
        # pacman.controlStateWithLSLStreams(['MouseControllerStream'], channels=[force_channel])
        pacman.controlStateWithLSLStreams(['yaga_nidaq'], channels=[force_channel])
        # pacman.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        #pacman.controlStateWithLSLStreams(['MouseControllerStream'], channels=[force_channel])
        #pacman.addSignalProcessingToLSLStream(map_y, channels=[force_channel])
        #pacman.addSignalProcessingToLSLStream(butter, channels=[force_channel])

        pacman.activate() # Pacman must be active during the whole run so that the LSL output stream is continuously populated


        # sequence definition
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_start_time = pre_paradigm_interval
                trial_start_time_type = "abs"
                trial_start_time_ref = ""
            else:
                trial_start_time = np.random.uniform(inter_trial_interval_min, inter_trial_interval_max)
                trial_start_time_type = "rel"
                trial_start_time_ref = "trial_end"
            self.script.append(ScriptItem(name='trial_start', time=trial_start_time, time_type=trial_start_time_type, rel_name=trial_start_time_ref, actions=[info_text.activate, attention_beep.beep]))

            self.script.append(ScriptItem(name="pacman_start", time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, pacman.start]))
            self.script.append(ScriptItem(name="ramp_start", time=pacman_delay, time_type='rel', rel_name='pacman_start', actions=[]))
            self.script.append(ScriptItem(name='generator_stop', wait_for_signal=Pacman.GENERATION_FINISHED, actions=[]))
            self.script.append(ScriptItem(name='trial_end', time=pacman_delay, time_type='rel', rel_name='generator_stop', actions=[pacman.stop])) # wait until all dots have reached Pacman

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
