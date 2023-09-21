from pathlib import Path
import numpy as np
from functools import partial

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
from yaga_modules.pacman import Pacman
import yaga_modules.graphic_objects as GO
import yaga_modules.audio_objects as AO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):
    root_dir = Path.home() / Path('studies') / Path('jaime2023') / Path('data')
    task_name = 'sinus'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=True, lsl_recorder_host='localhost', nidaqmx_event='trial_start', nidaqmx_trigger_line='Dev1/port1/line3', nidaqmx_high_duration=0.5)

        n_trials = 6
        pre_paradigm_interval = 5
        post_paradigm_interval = 5
        inter_trial_interval_min = 25
        inter_trial_interval_max = 35

        pacman_trial_duration = 35 # [s]
        pacman_wait_duration = 5 # time delay between dots entering the screen and reaching the pacman
        pacman_sinus_min_force = 0.07
        pacman_sinus_max_force = 0.10

        pacman_upper_force = 0.012
        pacman_lower_force = 0.008
        frequency_1 = 0.5 # [Hz]
        frequency_2 = 1.0
        frequency_3 = 1.5

        force_amp_voltage_offset = 2.758e6 # more reliable
        # force_amp_voltage_offset = 2.7606e6 # (has sticker)
        force_channel = 256

        pacman_amplitude = 0.5
        pacman_item_generation_base_rate = 70 # for 1 Hz
        screen_ratio = 16/9
        screen_distance = screen_ratio + 1.4 # Pacman x position is -1.4

        info_text = self.registerObject(GO.Text('prepare for force ramp up & down', scale_x=0.1, scale_y=0.1, color='white'))        
        pacman = self.registerObject(Pacman(item_speed=screen_distance/pacman_wait_duration, item_generator='sinus', item_generation_frequency=100, amplitude=pacman_amplitude, frequency=frequency_1, highscore=True))
        attention_beep = self.registerObject(AO.Beep())

        # Pacman force control
        max_normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [force_channel], force_amp_voltage_offset)
        butter = SP.ButterFilter(4, 5)
        map_y = SP.LinearMap(pacman_sinus_min_force, pacman_sinus_max_force, -pacman_amplitude, pacman_amplitude)
        pacman.controlStateWithLSLStreams(['quattrocento'], channels=[force_channel])
        pacman.addSignalProcessingToLSLStream(max_normalization, channels=[force_channel])
        pacman.addSignalProcessingToLSLStream(map_y, channels=[force_channel])
        pacman.addSignalProcessingToLSLStream(butter, channels=[force_channel])

        pacman.activate() # Pacman must be active during the whole run so that the LSL output stream is continuously populated

        # paradigm definition
        n_classes = 3
        assert n_trials % n_classes == 0, "number of trials must be a multiple of the number of classes (i.e. 3)"
        trial_classes = np.tile(np.arange(1, n_classes + 1), (int(n_trials/n_classes), 1)).reshape((-1))
        np.random.shuffle(trial_classes) # inplace
        self.script = []
        for trial_idx in range(n_trials):
            if trial_idx == 0:
                trial_script_items = [ScriptItem(name='trial_start', time=pre_paradigm_interval, actions=[info_text.activate, attention_beep.beep])]
            else:
                trial_script_items = [ScriptItem(name='trial_start', time=np.random.uniform(inter_trial_interval_min, inter_trial_interval_max), time_type='rel', rel_name='trial_end', actions=[info_text.activate, attention_beep.beep])]

            trial_class = trial_classes[trial_idx]
            if trial_class == 1:
                frequency = frequency_1
                class_name = "frequency1"
            elif trial_class == 2:
                frequency = frequency_2
                class_name = "frequency2"
            elif trial_class == 3:
                frequency = frequency_3
                class_name = "frequency3"
            trial_script_items.append(ScriptItem(name=class_name, time=3, time_type='rel', rel_name='trial_start', actions=[info_text.deactivate, partial(setattr, pacman, 'item_generation_frequency', pacman_item_generation_base_rate*frequency), partial(setattr, pacman, 'frequency', frequency), pacman.start]))
            trial_script_items.append(ScriptItem(name='trial_end', time=pacman_trial_duration, time_type='rel', rel_name='trial_start', actions=[pacman.stop]))
            self.script.extend(trial_script_items)

        self.script.append(ScriptItem(time=post_paradigm_interval, time_type='rel', rel_name='trial_end', actions=[]))
