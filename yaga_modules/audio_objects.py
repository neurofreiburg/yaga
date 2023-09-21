import numpy as np
import collections
from pathlib import Path
from scipy.io.wavfile import write
from scipy.signal import windows
from direct.showbase.ShowBase import ShowBase
import rtmixer
import sounddevice as sd

from yaga_modules.interface_objects import InterfaceObject


class AudioObject(InterfaceObject):

    def __init__(self):
        super().__init__()
        self.lsl_control_streams = None
        self.control_channels = None
        self.deactivate()

    def controlWithLSLStream(self, lsl_stream_name, channels, aggregation_mode='last'):
        assert isinstance(lsl_stream_name, str), '"lsl_stream_name" must be a string'
        assert isinstance(channels, list), '"channels" must be a list'
        self.connectToLSLStreams([lsl_stream_name], aggregation_mode)
        self.lsl_control_streams = [lsl_stream_name]
        self.control_channels = channels

    def controlWithLSLStreams(self, lsl_stream_names, channels, aggregation_mode='last'):
       assert isinstance(lsl_stream_names, list), '"lsl_stream_names" must be a list'
       assert isinstance(channels, list), '"channels" must be a list'
       self.connectToLSLStreams(lsl_stream_names, aggregation_mode)
       self.lsl_control_streams = lsl_stream_names
       self.control_channels = channels


class SpikeSound(AudioObject):
    def __init__(self, beep_frequencies=[1000], beep_channels=['both'], beep_duration=0.01, downsample=1, dynamic_frq=False, dynamic_frq_factor=1, dynamic_max_frq=20, dynamic_mov_avg=3, dynamic_exp_avg_alpha=None):
        super().__init__()

        if isinstance(beep_frequencies, float) or isinstance(beep_frequencies, int):
            beep_frequencies = [beep_frequencies]

        if isinstance(beep_channels, str):
            beep_channels = [beep_channels]

        # parameter checks
        assert len(beep_frequencies) == len(beep_channels), '"beep_frequencies" and "beep_channels" must have the same length'
        for beep_frequency in beep_frequencies:
            assert beep_frequency > 100 and beep_frequency < 10000, 'frequencies must be between 100 Hz and 10 kHz'
        for beep_channel in beep_channels:
            assert beep_channel == 'left' or beep_channel == 'right' or beep_channel == 'both', 'channel must be one of: right, left, both'
        assert isinstance(downsample, int) and downsample > 0, '"downsample" must be a positive integer'
        assert(not (dynamic_mov_avg and dynamic_exp_avg_alpha)), '"dynamic_mov_avg" and "dynamic_exp_avg_alpha" must not have a value assigned at the same time'
        if dynamic_mov_avg:
            assert isinstance(dynamic_mov_avg, int) and dynamic_mov_avg >= 2,'"dynamic_mov_avg" must be an integer larger than 1'

        self.downsample = downsample
        self.n_beeps = len(beep_frequencies)
        self.beep_frequencies = beep_frequencies
        self.beep_channels = beep_channels
        self.dynamic_frq = dynamic_frq
        self.dynamic_frq_factor = dynamic_frq_factor
        self.dynamic_max_frq = dynamic_max_frq
        self.dynamic_exp_avg_alpha = dynamic_exp_avg_alpha

        # generate beep data buffer
        # fs = 44100
        fs = 48000
        beep_duration = int(beep_duration*fs) / fs
        self.t = np.linspace(0., beep_duration, int(fs*beep_duration))
        self.beep_sounds = [None]*self.n_beeps
        for beep_idx in range(self.n_beeps):
            self.beep_sounds[beep_idx] = np.zeros([len(self.t), 2], dtype=np.float32)
            beep = 0.5 * np.sin(2. * np.pi * beep_frequencies[beep_idx] * self.t) * windows.kaiser(len(self.t), beta=5)
            if self.beep_channels[beep_idx] == 'left':
                self.beep_sounds[beep_idx][:, 0] = beep
            elif self.beep_channels[beep_idx] == 'right':
                self.beep_sounds[beep_idx][:, 1] = beep
            elif self.beep_channels[beep_idx] == 'both':
                self.beep_sounds[beep_idx][:, 0] = beep
                self.beep_sounds[beep_idx][:, 1] = beep
            else:
                raise Exception('unknown channel specification: %s', self.beep_channels[beep_idx])

        # variables used for downsampling
        self.spike_counts = [-1]*self.n_beeps

        # variables used for dynamic beep generation
        if dynamic_mov_avg:
            # use moving average when dynamic frq mode is requested
            self.spike_times = [collections.deque(maxlen=dynamic_mov_avg) for _ in range(self.n_beeps)]
        elif dynamic_exp_avg_alpha:
            # use exponential smoothing when dynamic frq mode is requested
            # buffer size is set to two spike times as only the most recent ISIs will be calculated
            self.spike_times = [collections.deque(maxlen=2) for _ in range(self.n_beeps)]
            self.last_smoothed_isi = [0]*self.n_beeps

        self.mixer = rtmixer.Mixer(channels=2, blocksize=0, samplerate=fs, latency='low')
        self.mixer.start()

    def updateState(self, time):
        if self.active and self.lsl_control_streams and self.lsl_streams_samples[self.lsl_control_streams[0]] is not None:
            assert len(self.lsl_control_streams) == 1, 'SpikeSound: exactly one control stream must be specified'
            assert len(self.control_channels) == self.n_beeps, 'SpikeSound: "channels" must have the same number of elements as defined beep frequencies'

            # check whether any unit spiked
            for beep_idx in range(self.n_beeps):
                spikes = self.lsl_streams_samples[self.lsl_control_streams[0]][self.control_channels[beep_idx]]
                self.spike_counts[beep_idx] += spikes

                if self.dynamic_frq and spikes > 0:
                    # compute beep frequency based on the smoothed inter spike interval

                    # save spike times in a circular buffer and calculate inter spike time intervals
                    self.spike_times[beep_idx].append(time)
                    if len(self.spike_times[beep_idx]) > 1:
                        isis = np.diff(self.spike_times[beep_idx]) # this also works for exponential smoothing in which case only one ISI is calculated as buffer is then of size 2
                    else:
                        isis = np.array([1])

                    if self.dynamic_exp_avg_alpha:
                        # exponential smoothing
                        self.last_smoothed_isi[beep_idx] = self.dynamic_exp_avg_alpha*isis + (1.0 - self.dynamic_exp_avg_alpha)*self.last_smoothed_isi[beep_idx]
                        avg_isi = self.last_smoothed_isi[beep_idx]
                    else:
                        # moving average
                        avg_isi = isis.mean()

                    dynamic_frq = self.beep_frequencies[beep_idx] + self.dynamic_frq_factor * min(1.0/avg_isi, self.dynamic_max_frq)

                    # generate beep data buffer
                    beep = 0.5 * np.sin(2. * np.pi * dynamic_frq * self.t) * windows.kaiser(len(self.t), beta=5)
                    if self.beep_channels[beep_idx] == 'left':
                        self.beep_sounds[beep_idx][:, 0] = beep
                    elif self.beep_channels[beep_idx] == 'right':
                        self.beep_sounds[beep_idx][:, 1] = beep
                    elif self.beep_channels[beep_idx] == 'both':
                        self.beep_sounds[beep_idx][:, 0] = beep
                        self.beep_sounds[beep_idx][:, 1] = beep

                if spikes > 1:
                    print('LSL buffer contained multiple spikes, check system speed')
                if spikes > 0 and self.spike_counts[beep_idx] % self.downsample == 0:
                    action = self.mixer.play_buffer(self.beep_sounds[beep_idx], 2, allow_belated=True)

            return InterfaceObject.NO_SIGNAL


# note: a delay of 0.2s or more reduces the jitter considerably
class Beep(AudioObject):
    def __init__(self, beep_frequency=2000, beep_amplitude=0.5,  beep_duration=0.15, beep_channels='both', delay=0):
        super().__init__()

        # parameter checks
        assert beep_frequency > 100 and beep_frequency < 10000, 'frequency must be between 100 Hz and 10 kHz'
        assert beep_channels == 'left' or beep_channels == 'right' or beep_channels == 'both', 'channels must be one of: right, left, both'

        self.beep_frequency = beep_frequency
        self.beep_channels = beep_channels
        self.delay = delay

        # generate beep data buffer
        # fs = 44100
        fs = 48000
        beep_duration = int(beep_duration*fs) / fs
        t = np.linspace(0., beep_duration, int(fs*beep_duration))
        # beep = beep_amplitude * np.sin(2. * np.pi * beep_frequency * t) * windows.kaiser(len(t), beta=5) # windowing can reduce sound artefacts
        beep = beep_amplitude * np.sin(2. * np.pi * beep_frequency * t)
        self.beep_sound = np.zeros([len(t), 2], dtype=np.float32)
        if self.beep_channels == 'left':
            self.beep_sound[:, 0] = beep
        elif self.beep_channels == 'right':
            self.beep_sound[:, 1] = beep
        elif self.beep_channels == 'both':
            self.beep_sound[:, 0] = beep
            self.beep_sound[:, 1] = beep
        else:
            raise Exception('unknown channel specification: %s', self.beep_channels)

        self.mixer = rtmixer.Mixer(channels=2, blocksize=0, samplerate=fs, latency='low', dither_off=True)
        self.mixer.start()

    def beep(self):
        if self.delay > 0:
            self.mixer.play_buffer(self.beep_sound, 2, start=self.mixer.time + self.delay, allow_belated=False)
        else:
            self.mixer.play_buffer(self.beep_sound, 2, allow_belated=True)
