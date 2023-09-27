from scipy import signal
import numpy as np
import pyxdf


# set channels to a constant value
class Constant:

    def __init__(self, value):
        self.value = value

    def update(self, samples_in, fs):
        samples_out = np.full(samples_in.shape, self.value)
        return samples_out


# copy channel
class CopyChannel:

    def __init__(self, channel_in, channel_out):
        self.channel_in = channel_in
        self.channel_out = channel_out

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]
        samples_out = samples_in
        samples_out[self.channel_out, :] = samples_in[self.channel_in, :]
        return samples_out


# Butterworth filter
class ButterFilter:

    def __init__(self, order, cutoff_frqs, filter_type='lowpass'):
        self.order = order
        self.cutoff_frqs = cutoff_frqs
        self.filter_type = filter_type
        self.z = None

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        # initialize filter
        if self.z is None:
            # design filter
            print('update: setting stream sampling rate to %f' % fs)
            self.sos = signal.butter(self.order, self.cutoff_frqs, self.filter_type, fs=fs, output='sos')

            # initialize filter state for step response steady-state
            z_one_channel = signal.sosfilt_zi(self.sos) # [sections x 2]
            n_channels = samples_in.shape[0]
            self.z = np.tile(z_one_channel[:, np.newaxis, :], [1, n_channels, 1]) # [sections x n_channels x 2]

        # apply Butterworth filter using cascaded second-order sections (filter along last dimension)
        samples_out, self.z = signal.sosfilt(self.sos, samples_in, zi=self.z)

        return samples_out


# calculates the angle in radians between the x-axis and the point given by (x,y)
class Angle:

    def update(self, samples_in, fs):
        # samples_in: [2 channels x samples]
        # samples_out: [1 x samples]

        assert samples_in.shape[0] == 2, 'the "Angle" signal processing method expects a 2-channel signal'
        samples_out = np.arctan2(samples_in[0, :], samples_in[1, :])*180.0/np.pi
        return samples_out


# integrate channel wise
class Integrate:

    def __init__(self,  factor=1):
        self.buffer = None
        self.factor = factor

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        if not self.buffer:
            self.buffer = np.zeros((samples_in.shape[0], 1))

        samples_out = self.buffer + np.sum(samples_in, axis=1)*self.factor
        self.buffer = samples_out

        return samples_out


# differentiate channel wise
class Diff:

    def __init__(self):
        self.buffer = None

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        if self.buffer:
            samples_out = np.diff(samples_in, 1, axis=1, prepend=self.buffer[:, np.newaxis])
        else:
            samples_out = np.diff(samples_in, 1, axis=1, prepend=0)
        self.buffer = samples_in[:, -1] # buffer last sample
        return samples_out


# sum over channels
class Sum:

    def update(self, samples_in, fs):
        # samples_in: [channels x samples]
        # samples_out: [1 x samples]

        samples_out = np.sum(samples_in, axis=0, keepdims=True)
        return samples_out


# mean over channels
class Mean:

    def update(self, samples_in, fs):
        # samples_in: [channels x samples]
        # samples_out: [1 x samples]

        samples_out = np.mean(samples_in, axis=0, keepdims=True)
        return samples_out


# sample-wise standard deviation (aka Global Field Power)
class StdDev:

    def update(self, samples_in, fs):
        # samples_in: [channels x samples]
        # samples_out: [1 x samples]

        samples_out = np.std(samples_in, axis=0, keepdims=True)
        return samples_out


# multiply channels by a scaling factor and add offsets before and after scaling
class Scaler:

    def __init__(self, scale=1, pre_offset=0, post_offset=0):
        self.scale = scale
        self.pre_offset = pre_offset
        self.post_offset = post_offset

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        samples_out = (samples_in + self.pre_offset) * self.scale + self.post_offset
        return samples_out


# linearly map channels to a target range
class LinearMap:

    def __init__(self, in_val1, in_val2, out_val1, out_val2):
        self.in_val1 = in_val1
        self.in_val2 = in_val2
        self.out_val1 = out_val1
        self.out_val2 = out_val2

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        samples_out = (samples_in - self.in_val1) / (self.in_val2 - self.in_val1) * (self.out_val2 - self.out_val1) + self.out_val1
        return samples_out


# limit channels to minimum and maximum values
class Limit:

        def __init__(self, min_val=None, max_val=None):
            self.min_val = min_val
            self.max_val = max_val

        def update(self, samples_in, fs):
            # samples_in/out: [channels x samples]

            samples_out = np.clip(samples_in, self.min_val, self.max_val)
            return samples_out


# calculate absolute values
class Abs:

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        samples_out = np.absolute(samples_in)
        return samples_out


# calculate power/exponent
class Power:

    def __init__(self, exponent):
        self.exponent = exponent

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        samples_out = np.power(samples_in, self.exponent)
        return samples_out


# calculate Euclidean norm over channels
class EuclidNorm:

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        samples_out = np.linalg.norm(samples_in, axis=0)
        return samples_out


# normalize channels by the maximum Euclidean norm found in the specified XDF file (e.g. force normalization)
class MaxEuclidNormalizationXDF:

    def __init__(self, xdf_file, data_stream_name, marker_stream_name, start_marker, end_marker, data_stream_channels=None, offset=None, filter_window_length=31):
        data, _ = pyxdf.load_xdf(xdf_file)

        # self.filter_cutoff_frqs = filter_cutoff_frqs
        # self.filter_order = filter_order

        # find data and marker streams
        data_stream = list(filter(lambda x: x['info']['name'] == [data_stream_name], data))
        marker_stream = list(filter(lambda x: x['info']['name'] == [marker_stream_name], data))
        if len(data_stream) == 0:
            raise Exception('data stream "%s" not found' % data_stream_name)
        if len(marker_stream) == 0:
            raise Exception('marker stream "%s" not found' % marker_stream_name)
        if len(data_stream) > 1:
            raise Exception('found more than one data stream "%s"' % data_stream_name)
        if len(marker_stream) > 1:
            raise Exception('found more than one marker stream "%s"' % marker_stream_name)
        data_stream = data_stream[0]
        marker_stream = marker_stream[0]

        # find start and end marker indices
        start_marker_idcs = [idx for idx, item in enumerate(marker_stream['time_series']) if item[0] == start_marker]
        end_marker_idcs = [idx for idx, item in enumerate(marker_stream['time_series']) if item[0] == end_marker]
        assert len(start_marker_idcs) == len(end_marker_idcs), 'number of start and end markers are different'

        # get signal
        stream_fs = int(float(data_stream['info']['nominal_srate'][0]))
        if data_stream_channels:
            raw_signal = data_stream['time_series'][:, data_stream_channels].transpose() # [channels x samples]
        else:
            raw_signal = data_stream['time_series'].transpose() # [channels x samples]
        n_channels = raw_signal.shape[0]

        # filter signal
        assert np.mod(filter_window_length, 2), '"filter_window_length" must be odd'
        filtered_signal = np.empty(raw_signal.shape)
        for channel_idx in range(n_channels):
            filtered_signal[channel_idx, :] = signal.medfilt(raw_signal[channel_idx, :], filter_window_length)

        if offset:
            self.min_values = offset*np.ones((n_channels,))
            print('max Euclidean norm normalization: using predefined offset: ', self.min_values)
        else:
            self.min_values = np.amin(filtered_signal, axis=1)
            print('max Euclidean norm normalization: found offset: ', self.min_values)
        offsetfree_signal = filtered_signal - self.min_values[:, np.newaxis] # [channels x samples]

        # calculate 2-norm
        signal_norm = np.linalg.norm(offsetfree_signal, axis=0)

        # extract epochs
        epoched_signal = np.array(())
        for start_marker_idx, end_marker_idx in zip(start_marker_idcs, end_marker_idcs):
            start_timestamp = marker_stream['time_stamps'][start_marker_idx]
            end_timestamp = marker_stream['time_stamps'][end_marker_idx]
            assert end_timestamp > start_timestamp, 'end maker must be after start marker'
            signal_epoch = signal_norm[np.where(np.logical_and(data_stream['time_stamps'] >= start_timestamp, data_stream['time_stamps'] <= end_timestamp))]
            epoched_signal = np.concatenate((epoched_signal, signal_epoch))

        # find maximum value
        self.norm_value = np.amax(epoched_signal)
        print('max Euclidean norm normalization: found maximum value of %.2f' % self.norm_value)


    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]

        # normalize samples
        samples_out = (samples_in - self.min_values[:, np.newaxis]) / self.norm_value
        return samples_out


# normalize channels by the maximum power found in the specified XDF file (e.g. EMG power normalization)
class MaxAvgPowerNormalizationXDF:

    def __init__(self, xdf_file, data_stream_name, marker_stream_name, start_marker, end_marker, data_stream_channels=None, prefilter_order=4, prefilter_cutoff_frqs=[150, 300], postfilter_win_length=1):
        data, _ = pyxdf.load_xdf(xdf_file)

        self.prefilter_cutoff_frqs = prefilter_cutoff_frqs
        self.prefilter_order = prefilter_order
        self.postfilter_win_length = postfilter_win_length # [s]

        # find data and marker streams
        data_stream = list(filter(lambda x: x['info']['name'] == [data_stream_name], data))
        marker_stream = list(filter(lambda x: x['info']['name'] == [marker_stream_name], data))
        if len(data_stream) == 0:
            raise Exception('data stream "%s" not found' % data_stream_name)
        if len(marker_stream) == 0:
            raise Exception('marker stream "%s" not found' % marker_stream_name)
        if len(data_stream) > 1:
            raise Exception('found more than one data stream "%s"' % data_stream_name)
        if len(marker_stream) > 1:
            raise Exception('found more than one marker stream "%s"' % marker_stream_name)
        data_stream = data_stream[0]
        marker_stream = marker_stream[0]

        # find start and end marker indices
        start_marker_idcs = [idx for idx, item in enumerate(marker_stream['time_series']) if item[0] == start_marker]
        end_marker_idcs = [idx for idx, item in enumerate(marker_stream['time_series']) if item[0] == end_marker]
        assert len(start_marker_idcs) == len(end_marker_idcs), 'number of start and end markers are different'

        # get signal
        stream_fs = int(float(data_stream['info']['nominal_srate'][0]))
        if data_stream_channels:
            raw_signal = data_stream['time_series'][:, data_stream_channels].transpose() # [channels x samples]
        else:
            raw_signal = data_stream['time_series'].transpose() # [channels x samples]
        n_channels = raw_signal.shape[0]

        # bandpass filter raw signals
        prefilter_sos = signal.butter(self.prefilter_order, self.prefilter_cutoff_frqs, 'bandpass', fs=stream_fs, output='sos')
        # initialize filter state for step response steady-state
        prefilter_z_one_channel = signal.sosfilt_zi(prefilter_sos) # [sections x 2]
        prefilter_z = np.tile(prefilter_z_one_channel[:, np.newaxis, :], [1, n_channels, 1]) # [sections x n_channels x 2]
        filtered_signal, _ = signal.sosfilt(prefilter_sos, raw_signal, zi=prefilter_z)

        # calculate signal power, smooth with a moving average filter, then average over all channels
        mov_avg_samples = int(stream_fs*self.postfilter_win_length)
        postfilter_B = 1.0/mov_avg_samples*np.ones((mov_avg_samples,))
        postfilter_A = 1
        # initialize filter state for step response steady-state
        postfilter_z_one_channel = signal.lfilter_zi(postfilter_B, postfilter_A)
        postfilter_z = np.tile(postfilter_z_one_channel.reshape(1, -1), [n_channels, 1])
        filtered_signal_power, _ = signal.lfilter(postfilter_B, postfilter_A, filtered_signal**2, zi=postfilter_z) # [channels x samples]
        # avg_filtered_signal_power = 10.0*np.log10(np.median(filtered_signal_power, axis=0)) # [samples, ]
        avg_filtered_signal_power = np.median(filtered_signal_power, axis=0) # [samples, ]

        # extract epochs
        epoched_signal = np.array(())
        for start_marker_idx, end_marker_idx in zip(start_marker_idcs, end_marker_idcs):
            start_timestamp = marker_stream['time_stamps'][start_marker_idx]
            end_timestamp = marker_stream['time_stamps'][end_marker_idx]
            assert end_timestamp > start_timestamp, 'end maker must be after start marker'
            signal_epoch = avg_filtered_signal_power[np.where(np.logical_and(data_stream['time_stamps'] >= start_timestamp, data_stream['time_stamps'] <= end_timestamp))]
            epoched_signal = np.concatenate((epoched_signal, signal_epoch))

        # find 90 percentile
        self.max_value = np.percentile(epoched_signal, 90)
        print('max power normalization: found maximum value of %.2f' % self.max_value)

        # reset filter coefficients; they are set in the first update call and adjusted to the online sampling rate
        self.prefilter_sos = None
        self.prefilter_z = None
        self.postfilter_B = None
        self.postfilter_A = None
        self.postfilter_z = None


    def update(self, samples_in, fs):
        # samples_in: [channels x samples]
        # samples_out: [1 x samples]

        # initialize pre&post filters
        if self.prefilter_z is None or self.postfilter_z is None:
            n_channels = samples_in.shape[0]

            # initialize bandpass filter (aka prefilter)
            self.prefilter_sos = signal.butter(self.prefilter_order, self.prefilter_cutoff_frqs, 'bandpass', fs=fs, output='sos')
            prefilter_z_one_channel = signal.sosfilt_zi(self.prefilter_sos) # [sections x 2]
            self.prefilter_z = np.tile(prefilter_z_one_channel[:, np.newaxis, :], [1, n_channels, 1]) # [sections x n_channels x 2]

            # initialize moving average filter (aka postfilter)
            mov_avg_samples = int(fs*self.postfilter_win_length)
            self.postfilter_B = 1.0/mov_avg_samples*np.ones((mov_avg_samples,))
            self.postfilter_A = 1
            z_one_channel = signal.lfilter_zi(self.postfilter_B, self.postfilter_A)
            self.postfilter_z = np.tile(z_one_channel.reshape(1, -1), [n_channels, 1]) # [channels x max(len(a),len(b))-1]

            print('update: initialized filters with the stream sampling rate of %f Hz' % fs)

        # bandpass filter signal
        filtered_samples, self.prefilter_z = signal.sosfilt(self.prefilter_sos, samples_in, zi=self.prefilter_z)

        # calculate signal power, smooth with a moving average filter, then average over all channels
        filtered_samples_power, self.postfilter_z = signal.lfilter(self.postfilter_B, self.postfilter_A, filtered_samples**2, zi=self.postfilter_z) # [channels x samples]
        # avg_filtered_samples_power = (10.0*np.log10(np.median(filtered_samples_power, axis=0))).reshape((1, -1)) # [1, samples]
        avg_filtered_samples_power = np.median(filtered_samples_power, axis=0).reshape((1, -1)) # [1, samples]

        # normalize values
        samples_out = avg_filtered_samples_power / self.max_value
        # samples_out = avg_filtered_samples_power - self.max_value
        # print(samples_out[0, -1])

        return samples_out


# implements a Flappy Bird style control with spikes
class FlappyBirdController:

    def __init__(self, pos_increment=0.1, negative_vel=0.1, switch_interval=1, x_max=1, y_max=1):
        self.pos_increment = pos_increment
        self.negative_vel = negative_vel
        self.switch_interval = switch_interval
        self.x_max = x_max
        self.y_max = y_max

        self.position = np.zeros((2, 1))
        self.last_spike_time = 0 # [samples]
        self.active_dimension_idx = 0
        self.inactive_dimension_idx = 1

    def update(self, samples_in, fs):
        # samples_in/out: [channels x samples]
        assert samples_in.shape[0] == 2, 'the "FlappyBirdControl" signal processing method expects a 2-channel signal'
        # note: only the first channel is evaluated; the method requires a 2-channel input signal to produce a 2-channel output signal

        # switch active and inactive dimensions when switch_interval has passed
        spikes = np.flatnonzero(samples_in[0, :] > 0.5);
        if len(spikes) > 0:
            if self.last_spike_time >= self.switch_interval*fs:
                self.active_dimension_idx, self.inactive_dimension_idx = self.inactive_dimension_idx, self.active_dimension_idx

            self.last_spike_time = samples_in.shape[1] - spikes[-1]
        else:
            # no spike found
            self.last_spike_time = self.last_spike_time + samples_in.shape[1]

        if self.last_spike_time >= self.switch_interval*fs:
            negative_vel_mask = 1
        else:
            negative_vel_mask = 0

        # update positions
        self.position[self.active_dimension_idx] = self.position[self.active_dimension_idx] - samples_in.shape[1]*self.negative_vel*negative_vel_mask + np.sum(spikes)*self.pos_increment
        self.position[self.inactive_dimension_idx] = self.position[self.inactive_dimension_idx] - samples_in.shape[1]*self.negative_vel

        self.position[0] = np.clip(self.position[0], 0, self.x_max)
        self.position[1] = np.clip(self.position[1], 0, self.y_max)

        return self.position
