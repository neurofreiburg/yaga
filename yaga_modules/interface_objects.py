from collections import namedtuple

import pylsl
import numpy as np


MAX_LSL_BUFFER_SAMPLES = 1024 # this allows for sampling rates up to 61 kHz when run with 60 FPS (i.e. 1024*60 Hz)

SignalProcessor = namedtuple('SignalProcessor', ('object', 'channels'))


class InterfaceObject:
    NO_SIGNAL = None

    def __init__(self):
        self.active = False
        self.lsl_inlets = {}
        self.lsl_fs = {}
        self.lsl_signal_processors = {}
        self.lsl_streams_samples = {}
        self.lsl_aggregation_modes = {}
        self.lsl_relay_outlet = None

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def updateState(self, time):
        return InterfaceObject.NO_SIGNAL

    def connectToLSLStreams(self, lsl_stream_names, aggregation_mode='last'):
        for lsl_stream_name in lsl_stream_names:
            if lsl_stream_name not in self.lsl_inlets:
                print('connecting to LSL stream %s...' % lsl_stream_name)
                lsl_info = pylsl.resolve_byprop('name', lsl_stream_name, timeout=15)
                if not lsl_info:
                    raise Exception('timeout: LSL stream "%s" not found' % lsl_stream_name)
                if len(lsl_info) > 1:
                    raise Exception('found more than one LSL stream with name "%s"' % lsl_stream_name)
                lsl_inlet = pylsl.StreamInlet(lsl_info[0], max_buflen=1, recover=True) # note: max_buflen is in seconds if there is a nominal sampling rate
                lsl_fs = lsl_inlet.info().nominal_srate()
                self.lsl_inlets[lsl_stream_name] = lsl_inlet
                self.lsl_fs[lsl_stream_name] = lsl_fs
                self.lsl_signal_processors[lsl_stream_name] = []
                if aggregation_mode == 'last' or aggregation_mode == 'sum' or aggregation_mode == 'mean':
                    self.lsl_aggregation_modes[lsl_stream_name] = aggregation_mode
                else:
                    raise Exception('unkown buffer aggregation mode: "%s"', aggregation_mode)
                self.lsl_streams_samples[lsl_stream_name] = np.zeros((lsl_inlet.info().channel_count(), 1)) # initialize buffer with float64 zeros of shape [channels x 1]
                print('connected')
            else:
                print('stream "%s" is already connected; ignoring connection request' % lsl_stream_name)

    def readLSLStream(self):
        # 1. this function is called with a frequency equal to FPS
        # 2. when new LSL samples are available, the samples are processed with their original sampling rate using a buffer
        # 3a. if LSL sampling rate > FPS: samples are aggregated (= take only last sample (default), sum of samples, or mean of samples)
        # 3b. if LSL sampling rate < FPS: signal is sampled with sample & hold
        # 4. the abstract method _newLSLSampleReceived() is called; it is up to subclasses to implement updates when new LSL samples are received

        if self.lsl_inlets:
            for lsl_stream_name in self.lsl_inlets.keys():

                # read chunk of samples from LSL inlet (non-blocking)
                samples_list, _ = self.lsl_inlets[lsl_stream_name].pull_chunk(timeout=0.0, max_samples=MAX_LSL_BUFFER_SAMPLES)
                assert type(samples_list) is list

                # check if new samples were received, if so, run signal processing methods
                if len(samples_list) > 0:
                    if len(samples_list) == MAX_LSL_BUFFER_SAMPLES:
                        # raise Exception('LSL buffer size is probably too small, extend it to prevent data loss from LSL signals')
                        print('LSL buffer size is probably too small, extend it to prevent data loss from LSL signals (it is OK if this message shows up right after startup)')

                    # convert list of lists into a numpy array
                    lsl_samples = np.array(samples_list).transpose() # [channels x samples]
                    # apply signal processing methods; they operate with sampling rate of the LSL source
                    for processor in self.lsl_signal_processors[lsl_stream_name]:
                        if processor.channels:
                            lsl_samples[processor.channels, :] = processor.object.update(lsl_samples[processor.channels, :], self.lsl_fs[lsl_stream_name])
                        else:
                            lsl_samples[:, :] = processor.object.update(lsl_samples, self.lsl_fs[lsl_stream_name])

                    # downsample signal to FPS with the specified aggregation method
                    if self.lsl_aggregation_modes[lsl_stream_name] == 'last':
                        self.lsl_streams_samples[lsl_stream_name] = lsl_samples[:, -1] # keep only the most recent sample
                    elif self.lsl_aggregation_modes[lsl_stream_name] == 'sum':
                        self.lsl_streams_samples[lsl_stream_name] = np.sum(lsl_samples, axis=1) # calculate buffer sum
                    elif self.lsl_aggregation_modes[lsl_stream_name] == 'mean':
                        self.lsl_streams_samples[lsl_stream_name] = np.mean(lsl_samples, axis=1) # calculate buffer average
                    else:
                        raise Exception('unkown buffer aggregation mode: "%s"', self.lsl_agregation_modes[lsl_stream_name])

            self._relay()
            self._newLSLSampleReceived() # when no new sample has been received, this method uses the last received sample (i.e., sample & hold)

    # signal processing methods must generate output samples with (1) the same number of channels as the input samples, or (2) outputs with exactly one channel
    # in the latter case, output sample channels are broadcasted
    def addSignalProcessingToLSLStream(self, processor_object, channels=None, lsl_stream_name=None):
        if isinstance(lsl_stream_name, str):
            assert lsl_stream_name in self.lsl_signal_processors, 'unknown stream name'
        elif lsl_stream_name == None:
            assert self.lsl_signal_processors, 'interface object is not connected to an LSL stream'
            lsl_stream_names = list(self.lsl_signal_processors)
            if len(lsl_stream_names) > 1:
                raise Exception('Interface object is controlled by more than one LSL stream. You need to explicitly specify with the parameter "lsl_stream_name" to which LSL stream this processor is applied.')
            lsl_stream_name = lsl_stream_names[0]
        else:
            raise Exception('"lsl_stream_name" must be None or a string (None selects the first added stream)')
        self.lsl_signal_processors[lsl_stream_name].append(SignalProcessor(object=processor_object, channels=channels))

    # configure LSL signal relay after processing
    def relayLSLSignals(self, lsl_in_signals, channels, lsl_out_signal, fps=60):
        assert len(lsl_in_signals) == len(channels), "relayLSLSignals: for every LSL input signal, a list of channels to be relayed must be specified ('lsl_in_signals' must be a list; 'channel' must be a list of lists)"
        n_total_channels = sum([len(element) for element in channels])

        lsl_info = pylsl.StreamInfo(lsl_out_signal, 'relay', n_total_channels, fps, 'float32', lsl_out_signal + "_relay")
        self.lsl_relay_outlet = pylsl.StreamOutlet(lsl_info)
        self.lsl_relay_in_signals = lsl_in_signals
        self.lsl_relay_channels = channels
        self.lsl_relay_buffer = np.zeros((n_total_channels))

    # relay LSL signals
    def _relay(self):
        if self.lsl_relay_outlet:
            # copy LSL samples from current time frame into buffer
            start_ch_idx = 0
            for signal_idx in range(len(self.lsl_relay_in_signals)):
                end_ch_idx = start_ch_idx + len(self.lsl_relay_channels[signal_idx])
                self.lsl_relay_buffer[start_ch_idx:end_ch_idx] = self.lsl_streams_samples[self.lsl_relay_in_signals[signal_idx]][self.lsl_relay_channels[signal_idx]].reshape((-1,))
                start_ch_idx = end_ch_idx

            self.lsl_relay_outlet.push_sample(self.lsl_relay_buffer, pushthrough=True)

    # subclasses can re-implement this method to execute specific updates based on the most recent LSL sample (i.e. self.lsl_sample)
    # by default, this method does nothing
    def _newLSLSampleReceived(self):
        pass
