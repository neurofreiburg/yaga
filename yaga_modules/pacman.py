import numpy as np
from scipy import signal
import math
import pylsl
import pymonctl
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import LColor, TransparencyAttrib
from panda3d.core import TextNode, TextFont

from yaga_modules.interface_objects import InterfaceObject
from yaga_modules.graphic_objects import GraphicObject2D
from yaga_modules.colormaps import StdColorMap


IMG_RESOURCES_DIR = 'resources/images'
FONT_RESOURCES_DIR = 'resources/fonts'


class Pacman(GraphicObject2D):
    GENERATION_FINISHED = 'generation_finished'

    def __init__(self, pos_x=0, pos_y=0, depth=0, item_generator='random', item_speed=0.5, item_generation_frequency=15,
                 amplitude=1, frequency=0.5, phase_duration=None, phase_value=None, noise_stddev=3, neg_feedback_type=None, highscore=True):

        node = aspect2d.attachNewNode('main')

        self.item_color = StdColorMap['white']
        self.item_size = 0.01
        self.items_left_limit = -1.8
        self.items_right_limit = 1.8

        self.item_speed = item_speed
        self.item_generation_frequency = item_generation_frequency
        self.item_generator = item_generator

        self.amplitude = amplitude
        self.frequency = frequency
        self.phase_duration = phase_duration
        self.phase_value = phase_value
        self.noise_stddev = noise_stddev
        self.filter_order = 4

        self.pacman_x_pos = -1.4
        self.pacman_size = 0.08
        self.pacman_color = StdColorMap['gold']
        self.pacman_neg_feedback_color = StdColorMap['red']
        self.hit_distance_threshold = 0.05

        self.gradient_x_pos = -1.4
        self.gradient_width = 0.3
        self.gradient_max_displacement = 0.2
        self.gradient_color_left_to_right = StdColorMap['lime']
        self.gradient_color_right_to_left = StdColorMap['red']

        self.highscore = highscore
        self.highscore_x_pos = 0
        self.highscore_y_pos = -0.8
        self.highscore_text_size = 0.2
        self.highscore_counter = 0
        self.highscore_text_color = StdColorMap['lime']
        self.highscore_bg_color = StdColorMap['white']
        self.highscore_frame_color = StdColorMap['black']

        # item template
        self.item_template = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
        self.item_template.setColor(LColor(self.item_color, w=255)/255)
        self.item_template.setTransparency(TransparencyAttrib.MAlpha)
        self.item_template.setScale(self.item_size, 1, self.item_size)
        self.item_template.setBin('fixed', -1)
        self.item_template.hide()

        # Pacman
        self.pacman = OnscreenImage(image=IMG_RESOURCES_DIR + '/pacman.png', parent=node)
        self.pacman.setColor(LColor(self.pacman_color, w=255)/255)
        self.pacman.setTransparency(TransparencyAttrib.MAlpha)
        self.pacman.setScale(self.pacman_size, 1, self.pacman_size)
        self.pacman.setPos(self.pacman_x_pos, 0, 0)

        # negative feedback
        if neg_feedback_type == 'color':
            self.neg_feedback_type = 'color'
        elif neg_feedback_type == 'pos':
            self.neg_feedback_type = 'pos'

            # draw left->right gradient
            self.gradient1 = OnscreenImage(image=IMG_RESOURCES_DIR + '/pacman_gradient.png', parent=node)
            self.gradient1.setColor(LColor(self.gradient_color_left_to_right, w=255)/255)
            self.gradient1.setTransparency(TransparencyAttrib.MAlpha)
            self.gradient1.setScale(self.gradient_width, 1, 1)
            self.gradient1.setPos(self.gradient_x_pos, 0, 0)
            self.gradient1.setBin('fixed', -depth - 1)

            # draw right->left gradient
            self.gradient2 = OnscreenImage(image=IMG_RESOURCES_DIR + '/pacman_gradient.png', parent=node)
            self.gradient2.setColor(LColor(self.gradient_color_right_to_left, w=255)/255)
            self.gradient2.setTransparency(TransparencyAttrib.MAlpha)
            self.gradient2.setScale(self.gradient_width, 1, 1)
            self.gradient2.setPos(self.gradient_x_pos, 0, 0)
            self.gradient2.setPos(self.gradient_x_pos, 0, 0)
            self.gradient2.setHpr(180, 0, 0)
            self.gradient2.setBin('fixed', -depth - 1)
        elif neg_feedback_type == None:
            self.neg_feedback_type = None
        else:
            raise Exception('unkown negative feedback type')

        # highscore counter
        font = loader.loadFont(FONT_RESOURCES_DIR + '/FreeSans.ttf')
        font.setPixelsPerUnit(256)
        self.highscore_node = OnscreenText("0", mayChange=True, font=font, parent=node)
        self.highscore_node.setAlign(TextNode.ACenter)
        self.highscore_node.setScale(self.highscore_text_size, self.highscore_text_size)
        self.highscore_node.setPos(self.highscore_x_pos, self.highscore_y_pos)
        self.highscore_node.setFg(LColor(self.highscore_text_color, w=255)/255)
        if not self.highscore:
            self.highscore_node.hide()

        # generator initializiations
        self.items = []
        self.generate_items = False
        self.initial_time = None
        self.last_update_time = 0
        self.last_item_generation_time = -math.inf
        if self.item_generator == 'constant':
            pass
        elif self.item_generator == 'sinus':
            pass
        elif self.item_generator == 'chirp':
            assert len(frequency) == 2, 'Pacman: "frequency must be a list with 2 elements (start & end frequency)'
            assert phase_duration, 'Pacman: "phase_duration" is not set'
        elif self.item_generator == 'ramp':
            assert phase_duration, 'Pacman: "phase_duration" is not set'
            assert len(phase_duration) == 5, 'Pacman: "phase_duration" must a list with 5 elements'
            assert phase_value, 'Pacman: "phase_value" is not set'
            assert len(phase_value) == 2, 'Pacman: "phase_value" must a list with 2 elements'
            self.ramp_low_phase_1 = phase_duration[0]
            self.ramp_up_phase = phase_duration[1]
            self.ramp_high_phase = phase_duration[2]
            self.ramp_down_phase = phase_duration[3]
            self.ramp_low_phase_2 = phase_duration[4]
            self.ramp_low_value = phase_value[0]
            self.ramp_high_value = phase_value[1]
        elif self.item_generator == 'random':
            # design filter
            if isinstance(self.frequency, float) or isinstance(self.frequency, int):
                self.sos = signal.butter(self.filter_order, self.frequency, 'lowpass', fs=self.item_generation_frequency, output='sos')
            elif isinstance(self.frequency, list) and len(self.frequency) == 2:
                self.sos = signal.butter(self.filter_order, self.frequency, 'bandpass', fs=self.item_generation_frequency, output='sos')
            else:
                raise Exception('frequency must be a scalar (lowpass) or a list with two elements (bandpass)')
            # initialize filter state for step response steady-state
            self.z = signal.sosfilt_zi(self.sos) # [sections x 2]
        else:
            raise Exception('unkown generator')

        lsl_info = pylsl.StreamInfo('pacman', 'state', 4, pymonctl.getPrimary().frequency, 'float32', 'pacman_state')
        self.lsl_state_outlet = pylsl.StreamOutlet(lsl_info)

        super().__init__(node, pos_x, pos_y, depth, 1, 1, 0)

    def activate(self):
        super().activate()
        self.highscore_counter = 0

    def start(self):
        self.generate_items = True
        self.initial_time = None
        self.last_update_time = 0
        self.last_item_generation_time = -math.inf
        self.highscore_counter = 0

    def stop(self):
        self.generate_items = False
        self.initial_time = None
        self.last_update_time = 0
        self.last_item_generation_time = -math.inf
        # [item_node.removeNode() for item_node in self.items]
        # self.items = []

    def updateState(self, time):
        # get time since first method call
        if not self.initial_time:
            self.initial_time = time
        elapsed_time = time - self.initial_time

        # get time since last method call
        time_delta = elapsed_time - self.last_update_time
        self.last_update_time = elapsed_time

        # time: absolute time (for LSL)
        # elapsed_time: time since call of "start" (for item generator)
        # time_delta: time since last call of "updateState" (for position updates)

        if self.active:
            # snake update
            for item_node in self.items:
                new_x = item_node.getX() - time_delta*self.item_speed
                item_node.setX(new_x)

            # hide items which got hit by Pacman
            # important: we don't remove them as otherwise the distance calculation between Pacman and the next item may be affected
            for item_node in self.items:
                if item_node.isHidden() == False: # TODO: undo hack
                    if (item_node.getPos() - self.pacman.getPos()).length() < self.hit_distance_threshold:
                    # if item_node.getDistance(self.pacman) < self.hit_distance_threshold:
                        item_node.hide()
                        self.highscore_counter += 1

            # remove items which are beyond the left limit
            while(self.items and self.items[0].getX() < self.items_left_limit):
                item_node = self.items.pop(0)
                item_node.removeNode()

            # check if a new item has to be created
            if self.generate_items and elapsed_time - self.last_item_generation_time >= 1/self.item_generation_frequency:
                self.last_item_generation_time = elapsed_time
                pos_y = self.getNextPosition(elapsed_time)
                if pos_y is None:
                    # generator is finished
                    self.generate_items = False
                    return Pacman.GENERATION_FINISHED
                item_node = self.item_template.copyTo(self.node)
                item_node.show()
                item_node.setPos(self.items_right_limit, 0, pos_y)
                self.items.append(item_node)

            # pacman update from LSL input
            assert self.lsl_state_control_streams and len(self.lsl_state_control_streams) in [1, 2], 'Pacman: one or two state control streams must be specified'
            pacman_y_pos = 0
            neg_feedback = 0

            pacman_pos_samples = self.lsl_streams_samples[self.lsl_state_control_streams[0]]
            neg_feedback_samples = self.lsl_streams_samples[self.lsl_state_control_streams[-1]] # accesses the first or, if available, the second stream

            # update vertical Pacman position
            pacman_y_pos = pacman_pos_samples.item(self.state_control_channels[0])
            pacman_y_pos = np.clip(pacman_y_pos, -1.0, 1.0)
            self.pacman.setZ(pacman_y_pos)

            if self.neg_feedback_type:
                assert len(self.state_control_channels) == 2, 'Pacman: "channels" must have exactly two elements'
                neg_feedback = neg_feedback_samples[self.state_control_channels[1]]
                if self.neg_feedback_type == 'color':
                    # update color
                    neg_feedback = np.clip(neg_feedback, 0, 1.0)
                    new_color = (1 - neg_feedback)*np.array(self.pacman_color) + neg_feedback*np.array(self.pacman_neg_feedback_color)
                    self.pacman.setColor(LColor(tuple(new_color), w=255)/255)
                    # neg_feedback = np.clip(neg_feedback, 0, 0.7)
                    # self.pacman.setAlphaScale(1 - neg_feedback) # 0...transparent, 1...opaque
                    # new_pacman_size = self.pacman_size*(1 - neg_feedback)
                    # self.pacman.setScale(new_pacman_size, 1, new_pacman_size)
                elif self.neg_feedback_type == 'pos':
                    # update x-position
                    neg_feedback = np.clip(neg_feedback, -1.0, 1.0)
                    new_x_pos = self.pacman_x_pos + neg_feedback*self.gradient_max_displacement
                    self.pacman.setX(new_x_pos)
                else:
                    raise Exception('unkown negative feedback type')
            else:
                # nothing to do
                assert len(self.state_control_channels) == 1, 'Pacman: "channels" must have exactly one element'

            # highscore update
            if self.highscore:
                self.highscore_node.setText(str(self.highscore_counter))

            # find position of next closest item to Pacman (we can assume that items are sorted)
            item_pos = 0
            for item_node in self.items:
                if item_node.getX() >= self.pacman_x_pos:
                    item_pos = item_node.getZ()
                    break

            # send Pacman state via LSL
            self.lsl_state_outlet.push_sample([pacman_y_pos, neg_feedback, item_pos, self.highscore_counter], time, pushthrough=True)

        return InterfaceObject.NO_SIGNAL

    def getNextPosition(self, time):

        if self.item_generator == 'constant':
            pos_y = self.amplitude

        elif self.item_generator == 'sinus':
            pos_y = self.amplitude*math.sin(2*math.pi*self.frequency*time)

        elif self.item_generator == 'chirp':
            pos_y = self.amplitude*signal.chirp(time, self.frequency[0], self.phase_duration, self.frequency[1])

        elif self.item_generator == 'ramp':
            # end
            if time >= self.ramp_low_phase_1 + self.ramp_up_phase + self.ramp_high_phase + self.ramp_down_phase + self.ramp_low_phase_2:
                pos_y = None
            # low phase 2
            elif time >= self.ramp_low_phase_1 + self.ramp_up_phase + self.ramp_high_phase + self.ramp_down_phase:
                pos_y = self.ramp_low_value
            # ramp-down phase
            elif time >= self.ramp_low_phase_1 + self.ramp_up_phase + self.ramp_high_phase:
                phase_progress = (time - self.ramp_low_phase_1 - self.ramp_up_phase - self.ramp_high_phase)/self.ramp_down_phase # 0 -> 1
                pos_y = self.ramp_low_value + (self.ramp_high_value - self.ramp_low_value) * (1 - phase_progress)
            # hold phase
            elif time >= self.ramp_low_phase_1 + self.ramp_up_phase:
                pos_y = self.ramp_high_value
            # ramp-up phase
            elif time >= self.ramp_low_phase_1:
                phase_progress = (time - self.ramp_low_phase_1)/self.ramp_up_phase # 0 -> 1
                pos_y = self.ramp_low_value + (self.ramp_high_value - self.ramp_low_value) * phase_progress
            # low phase 1
            elif time >= 0:
                pos_y = self.ramp_low_value

        elif self.item_generator == 'random':
            # generate band-pass filtered Gaussian noise limited by tanh
            noise_signal = np.random.normal(0, self.noise_stddev, 1)
            pos_y, self.z = signal.sosfilt(self.sos, noise_signal, zi=self.z)
            pos_y = self.amplitude*np.tanh(pos_y)

        else:
            raise Exception('unkown generator')

        return pos_y
