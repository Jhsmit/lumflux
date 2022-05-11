import param
import yaml
from pathlib import Path
import panel as pn
import pandas as pd
import numpy as np

from lumflux.base import ControlPanel
from lumflux.constructor import AppConstructor

class MWEControl(ControlPanel):

    _type = 'mwe'

    test_button = param.Action(lambda self: self._action_button())

    def _action_button(self):
        print('Button was pressed')
        df = pd.DataFrame(
            {'x': np.arange(10), 'y': np.random.rand(10)}
        )

        self.sources['main'].add_table('test_data', df)


app_spec = yaml.safe_load(Path("app_spec.yaml").read_text(encoding="utf-8"))

ctr = AppConstructor()
ctrl = ctr.parse(app_spec)

df = pd.DataFrame(
    {'x': np.arange(10), 'y': np.random.rand(10)}
)
ctrl.sources['main'].add_table('test_data', df)

mwe_control = ctrl.control_panels['MWEControl']

buttons = pn.Column(*mwe_control.widgets.values())
graphs = pn.Column(ctrl.views['xy_scatter'].get_panel(), ctrl.views['xy_line'].get_panel())

app = pn.Row(buttons, graphs)

if __name__ == '__main__':
    pn.serve(app)
elif __name__.startswith('bokeh'):
    app.servable()

