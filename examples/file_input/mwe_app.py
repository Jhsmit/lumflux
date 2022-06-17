from __future__ import annotations

import time
from io import StringIO

import param
import panel as pn
import pandas as pd
import numpy as np

from lumflux.controllers import ControlPanel
from lumflux.constructor import AppConstructor
from lumflux.loader import load_spec


class FileInputControl(ControlPanel):
    """Input .csv files"""

    _type = 'file_input'

    single_file = param.Parameter()

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

        file_input = pn.widgets.FileInput(accept='.csv', multiple=False)
        widgets = super().generate_widgets(single_file=file_input)

        return widgets

    @param.depends('single_file', watch=True)
    def _file_input_updated(self):
        sio = StringIO(self.single_file.decode('UTF-8'))

        df = pd.read_csv(sio)
        print(df)

        self.sources['main'].set(df)


    @property
    def layout(self) -> list[tuple]:
        return [
            ('self', None),
        ]


app_spec = load_spec("app_spec.yaml")

ctr = AppConstructor(errors='warn')
ctrl = ctr.parse(app_spec)

df = pd.DataFrame(
    {'x': np.arange(10), 'y': np.random.rand(10)}
)
ctrl.sources['main'].set_table('main', df)


mwe_control = ctrl.control_panels['FileInputControl']

buttons = mwe_control.panel
graphs = pn.Column(
    ctrl.views['dataframe'].panel,
    sizing_mode='stretch_width'

)

app = pn.Row(buttons, graphs)

if __name__ == '__main__':
    pn.serve(app)
elif __name__.startswith('bokeh'):
    app.servable()

