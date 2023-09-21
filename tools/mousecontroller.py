from panda3d.core import WindowProperties, ClockObject
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextNode, TextFont
from direct.gui.OnscreenText import OnscreenText
import sys
import pylsl


FPS = 60
globalClock = ClockObject.getGlobalClock()
globalClock.setMode(ClockObject.MLimited)
globalClock.setFrameRate(FPS)


class MouseController(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        props = WindowProperties()
        props.setTitle('Mouse Controller')
        base.win.requestProperties(props)

        self.accept('escape', sys.exit)
        base.disableMouse()
        base.setFrameRateMeter(True)

        # set up mouse position streaming
        lsl_pos_info = pylsl.StreamInfo('MouseControllerStream', 'position', 2, FPS, pylsl.cf_float32, 'mousecontroller_pos')
        self.lsl_pos_outlet = pylsl.StreamOutlet(lsl_pos_info)
        self.task = taskMgr.add(self.updateLSLOutlet, 'updateLSLOutlet')

        # set up mouse button event generation
        lsl_button_info = pylsl.StreamInfo('MouseControllerMarkers', 'button', 1, pylsl.IRREGULAR_RATE, pylsl.cf_string, 'mousecontroller_button')
        self.lsl_button_outlet = pylsl.StreamOutlet(lsl_button_info)
        self.accept('mouse1', self.generateLSLEvent, [1])
        self.accept('mouse2', self.generateLSLEvent, [2])
        self.accept('mouse3', self.generateLSLEvent, [3])
        self.accept('arrow_up', self.generateLSLEvent, [1])
        self.accept('arrow_left', self.generateLSLEvent, [2])
        self.accept('arrow_right', self.generateLSLEvent, [3])

        text_node = OnscreenText('move mouse cursor within this window')
        text_node.setAlign(TextNode.ACenter)

        self.display_counter = 0

    def updateLSLOutlet(self, task):
        if base.mouseWatcherNode.hasMouse():
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()

            x *= 1
            y *= 1
            self.display_counter += 1
            if self.display_counter % 15 == 0:
                print('%f\t%f' % (x,y))

            self.lsl_pos_outlet.push_sample([x, y], pushthrough=True)

        return Task.cont

    def generateLSLEvent(self, button):
        event_name = 'button' + str(button)
        self.lsl_button_outlet.push_sample([event_name], pushthrough=True)



app = MouseController()
app.run()
