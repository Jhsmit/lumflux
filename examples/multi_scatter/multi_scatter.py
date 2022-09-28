from __future__ import annotations

import time

import param
import yaml
from pathlib import Path
import panel as pn
import pandas as pd
import numpy as np
import string
from lumflux.controllers import ControlPanel
from lumflux.constructor import AppConstructor
from lumflux.loader import load_spec

rng = np.random.default_rng(seed=43)


class ScatterControl(ControlPanel):

    _type = 'scatter'

    num_columns = param.Integer(5, bounds=(1, 26))

    a = param.Range(default=(-1.5, 1.5), bounds=(-5, 5))

    b = param.Range(default=(0, 10), bounds=(-20, 20))

    noise = param.Range(default=(0.1, 0.4), bounds=(0, 3.))

    N = param.Integer(default=100, bounds=(20, 500))

    genenerate_data = param.Action(lambda self: self._action_button())

    def _action_button(self):
        print('Button was pressed')

        x = np.linspace(0, 10, num=self.N, endpoint=True)
        columns = list(string.ascii_lowercase[0:self.num_columns])
        data = np.empty((self.N, self.num_columns))
        for i in range(self.num_columns):
            a = rng.uniform(*self.a)
            b = rng.uniform(*self.b)
            noise = rng.normal(0, rng.uniform(*self.noise), size=self.N)
            y = a*x+b+noise
            data[:, i] = y

        df = pd.DataFrame(data, index=x, columns=columns)
        self.sources['main'].set(df, "test_data")



app_spec = load_spec("app_spec.yaml")

ctr = AppConstructor(errors='warn')
main_ctrl = ctr.parse(app_spec)

df = pd.read_csv('pd_dataframe.csv', index_col=0)
main_ctrl.sources['main'].set(df, 'test_data')

graphs = pn.Column(
    main_ctrl.views['xy_scatter'].panel,
    width=800,
)

ctrl = main_ctrl.control_panels['ScatterControl']
buttons = ctrl.panel
app = pn.Row(buttons, graphs)


if __name__ == '__main__':
    pn.serve(app)
elif __name__.startswith('bokeh'):
    app.servable()

