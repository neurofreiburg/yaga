import numpy as np
import math
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import LColor, LVecBase3f, TransparencyAttrib
from panda3d.core import TextNode, TextFont

from yaga_modules.interface_objects import InterfaceObject
from yaga_modules.colormaps import StdColorMap


IMG_RESOURCES_DIR = 'resources/images'
FONT_RESOURCES_DIR = 'resources/fonts'


class GraphicObject2D(InterfaceObject):

    def __init__(self, node, pos_x, pos_y, depth, scale_x, scale_y, angle, color=None):
        super().__init__()

        self.node = node
        self.lsl_pos_control_streams = None
        self.lsl_scale_control_streams = None
        self.lsl_color_control_stream = None # only one stream is possible
        self.lsl_state_control_streams = None

        self.pos_control_channels = None   # 2 channels
        self.scale_control_channels = None # 2 channels
        self.color_control_channel = None  # 1 channels
        self.state_control_channels = None # 1 or more channels

        self.updatePos(pos_x, pos_y, depth)
        self.updateScale(scale_x, scale_y)
        self.updateRot(angle)
        if color:
            self.updateColor(color)
        self.deactivate()

    def activate(self):
        super().activate()
        self.node.show()

    def deactivate(self):
        super().deactivate()
        self.node.hide()

    def updatePos(self, pos_x, pos_y, depth=None):
        self.node.setPos(pos_x, 0, pos_y)
        if depth:
            self.node.setBin('fixed', -depth)

    def updateScale(self, scale_x, scale_y):
        self.node.setScale(scale_x, 1, scale_y)

    def updateRot(self, angle):
        self.node.setHpr(0, 0, angle)

    def updateColor(self, color):
        if isinstance(color, str):
            color_tuple = StdColorMap[color]
        else:
            color_tuple = color
        color_tuple = LColor(color_tuple, w=255) / 255
        self.node.setColor(color_tuple)
        self.node.setTransparency(TransparencyAttrib.MAlpha)

    def controlPosWithLSLStream(self, lsl_stream_name, channels=[0,1], aggregation_mode='last'):
        assert isinstance(lsl_stream_name, str), '"lsl_stream_name" must be a string'
        assert isinstance(channels, list) and len(channels) == 2, '"channels" must have 2 elements'
        self.connectToLSLStreams([lsl_stream_name], aggregation_mode)
        self.lsl_pos_control_streams = [lsl_stream_name]
        self.pos_control_channels = channels

    def controlPosWithLSLStreams(self, lsl_stream_names, channels=[0,1], aggregation_mode='last'):
        assert isinstance(lsl_stream_names, list) and len(lsl_stream_names) == 2, '"lsl_stream_names" must have 2 elements'
        assert isinstance(channels, list) and len(channels) == 2, '"channels" must have 2 elements'
        self.connectToLSLStreams(lsl_stream_names, aggregation_mode)
        self.lsl_pos_control_streams = lsl_stream_names
        self.pos_control_channels = channels

    def controlScaleWithLSLStream(self, lsl_stream_name, channels=[0,1], aggregation_mode='last'):
        assert isinstance(lsl_stream_name, str), '"lsl_stream_name" must be a string'
        assert isinstance(channels, list) and len(channels) == 2, '"channels" must have 2 elements'
        self.connectToLSLStreams([lsl_stream_name], aggregation_mode)
        self.lsl_scale_control_streams = [lsl_stream_name]
        self.scale_control_channels = channels

    def controlScaleWithLSLStreams(self, lsl_stream_names, channels=[0,1], aggregation_mode='last'):
        assert isinstance(lsl_stream_names, list) and len(lsl_stream_names) == 2, '"lsl_stream_names" must have 2 elements'
        assert isinstance(channels, list) and len(channels) == 2, '"channels" must have 2 elements'
        self.connectToLSLStreams(lsl_stream_names, aggregation_mode)
        self.lsl_scale_control_streams = lsl_stream_names
        self.scale_control_channels = channels

    def controlColorWithLSLStream(self, lsl_stream_name, channel=0, aggregation_mode='last', neg_color='blue', pos_color='red', neutral_color='white'):
        assert isinstance(lsl_stream_name, str), '"lsl_stream_name" must be a string'
        assert isinstance(channel, int), '"channel" must be an integer'
        self.connectToLSLStreams([lsl_stream_name], aggregation_mode)
        self.lsl_color_control_stream = lsl_stream_name
        self.color_control_channel = channel
        self.neg_color = LVecBase3f(StdColorMap[neg_color])
        self.pos_color = LVecBase3f(StdColorMap[pos_color])
        self.neutral_color = LVecBase3f(StdColorMap[neutral_color])

    def controlStateWithLSLStream(self, lsl_stream_name, channels, aggregation_mode='last'):
        assert isinstance(lsl_stream_name, str), '"lsl_stream_name" must be a string'
        assert isinstance(channels, list), '"channels" must be a list'
        self.connectToLSLStreams([lsl_stream_name], aggregation_mode)
        self.lsl_state_control_streams = [lsl_stream_name]
        self.state_control_channels = channels

    def controlStateWithLSLStreams(self, lsl_stream_names, channels, aggregation_mode='last'):
        assert isinstance(lsl_stream_names, list), '"lsl_stream_names" must be a list'
        assert isinstance(channels, list), '"channels" must be a list'
        self.connectToLSLStreams(lsl_stream_names, aggregation_mode)
        self.lsl_state_control_streams = lsl_stream_names
        self.state_control_channels = channels

    def _newLSLSampleReceived(self):
        # apply update methods only when object is active
        if self.active and self.lsl_streams_samples:
            # updates happen with the screen refresh rate (e.g. 60 Hz)
            # pos and scale update support reading from one or two LSL streams; the state update can support multiple LSL streams depending on the concrete implementation of updateState
            if self.lsl_pos_control_streams:
                stream_x = self.lsl_streams_samples[self.lsl_pos_control_streams[0]]
                stream_y = self.lsl_streams_samples[self.lsl_pos_control_streams[-1]] # access the last element to support one or two control streams
                self.updatePos(stream_x[self.pos_control_channels[0]], stream_y[self.pos_control_channels[1]])
            if self.lsl_scale_control_streams:
                stream_x = self.lsl_streams_samples[self.lsl_scale_control_streams[0]]
                stream_y = self.lsl_streams_samples[self.lsl_scale_control_streams[-1]] # access the last element to support one or two control streams
                self.updateScale(stream_x[self.scale_control_channels[0]], stream_y[self.scale_control_channels[1]])
            if self.lsl_color_control_stream:
                val = self.lsl_streams_samples[self.lsl_color_control_stream][self.color_control_channel]
                # when value is between [-1, 0) interpolate between negative and neutral color; when value is between [0, 1] interpolate between neutral and positive color
                if val < 0:
                    color = self.neg_color*(-val) + self.neutral_color*(1+val) # attention: color must be LVecBase3f and order is important
                else:
                    color = self.pos_color*val + self.neutral_color*(1-val) # attention: color must be LVecBase3f and order is important
                self.updateColor(color)

            # lsl_state_control_streams: nothing to do here; the "updateState" method is called by the task manager and handles state updates


class Image(GraphicObject2D):

    def __init__(self, file, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0):
        node = aspect2d.attachNewNode('image')
        image = OnscreenImage(image=IMG_RESOURCES_DIR + '/' + file, parent=node)
        image.setTransparency(TransparencyAttrib.MAlpha)
        if scale_x and not scale_y:
            scale_y = scale_x*image.getTexture().getOrigFileYSize()/image.getTexture().getOrigFileXSize()
            print('scale x = %f\tscale y = %f\n' % (scale_x, scale_y))
        if scale_y and not scale_x:
            scale_x = scale_y*image.getTexture().getOrigFileXSize()/image.getTexture().getOrigFileYSize()
        super().__init__(image, pos_x, pos_y, depth, scale_x, scale_y, angle, None)


class Ball(GraphicObject2D):

    def __init__(self, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, color='white'):
        node = aspect2d.attachNewNode('ball')
        ball = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
        super().__init__(ball, pos_x, pos_y, depth, scale_x, scale_y, 0, color)


class Box(GraphicObject2D):

    def __init__(self, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0, color='white'):
        node = aspect2d.attachNewNode('box')
        box = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        super().__init__(box, pos_x, pos_y, depth, scale_x, scale_y, angle, color)


class Bar(GraphicObject2D):

    def __init__(self, pos_x=0, pos_y=0, depth=0, bar_width=0.1, bar_height=0.8, frame_width=0.01, target_width=0.2, target_height=0.01, bar_color='lime', frame_color='black', target_color='red', low_value=0.0, high_value=1.0, target_value=None, target_online_control=False):

        node = aspect2d.attachNewNode('bar')

        self.bar_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        self.frame_top_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        self.frame_bottom_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        self.frame_left_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        self.frame_right_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
        self.target_node = None
        self.target_online_control = target_online_control

        self.low_value = low_value
        self.high_value = high_value
        self.bar_width = bar_width
        self.bar_height = bar_height
        bar_scale_x = self.bar_width/2
        bar_scale_y = self.bar_height/2

        # bar
        self.bar_node.setScale(bar_scale_x, 1, bar_scale_y)
        self.bar_node.setPos(0, 0, bar_scale_y)
        self.frame_bottom_node.setScale(bar_scale_x + frame_width, 1, frame_width/2)
        self.frame_bottom_node.setPos(0, 0, -frame_width/2)
        self.frame_top_node.setScale(bar_scale_x + frame_width, 1, frame_width/2)
        self.frame_top_node.setPos(0, 0, bar_height + frame_width/2)
        self.frame_left_node.setScale(frame_width/2, 1, bar_scale_y)
        self.frame_left_node.setPos(-bar_scale_x - frame_width/2, 0, bar_scale_y)
        self.frame_right_node.setScale(frame_width/2, 1, bar_scale_y)
        self.frame_right_node.setPos(bar_scale_x + frame_width/2, 0, bar_scale_y)
        if isinstance(frame_color, str):
            frame_color_tuple = StdColorMap[frame_color]
        else:
            frame_color_tuple = frame_color
        frame_color_tuple = LColor(frame_color_tuple, w=255) / 255
        self.frame_bottom_node.setColor(frame_color_tuple)
        self.frame_top_node.setColor(frame_color_tuple)
        self.frame_left_node.setColor(frame_color_tuple)
        self.frame_right_node.setColor(frame_color_tuple)

        # target
        if target_value is not None:
            self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=node)
            self.target_node.setScale(target_width/2, 1, target_height/2)
            if isinstance(target_color, str):
                target_color_tuple = StdColorMap[target_color]
            else:
                target_color_tuple = target_color
            target_color_tuple = LColor(target_color_tuple, w=255) / 255
            self.target_node.setColor(target_color_tuple)
            self.updateTargetValue(target_value)

        super().__init__(node, pos_x, pos_y, depth, 1, 1, 0, bar_color)

    def updateTargetValue(self, target_value):
        assert self.target_node, 'Bar: an intial target value must be specified'
        target_y_pos = self.bar_height * (target_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)

    def updateTargetValueFromLSLStream(self):
        assert self.target_node, 'Bar: an intial target value must be specified'
        assert len(self.state_control_channels) == 2, 'Bar: "channels" must have two elements: first channel = feedback value, second channel = target value'
        target_value = self.lsl_streams_samples[self.lsl_state_control_streams[-1]][self.state_control_channels[1]]
        target_y_pos = self.bar_height * (target_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)

    def updateState(self, time):
        if self.active and self.lsl_state_control_streams:
            assert len(self.lsl_state_control_streams) == 1 or len(self.lsl_state_control_streams) == 2, 'Bar: one or two state control streams must be specified'
            assert len(self.state_control_channels) == 1 or len(self.state_control_channels) == 2, 'Bar: "channels" must have one or two elements: first channel = feedback value; second channel = target value (optional)'

            if self.target_online_control:
                assert self.target_node, 'Bar: an intial target value must be specified'
                assert len(self.state_control_channels) == 2, 'Bar: "channels" must have two elements: first channel = feedback, second channel = target position'

                target_value = self.lsl_streams_samples[self.lsl_state_control_streams[-1]][self.state_control_channels[1]]
                target_y_pos = self.bar_height * (target_value - self.low_value) / (self.high_value - self.low_value)
                self.target_node.setPos(0, 0, target_y_pos)

            feedback_sample = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[0]]
            bar_relative_height = (np.clip(feedback_sample, self.low_value, self.high_value) - self.low_value) / (self.high_value - self.low_value) # transform values to [0, 1]
            bar_current_height = self.bar_height*bar_relative_height
            self.bar_node.setScale(self.bar_width/2, 1, bar_current_height/2)
            self.bar_node.setZ(bar_current_height/2)

        return InterfaceObject.NO_SIGNAL


class BarWithRampTarget(Bar):
    BAR_FINISHED = 'bar_finished'

    def __init__(self, pos_x=0, pos_y=0, depth=0, bar_width=0.1, bar_height=0.8, frame_width=0.01, target_width=0.2, target_height=0.01, bar_color='lime', frame_color='black', target_color='red', target_info_color='black',
                 pre_phase_duration=3, ramp_up_phase_duration=10, hold_phase_duration=20, ramp_down_phase_duration=10, post_phase_duration=3, low_value=0.0, high_value=1.0, start_value=0.0, ramp_value=0.3):
        super().__init__(pos_x, pos_y, depth, bar_width, bar_height, frame_width, target_width, target_height, bar_color, frame_color, target_color, low_value, high_value)
        self.animate = False
        self.start_time = None

        self.pre_phase_duration = pre_phase_duration
        self.ramp_up_phase_duration = ramp_up_phase_duration
        self.hold_phase_duration = hold_phase_duration
        self.ramp_down_phase_duration = ramp_down_phase_duration
        self.post_phase_duration = post_phase_duration

        self.start_value = start_value
        self.ramp_value = ramp_value

        # ramp target
        if ramp_value != high_value:
            self.hold_target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=self.node)
            self.hold_target_node.setScale(target_width/2, 1, frame_width/2)
            hold_target_y_pos = self.bar_height * (ramp_value - self.low_value) / (self.high_value - self.low_value)
            self.hold_target_node.setPos(0, 0, hold_target_y_pos)
            if isinstance(target_info_color, str):
                hold_target_color_tuple = StdColorMap[target_info_color]
            else:
                hold_target_color_tuple = target_info_color
            hold_target_color_tuple = LColor(hold_target_color_tuple, w=255) / 255
            self.hold_target_node.setColor(hold_target_color_tuple)

        # current target
        self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=self.node)
        self.target_node.setScale(target_width/2, 1, target_height/2)
        target_y_pos = self.bar_height * (start_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)
        if isinstance(target_color, str):
            target_color_tuple = StdColorMap[target_color]
        else:
            target_color_tuple = target_color
        target_color_tuple = LColor(target_color_tuple, w=255) / 255
        self.target_node.setColor(target_color_tuple)

    def startAnimation(self):
        self.animate = True
        self.start_time = None

    def stopAnimation(self):
        self.animate = False
        self.start_time = None

    def updateState(self, time):
        # update actual value
        super().updateState(time)

        # update target value
        if self.active and self.animate:

            # get animation time
            if not self.start_time:
                self.start_time = time
            elapsed_time = time - self.start_time

            if elapsed_time < self.pre_phase_duration:
                # pre phase
                target_rel_value = 0
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration:
                # ramp up phase
                target_rel_value = (elapsed_time - self.pre_phase_duration)/self.ramp_up_phase_duration
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration:
                # hold phase
                target_rel_value = 1
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration + self.ramp_down_phase_duration:
                # ramp down phase
                target_rel_value = 1 - (elapsed_time - self.pre_phase_duration - self.ramp_up_phase_duration - self.hold_phase_duration)/self.ramp_down_phase_duration
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration + self.ramp_down_phase_duration + self.post_phase_duration:
                # post phase
                target_rel_value = 0
            else:
                self.animate = False
                return BarWithRampTarget.BAR_FINISHED

            # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
            target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value

            # transform bar value into screen coordinates
            target_y_pos = self.bar_height * (target_abs_value - self.low_value) / (self.high_value - self.low_value)

            self.target_node.setPos(0, 0, target_y_pos)

        return InterfaceObject.NO_SIGNAL


class BarWithSinusTarget(Bar):
    BAR_FINISHED = 'bar_finished'

    def __init__(self, pos_x=0, pos_y=0, depth=0, bar_width=0.1, bar_height=0.8, frame_width=0.01, target_width=0.2, target_height=0.01, bar_color='lime', frame_color='black', target_color='red', target_info_color='black',
                 pre_phase_duration=3, ramp_up_phase_duration=10, sinus_phase_duration=20, sinus_frequency=1, sinus_amplitude=0.1, ramp_down_phase_duration=10, post_phase_duration=3, low_value=0.0, high_value=1.0, start_value=0.0, ramp_value=0.3):
        super().__init__(pos_x, pos_y, depth, bar_width, bar_height, frame_width, target_width, target_height, bar_color, frame_color, target_color, low_value, high_value)
        self.animate = False
        self.start_time = None

        self.pre_phase_duration = pre_phase_duration
        self.ramp_up_phase_duration = ramp_up_phase_duration
        self.sinus_phase_duration = sinus_phase_duration
        self.ramp_down_phase_duration = ramp_down_phase_duration
        self.post_phase_duration = post_phase_duration

        self.sinus_frequency = sinus_frequency
        self.sinus_amplitude = sinus_amplitude

        self.start_value = start_value
        self.ramp_value = ramp_value

        # ramp target
        if ramp_value != high_value:
            self.hold_target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=self.node)
            self.hold_target_node.setScale(target_width/2, 1, frame_width/2)
            hold_target_y_pos = self.bar_height * (ramp_value - self.low_value) / (self.high_value - self.low_value)
            self.hold_target_node.setPos(0, 0, hold_target_y_pos)
            if isinstance(target_info_color, str):
                hold_target_color_tuple = StdColorMap[target_info_color]
            else:
                hold_target_color_tuple = target_info_color
            hold_target_color_tuple = LColor(hold_target_color_tuple, w=255) / 255
            self.hold_target_node.setColor(hold_target_color_tuple)

        # current target
        self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=self.node)
        self.target_node.setScale(target_width/2, 1, target_height/2)
        target_y_pos = self.bar_height * (start_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)
        if isinstance(target_color, str):
            target_color_tuple = StdColorMap[target_color]
        else:
            target_color_tuple = target_color
        target_color_tuple = LColor(target_color_tuple, w=255) / 255
        self.target_node.setColor(target_color_tuple)

    def startAnimation(self):
        self.animate = True
        self.start_time = None
        self.sinus_time = None

    def stopAnimation(self):
        self.animate = False
        self.start_time = None
        self.sinus_time = None

    def updateState(self, time):
        # update actual value
        super().updateState(time)

        # update target value
        if self.active and self.animate:

            # get animation time
            if not self.start_time:
                self.start_time = time
            elapsed_time = time - self.start_time

            if elapsed_time < self.pre_phase_duration:
                # pre phase
                target_abs_value = self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration:
                # ramp up phase
                target_rel_value = (elapsed_time - self.pre_phase_duration)/self.ramp_up_phase_duration
                # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
                target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration:
                # sinus phase
                if not self.sinus_time:
                    self.sinus_time = time
                elapsed_sinus_time = time - self.sinus_time

                sin = self.sinus_amplitude*math.sin(2*math.pi*self.sinus_frequency*elapsed_sinus_time)
                target_abs_value = sin + self.ramp_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration + self.ramp_down_phase_duration:
                # ramp down phase
                target_rel_value = 1 - (elapsed_time - self.pre_phase_duration - self.ramp_up_phase_duration - self.sinus_phase_duration)/self.ramp_down_phase_duration
                # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
                target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration + self.ramp_down_phase_duration + self.post_phase_duration:
                # post phase
                target_abs_value = self.start_value
            else:
                self.animate = False
                return BarWithSinusTarget.BAR_FINISHED

            # transform bar value into screen coordinates
            target_y_pos = self.bar_height * (target_abs_value - self.low_value) / (self.high_value - self.low_value)

            self.target_node.setPos(0, 0, target_y_pos)

        return InterfaceObject.NO_SIGNAL


class Cross(GraphicObject2D):

    def __init__(self, line_width=0.05, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0, color='white'):
        cross_node = aspect2d.attachNewNode('cross')
        horizontal_bar_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', scale=(line_width, 1, 1), parent=cross_node)
        vertical_bar_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', scale=(1, 1, line_width), parent=cross_node)
        super().__init__(cross_node, pos_x, pos_y, depth, scale_x, scale_y, angle, color)


class Text(GraphicObject2D):

    def __init__(self, text, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0, color='black', background_color=None, frame_color=None):
        font = loader.loadFont(FONT_RESOURCES_DIR + '/FreeSans.ttf')
        font.setPixelsPerUnit(256)
        node = aspect2d.attachNewNode('text')
        text = OnscreenText(text, mayChange=True, font=font, parent=node)
        text.setAlign(TextNode.ACenter)
        super().__init__(text, pos_x, pos_y, depth, scale_x, scale_y, angle, color)
        if background_color:
            self.updateBackgroundColor(background_color)
        if frame_color:
            self.updateFrameColor(frame_color)

    def updatePos(self, pos_x, pos_y, depth=0):
        self.node.setPos(pos_x, pos_y)
        self.node.setBin('fixed', -depth)

    def updateScale(self, scale_x, scale_y):
        self.node.setScale(scale_x, scale_y)

    def updateColor(self, color):
        if isinstance(color, str):
            color_tuple = StdColorMap[color]
        else:
            color_tuple = color
        color_tuple = LColor(color_tuple, w=255) / 255
        self.node.setFg(color_tuple)

    def updateBackgroundColor(self, color):
        if isinstance(color, str):
            color_tuple = StdColorMap[color]
        else:
            color_tuple = color
        color_tuple = LColor(color_tuple, w=255) / 255
        self.node.setBg(color_tuple)

    def updateFrameColor(self, color):
        if isinstance(color, str):
            color_tuple = StdColorMap[color]
        else:
            color_tuple = color
        color_tuple = LColor(color_tuple, w=255) / 255
        self.node.setFrame(color_tuple)

    def updateText(self, text):
        self.node.setText(text)

    def updateState(self, time):
        if self.active and self.lsl_state_control_streams:
            assert len(self.lsl_state_control_streams) == 1, 'Text: exactly one state control stream must be specified'
            assert len(self.state_control_channels) == 1, 'Text: "channels" must have exactly one element'

            sample = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[0]]
            self.updateText(str(sample.round()))


class RandomNumber(Text):
    def __init__(self, interval, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0, color='black', background_color=None, frame_color=None):
        self.rand_interval = interval
        self.rand_number = np.nan
        super().__init__('', pos_x, pos_y, depth, scale_x, scale_y, angle, color, background_color, frame_color)

    def activate(self):
        super().activate()
        self.rand_number = np.random.default_rng().integers(self.rand_interval[0], self.rand_interval[1], endpoint=True)
        self.node.setText(str(self.rand_number))


class Countdown(Text):
    COUNTDOWN_FINISHED = 'countdown_finished'

    def __init__(self, counter_start=10, counter_stop=1, counter_interval=1, pos_x=0, pos_y=0, depth=0, scale_x=1, scale_y=1, angle=0, color='black', background_color=None, frame_color=None):
        self.counter_start = counter_start
        self.counter_stop = counter_stop
        self.counter_interval = counter_interval
        super().__init__(str(counter_start), pos_x, pos_y, depth, scale_x,
              scale_y, angle, color, background_color, frame_color)

    def activate(self):
        super().activate()
        self.current_counter = None
        self.start_time = None

    def deactivate(self):
        super().deactivate()
        self.current_counter = None
        self.start_time = None

    def updateState(self, time):

        if self.active:
            # caluclate current counter state
            if self.start_time:
                elapsed_time = time - self.start_time
                calculated_counter = self.counter_start - int(elapsed_time/self.counter_interval)
            else:
                # initialize counter
                self.start_time = time
                calculated_counter = self.counter_start

            # check if counter has to be stopped or updated
            if calculated_counter < self.counter_stop:
                # stop counter
                self.deactivate()
                return Countdown.COUNTDOWN_FINISHED
            elif self.current_counter != calculated_counter:
                # update counter
                self.current_counter = calculated_counter
                self.updateText(str(self.current_counter))

        return InterfaceObject.NO_SIGNAL


class Arrow(GraphicObject2D):

    def __init__(self, pos_x=0, pos_y=0, depth=0, angle=0, arrow_length=0.5, line_width=0.02, head_size=0.1, target_size=0.1, arrow_color='lime', target_color='white', low_value=0, high_value=0.2, target_value=None, target_online_control=False):

        node = aspect2d.attachNewNode('arrow')

        self.arrow_node = node.attachNewNode('arrow_handle')
        self.line_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/box_128x128.png', parent=self.arrow_node)
        self.head_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/triangle_128x128.png', parent=self.arrow_node)
        self.target_node = None
        self.target_online_control = target_online_control

        self.angle = angle
        self.low_value = low_value
        self.high_value = high_value
        self.arrow_length = arrow_length
        self.head_size = head_size
        self.line_width = line_width
        line_height = arrow_length - head_size

        # arrow
        self.line_node.setScale(line_width/2, 1, line_height/2)
        self.line_node.setPos(0, 0, line_height/2)
        self.head_node.setScale(head_size/2, 1, head_size/2)
        self.head_node.setPos(0, 0, line_height + head_size/2)
        if isinstance(arrow_color, str):
            color_tuple = StdColorMap[arrow_color]
        else:
            color_tuple = arrow_color
        color_tuple = LColor(color_tuple, w=255) / 255
        self.line_node.setColor(color_tuple)
        self.head_node.setColor(color_tuple)

        # target
        if target_value is not None:
            self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
            self.target_node.setScale(target_size/2, 1, target_size/2)
            if isinstance(target_color, str):
                target_color_tuple = StdColorMap[target_color]
            else:
                target_color_tuple = target_color
            target_color_tuple = LColor(target_color_tuple, w=255) / 255
            self.target_node.setColor(target_color_tuple)
            self.target_node.setBin('fixed', -depth - 1)
            self.updateTargetValue(target_value)

        super().__init__(node, pos_x, pos_y, depth, 1, 1, 0, arrow_color)

    def updateTargetValue(self, target_value):
        assert self.target_node, 'Arrow: an intial target value must be specified'
        target_y_pos = self.arrow_length * (target_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)

    def updateTargetValueFromLSLStream(self):
        assert self.target_node, 'Arrow: an intial target value must be specified'
        assert len(self.state_control_channels) == 3, 'Arrow: "channels" must have three elements: channel 1 = x-feedback, channel 2 = y-feedback, channel 3 = target y position'
        target_value = self.lsl_streams_samples[self.lsl_state_control_streams[-1]][self.state_control_channels[2]]
        target_y_pos = self.arrow_length * (target_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)

    def updateState(self, time):

        if self.active and self.lsl_state_control_streams:
            assert len(self.lsl_state_control_streams) == 1 or len(self.lsl_state_control_streams) == 2, 'Arrow: one or two state control streams must be specified'
            assert len(self.state_control_channels) == 2 or len(self.state_control_channels) == 3, 'Arrow: "channels" must have two or three elements: channel 1/2 = feedback x/y; channel 3 = target position (optional)'

            if self.target_online_control:
                assert self.target_node, 'Arrow: an intial target value must be specified'
                assert len(self.state_control_channels) == 3, 'Arrow: "channels" must have three elements: channel 1 = x-feedback, channel 2 = y-feedback, channel 3 = target y position'
                target_value = self.lsl_streams_samples[self.lsl_state_control_streams[-1]][self.state_control_channels[2]]
                target_y_pos = self.arrow_length * (target_value - self.low_value) / (self.high_value - self.low_value)
                self.target_node.setPos(0, 0, target_y_pos)

            feedback_x = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[0]] # first channel points to the right
            feedback_y = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[1]] # second channel points upwards

            arrow_abs_value = np.sqrt(feedback_x**2 + feedback_y**2)
            arrow_angle = np.arctan2(feedback_y, feedback_x)*180.0/np.pi

            # convert the arrow's absolute value into the corresponding arrow length on the screen
            relative_arrow_length = (np.clip(arrow_abs_value, self.low_value, self.high_value) - self.low_value) / (self.high_value - self.low_value) # limit absolute value to [0, 1]
            absolute_arrow_length = self.arrow_length*relative_arrow_length

            line_height = np.maximum(absolute_arrow_length - self.head_size, 0)

            self.line_node.setScale(self.line_width/2, 1, line_height/2)
            self.line_node.setZ(line_height/2)
            self.head_node.setZ(line_height + self.head_size/2)
            self.arrow_node.setHpr(0, 0, self.angle + arrow_angle)

        return InterfaceObject.NO_SIGNAL


class ArrowWithRampTarget(Arrow):
    ARROW_FINISHED = 'arrow_finished'

    def __init__(self, pos_x=0, pos_y=0, depth=0, angle=0, arrow_length=0.5, line_width=0.02, head_size=0.1, target_size=0.1, target_info_size=0.1, arrow_color='lime', target_color='red', target_info_color='white',
                 pre_phase_duration=3, ramp_up_phase_duration=10, hold_phase_duration=20, ramp_down_phase_duration=10, post_phase_duration=3, low_value=0, high_value=0.2, start_value=0, ramp_value=0.2):
        super().__init__(pos_x, pos_y, depth, angle, arrow_length, line_width, head_size, target_size, arrow_color, target_color, low_value, high_value)
        self.animate = False
        self.start_time = None

        self.pre_phase_duration = pre_phase_duration
        self.ramp_up_phase_duration = ramp_up_phase_duration
        self.hold_phase_duration = hold_phase_duration
        self.ramp_down_phase_duration = ramp_down_phase_duration
        self.post_phase_duration = post_phase_duration

        self.start_value = start_value
        self.ramp_value = ramp_value

        # hold target
        self.hold_target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=self.node)
        self.hold_target_node.setScale(target_info_size/2, 1, target_info_size/2)
        hold_target_y_pos = self.arrow_length * (ramp_value - self.low_value) / (self.high_value - self.low_value)
        self.hold_target_node.setPos(0, 0, hold_target_y_pos)
        if isinstance(target_info_color, str):
            hold_target_color_tuple = StdColorMap[target_info_color]
        else:
            hold_target_color_tuple = target_info_color
        hold_target_color_tuple = LColor(hold_target_color_tuple, w=255) / 255
        self.hold_target_node.setColor(hold_target_color_tuple)
        self.hold_target_node.setBin('fixed', -depth - 1)

        # current target
        self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=self.node)
        self.target_node.setScale(target_size/2, 1, target_size/2)
        target_y_pos = self.arrow_length * (start_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)
        if isinstance(target_color, str):
            target_color_tuple = StdColorMap[target_color]
        else:
            target_color_tuple = target_color
        target_color_tuple = LColor(target_color_tuple, w=255) / 255
        self.target_node.setColor(target_color_tuple)
        self.target_node.setBin('fixed', -depth - 1)

    def startAnimation(self):
        self.animate = True
        self.start_time = None

    def stopAnimation(self):
        self.animate = False
        self.start_time = None

    def updateState(self, time):
        # update actual value
        super().updateState(time)

        # update target value
        if self.active and self.animate:

            # get animation time
            if not self.start_time:
                self.start_time = time
            elapsed_time = time - self.start_time

            if elapsed_time < self.pre_phase_duration:
                # pre phase
                target_rel_value = 0
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration:
                # ramp up phase
                target_rel_value = (elapsed_time - self.pre_phase_duration)/self.ramp_up_phase_duration
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration:
                # hold phase
                target_rel_value = 1
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration + self.ramp_down_phase_duration:
                # ramp down phase
                target_rel_value = 1 - (elapsed_time - self.pre_phase_duration - self.ramp_up_phase_duration - self.hold_phase_duration)/self.ramp_down_phase_duration
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.hold_phase_duration + self.ramp_down_phase_duration + self.post_phase_duration:
                # post phase
                target_rel_value = 0
            else:
                self.animate = False
                return ArrowWithRampTarget.ARROW_FINISHED

            # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
            target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value

            # transform bar value into screen coordinates
            target_y_pos = self.arrow_length * (target_abs_value - self.low_value) / (self.high_value - self.low_value)

            self.target_node.setPos(0, 0, target_y_pos)

        return InterfaceObject.NO_SIGNAL


class ArrowWithSinusTarget(Arrow):
    ARROW_FINISHED = 'arrow_finished'

    def __init__(self, pos_x=0, pos_y=0, depth=0, angle=0, arrow_length=0.5, line_width=0.02, head_size=0.1, target_size=0.1, target_info_size=0.1, arrow_color='lime', target_color='red', target_info_color='white',
                 pre_phase_duration=3, ramp_up_phase_duration=10, sinus_phase_duration=20, sinus_frequency=1, sinus_amplitude=0.1, ramp_down_phase_duration=10, post_phase_duration=3, low_value=0, high_value=0.2, start_value=0, ramp_value=0.2):
        super().__init__(pos_x, pos_y, depth, angle, arrow_length, line_width, head_size, target_size, arrow_color, target_color, low_value, high_value)
        self.animate = False
        self.start_time = None

        self.pre_phase_duration = pre_phase_duration
        self.ramp_up_phase_duration = ramp_up_phase_duration
        self.sinus_phase_duration = sinus_phase_duration
        self.ramp_down_phase_duration = ramp_down_phase_duration
        self.post_phase_duration = post_phase_duration

        self.sinus_frequency = sinus_frequency
        self.sinus_amplitude = sinus_amplitude

        self.start_value = start_value
        self.ramp_value = ramp_value

        # hold target
        self.hold_target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=self.node)
        self.hold_target_node.setScale(target_info_size/2, 1, target_info_size/2)
        hold_target_y_pos = self.arrow_length * (ramp_value - self.low_value) / (self.high_value - self.low_value)
        self.hold_target_node.setPos(0, 0, hold_target_y_pos)
        if isinstance(target_info_color, str):
            hold_target_color_tuple = StdColorMap[target_info_color]
        else:
            hold_target_color_tuple = target_info_color
        hold_target_color_tuple = LColor(hold_target_color_tuple, w=255) / 255
        self.hold_target_node.setColor(hold_target_color_tuple)
        self.hold_target_node.setBin('fixed', -depth - 1)

        # current target
        self.target_node = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=self.node)
        self.target_node.setScale(target_size/2, 1, target_size/2)
        target_y_pos = self.arrow_length * (start_value - self.low_value) / (self.high_value - self.low_value)
        self.target_node.setPos(0, 0, target_y_pos)
        if isinstance(target_color, str):
            target_color_tuple = StdColorMap[target_color]
        else:
            target_color_tuple = target_color
        target_color_tuple = LColor(target_color_tuple, w=255) / 255
        self.target_node.setColor(target_color_tuple)
        self.target_node.setBin('fixed', -depth - 1)

    def startAnimation(self):
        self.animate = True
        self.start_time = None
        self.sinus_time = None

    def stopAnimation(self):
        self.animate = False
        self.start_time = None
        self.sinus_time = None

    def updateState(self, time):
        # update actual value
        super().updateState(time)

        # update target value
        if self.active and self.animate:

            # get animation time
            if not self.start_time:
                self.start_time = time
            elapsed_time = time - self.start_time

            if elapsed_time < self.pre_phase_duration:
                # pre phase
                target_abs_value = self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration:
                # ramp up phase
                target_rel_value = (elapsed_time - self.pre_phase_duration)/self.ramp_up_phase_duration
                # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
                target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration:
                # sinus phase
                if not self.sinus_time:
                    self.sinus_time = time
                elapsed_sinus_time = time - self.sinus_time

                sin = self.sinus_amplitude*math.sin(2*math.pi*self.sinus_frequency*elapsed_sinus_time)
                target_abs_value = sin + self.ramp_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration + self.ramp_down_phase_duration:
                # ramp down phase
                target_rel_value = 1 - (elapsed_time - self.pre_phase_duration - self.ramp_up_phase_duration - self.sinus_phase_duration)/self.ramp_down_phase_duration
                # target_rel_value in [0, 1] -> target_abs_value in [start_value, ramp_value]
                target_abs_value = target_rel_value * (self.ramp_value - self.start_value) +  self.start_value
            elif elapsed_time < self.pre_phase_duration + self.ramp_up_phase_duration + self.sinus_phase_duration + self.ramp_down_phase_duration + self.post_phase_duration:
                # post phase
                target_abs_value = self.start_value
            else:
                self.animate = False
                return ArrowWithSinusTarget.ARROW_FINISHED

            # transform bar value into screen coordinates
            target_y_pos = self.arrow_length * (target_abs_value - self.low_value) / (self.high_value - self.low_value)

            self.target_node.setPos(0, 0, target_y_pos)

        return InterfaceObject.NO_SIGNAL


class SpikeVis(GraphicObject2D):

    def __init__(self, pos_x=0, pos_y=0, depth=0, number_of_units=2, size=0.01, spacing=0.05, flash_duration=0.2, active_color='lime', inactive_color='white'):
        node = aspect2d.attachNewNode('units')

        # convert color codes
        if isinstance(active_color, str):
            self.active_color = LColor(StdColorMap[active_color], w=255) / 255
        else:
            self.active_color = LColor(active_color, w=255) / 255
        if isinstance(inactive_color, str):
            self.inactive_color = LColor(StdColorMap[inactive_color], w=255) / 255
        else:
            self.inactive_color = LColor(inactive_color, w=255) / 255

        self.units = [None]*number_of_units
        self.last_flash = [0]*number_of_units
        self.flash_duration = flash_duration
        for unit_idx in range(number_of_units):
            unit_x_pos = unit_idx*spacing - (number_of_units-1)*spacing/2
            self.units[unit_idx] = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
            self.units[unit_idx].setBin('fixed', -depth)
            self.units[unit_idx].setTransparency(TransparencyAttrib.MAlpha)
            self.units[unit_idx].setScale(size, 1, size)
            self.units[unit_idx].setPos(unit_x_pos, 0, 0)
            self.units[unit_idx].setColor(self.inactive_color)

        super().__init__(node, pos_x, pos_y, depth, 1, 1, 0, None)

    def updateState(self, time):
        if self.active and self.lsl_state_control_streams:
            assert len(self.lsl_state_control_streams) == 1, 'SpikeVis: exactly one state control stream must be specified'
            assert len(self.state_control_channels) == len(self.units), 'SpikeVis: number of LSL channels must correspond to number of defined units'

            # flash on receiving a spike
            for unit_idx in range(len(self.units)):
                spikes = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[unit_idx]]

                # this warning may be unwanted
                # if spikes > 1:
                    # print('LSL buffer contained multiple spikes, check system speed')

                # activate unit
                if spikes > 0:
                    self.units[unit_idx].setColor(self.active_color)
                    self.last_flash[unit_idx] = time

                # deactivate unit after some time
                if time - self.last_flash[unit_idx] > self.flash_duration:
                    self.units[unit_idx].setColor(self.inactive_color)

            return InterfaceObject.NO_SIGNAL


class ReachTargets(GraphicObject2D):
    TARGET_REACHED = 'target_reached'
    START_TARGET_REACHED = 'start_target_reached'

    def __init__(self, pos_x=0, pos_y=0, depth=0, radius=1, number_of_targets=4, dwell_time=3, start_target=False, target_rotation=0, target_size=0.05, cursor_size=0.02, target_active_color='orange', target_inactive_color='white', target_reached_color='lime', cursor_color='red'):
        # note: pos_x and pos_y set the center of the targets while the main node "targets" is always positioned at (0,0); this way the cursor position is compatible to the screen coordinate system

        node = aspect2d.attachNewNode('targets')

        # convert color codes
        if isinstance(target_active_color, str):
            self.target_active_color = LColor(StdColorMap[target_active_color], w=255) / 255
        else:
            self.target_active_color = LColor(target_active_color, w=255) / 255
        if isinstance(target_inactive_color, str):
            self.target_inactive_color = LColor(StdColorMap[target_inactive_color], w=255) / 255
        else:
            self.target_inactive_color = LColor(target_inactive_color, w=255) / 255
        if isinstance(target_reached_color, str):
            self.target_reached_color = LColor(StdColorMap[target_reached_color], w=255) / 255
        else:
            self.target_reached_color = LColor(target_reached_color, w=255) / 255

        # create reach targets
        angle_delta = 360 / number_of_targets
        self.targets = [None] * number_of_targets
        self.radius = radius
        self.target_size = target_size
        for target_idx in range(number_of_targets):
            target_angle = target_rotation + angle_delta*target_idx

            target_pos_x = np.cos(target_angle/180*np.pi)*self.radius + pos_x
            target_pos_y = np.sin(target_angle/180*np.pi)*self.radius + pos_y

            self.targets[target_idx] = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
            self.targets[target_idx].setBin('fixed', -depth)
            self.targets[target_idx].setTransparency(TransparencyAttrib.MAlpha)
            self.targets[target_idx].setScale(target_size, 1, target_size)
            self.targets[target_idx].setPos(target_pos_x, 0, target_pos_y)

        # create start target
        if start_target:
            self.start_target = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
            self.start_target.setBin('fixed', -depth)
            self.start_target.setTransparency(TransparencyAttrib.MAlpha)
            self.start_target.setScale(target_size, 1, target_size)
            self.start_target.setPos(pos_x, 0, pos_y)
        else:
            self.start_target = None
        self.start_target_reached = False

        # create cursor target
        self.cursor = OnscreenImage(image=IMG_RESOURCES_DIR + '/ball_128x128.png', parent=node)
        # OnscreenImage.setImage(tex) -> self.setTexture(self) (from NodePath)
        # --> /panda3d.core.NodePath
        # panda3d.core.Texture
        # https://docs.panda3d.org/1.10/python/programming/texturing/simple-texturing
        self.cursor.setBin('fixed', -depth+1)
        self.cursor.setScale(cursor_size, 1, cursor_size)
        if isinstance(cursor_color, str):
            cursor_color_tuple = LColor(StdColorMap[cursor_color], w=255) / 255
        else:
            cursor_color_tuple = LColor(cursor_color, w=255) / 255
        self.cursor.setColor(cursor_color_tuple)
        self.cursor.setTransparency(TransparencyAttrib.MAlpha)

        self.dwell_time = dwell_time
        self.target_hit_time = None
        self.selected_target_idx = 0

        super().__init__(node, 0, 0, depth, 1, 1, 0, None)

    def setActiveTarget(self, selected_target_idx):
        assert selected_target_idx == None or (selected_target_idx >= 0 and selected_target_idx < len(self.targets)), 'invalid target index'
        for target_idx in range(len(self.targets)):
            self.targets[target_idx].setColor(self.target_inactive_color)
        if selected_target_idx != None:
            self.targets[selected_target_idx].setColor(self.target_active_color)
        self.selected_target_idx = selected_target_idx;

    def activate(self):
        super().activate()
        self.target_hit_time = None
        self.selected_target_idx = None
        self.start_target_reached = False
        if self.start_target:
            self.start_target.show()

    def deactivate(self):
        super().deactivate()
        self.target_hit_time = None
        self.selected_target_idx = None
        self.start_target_reached = False

    def updateState(self, time):
        if self.active and self.lsl_state_control_streams:
            assert len(self.lsl_state_control_streams) == 1, 'ReachTargets: exactly one state control stream must be specified'
            assert len(self.state_control_channels) == 2, 'ReachTargets: "channels" must have exactly two elements'

            cursor_x = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[0]] # first channel points to the right
            cursor_y = self.lsl_streams_samples[self.lsl_state_control_streams[0]][self.state_control_channels[1]] # second channel points upwards

            self.cursor.setPos(cursor_x, 0, cursor_y)

            if self.selected_target_idx != None:

                if self.start_target and not self.start_target_reached:
                    # check if cursor is within the start target area
                    target_x_pos, target_y_pos = self.start_target.getPos()[0], self.start_target.getPos()[2]
                    diff = np.sqrt((target_x_pos - cursor_x)**2 + (target_y_pos - cursor_y)**2)
                    if diff <= self.target_size:
                        self.start_target.setColor(self.target_reached_color)
                        if not self.target_hit_time:
                            self.target_hit_time = time
                        if time - self.target_hit_time >= self.dwell_time:
                            self.target_hit_time = None
                            self.start_target.hide()
                            self.start_target_reached = True
                            return ReachTargets.START_TARGET_REACHED
                    else:
                        self.start_target.setColor(self.target_active_color)
                        self.target_hit_time = None
                else:
                    # check if cursor is within the target area
                    target_x_pos, target_y_pos = self.targets[self.selected_target_idx].getPos()[0], self.targets[self.selected_target_idx].getPos()[2]
                    diff = np.sqrt((target_x_pos - cursor_x)**2 + (target_y_pos - cursor_y)**2)
                    if diff <= self.target_size:
                        self.targets[self.selected_target_idx].setColor(self.target_reached_color)
                        if not self.target_hit_time:
                            self.target_hit_time = time
                        if time - self.target_hit_time >= self.dwell_time:
                            return ReachTargets.TARGET_REACHED
                    else:
                        self.targets[self.selected_target_idx].setColor(self.target_active_color)
                        self.target_hit_time = None

            return InterfaceObject.NO_SIGNAL
