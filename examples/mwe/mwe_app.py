import time

import param
import yaml
from pathlib import Path
import panel as pn
import pandas as pd
import numpy as np

from lumflux.base import ControlPanel
from lumflux.constructor import AppConstructor
from lumflux.widgets import ASyncProgressBar


class MWEControl(ControlPanel):

    _type = 'mwe'

    test_button = param.Action(lambda self: self._action_button())

    _not_a_number = param.Number(123)

    temperature = param.Number(
        293.15,
        bounds=(273.15, 373.15),
        doc="Temperature of the reaction",
        label="Temperature (K)"
    )

    def _action_button(self):
        print('Button was pressed')

        num_tasks = np.random.randint(4, 12)
        pbar = self.widgets["pbar"]
        pbar.num_tasks = num_tasks
        for i in range(num_tasks):
            pbar.completed += 1

            df = pd.DataFrame(
                {'x': np.arange(10), 'y': np.random.rand(10)}
            )
            self.sources['main'].set_table('test_data', df)

            time.sleep(0.25*np.random.rand())

        pbar.reset()

    def generate_widgets(self, **kwargs) -> dict:
        """Generates widgets

        By default, widgets are generated from the object's parameters. Custom widgets can
        be added

        Args:
            **kwargs: Kwargs to pass to pn.Param's `widgets` keyword argument. Use to
            override default mappings.

        Returns:
            Dictionary of widgets.

        """

        widgets = super().generate_widgets(temperature=pn.widgets.FloatInput)
        widgets["pbar"] = ASyncProgressBar()

        return widgets

app_spec = yaml.safe_load(Path("app_spec.yaml").read_text(encoding="utf-8"))

ctr = AppConstructor(errors='warn')
ctrl = ctr.parse(app_spec)

df = pd.DataFrame(
    {'x': np.arange(10), 'y': np.random.rand(10)}
)
ctrl.sources['main'].set_table('test_data', df)

mwe_control = ctrl.control_panels['MWEControl']

buttons = mwe_control.panel
graphs = pn.Column(ctrl.views['xy_scatter'].get_panel(), ctrl.views['xy_line'].get_panel())

app = pn.Row(buttons, graphs)

if __name__ == '__main__':
    pn.serve(app)
elif __name__.startswith('bokeh'):
    app.servable()

