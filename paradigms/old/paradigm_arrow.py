from pathlib import Path
import numpy as np

from yaga_modules.paradigm_base import ParadigmBase, ScriptItem
import yaga_modules.graphic_objects as GO
import yaga_modules.signal_processing as SP


class Paradigm(ParadigmBase):

    # root_dir = Path.home() / Path('Documents') / Path('CurrentStudy')
    root_dir = Path.home() / Path('Nextcloud') / Path('Data')
    task_name = 'arrow'

    def __init__(self, paradigm_variables):
        super().__init__(paradigm_variables, lsl_recorder_remote_control=False, lsl_recorder_host='localhost')

        cross = self.registerObject(GO.Cross(scale_x=0.1, scale_y=0.1, color='black', depth=2))

        # arrow = self.registerObject(GO.Arrow(pos_x=0, pos_y=0, depth=0, arrow_length=0.5, line_width=0.1, head_size=0.1, color='green', low_value=0.0, high_value=1.0))
        # arrow = self.registerObject(GO.Arrow(high_value=0.1))
        # arrow = self.registerObject(GO.ArrowWithRampTarget())
        arrow = self.registerObject(GO.ArrowWithSinusTarget())

        normalization = SP.MaxEuclidNormalizationXDF(str(self.root_dir / Path('%s_S%.3d' % (paradigm_variables['subject'], paradigm_variables['session'])) / Path('task_mvc_run_001.xdf')), 'quattrocento', 'yaga', 'start_counter', 'trial_end', [64, 65], 2.761e6)
        arrow.controlStateWithLSLStream('quattrocento', channels=[64, 65])
        # arrow.controlStateWithLSLStream('MouseControllerStream', channels=[0, 1])
        arrow.addSignalProcessingToLSLStream(normalization, channels=[64, 65])

        arrow.activate()
        arrow.startAnimation()
        cross.activate()

        self.script = [ScriptItem(name='trial_start', time=0, actions=[]),
                       ScriptItem(name='trial_end', time=np.inf, actions=[])]
