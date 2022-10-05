from __future__ import annotations

import time

import param
import yaml
from pathlib import Path
import panel as pn
import pandas as pd
import numpy as np

from lumflux.control_panels import ControlPanel
from lumflux.constructor import AppConstructor
from lumflux.widgets import ASyncProgressBar
from lumflux.template import GoldenElvis, ExtendedGoldenTemplate
from lumflux.theme import ExtendedGoldenDefaultTheme, ExtendedGoldenDarkTheme


class MWEControl(ControlPanel):

    _type = 'mwe'

    gen_data = param.Action(lambda self: self._action_button())

    loc = param.Number(default=2., bounds=(-1, 3), doc="Center position for histogram data")

    update_hist = param.Action(lambda self: self._hist_button())

    test = param.Action(lambda self: self._test_button())

    _not_a_number = param.Number(123)

    temperature = param.Number(
        293.15,
        bounds=(273.15, 373.15),
        doc="Temperature of the reaction",
        label="Temperature (K)"
    )

    def _test_button(self):
        print(self.sources['main'].contents)
        print(self.sources['main'].hashes)

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
            self.sources['main'].set(df, "test_data")

            time.sleep(0.25*np.random.rand())

        pbar.reset()

    def _hist_button(self):
        print(f'Updating hist location to {self.loc:.1f}')
        df = pd.DataFrame({'x': np.random.normal(self.loc, 0.1, size=int(np.random.uniform(100, 1000)))})
        self.sources['hist_src'].set(df)

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

    @property
    def layout(self) -> list[tuple]:
        return [
            ('self', None),
            ('views.xy_line', None)
        ]


#app_spec = yaml.safe_load("app_spec.yaml")

ctr = AppConstructor(errors='warn')
ctrl = ctr.parse_yaml("app_spec.yaml")

df = pd.DataFrame(
    {'x': np.arange(10), 'y': np.random.rand(10)}
)

ctrl.sources['main'].set(df, 'test_data')
df = pd.DataFrame(
    {'x': np.arange(10), 'y1': np.random.rand(10), 'y2': np.random.rand(10), 'y3': np.random.rand(10)}
)
ctrl.sources['main'].set(df, 'lines')

df = pd.DataFrame({'x': np.random.normal(2, 0.1, size=1000)})
ctrl.sources['hist_src'].set(df)


elvis = GoldenElvis(ctrl, ExtendedGoldenTemplate, ExtendedGoldenDefaultTheme, title="My templated app")

app = elvis.compose(
    elvis.column(
        elvis.stack(
            elvis.view('xy_scatter'),
            elvis.view('xy_line')
        ),
        elvis.stack(
            elvis.view('hist'),
            elvis.view('bars')
        )
    )
)


#
# mwe_control = ctrl.control_panels['mwe_controller']
#
# buttons = mwe_control.panel
# graphs = pn.Column(
#     ctrl.views['xy_scatter'].panel,
#     ctrl.views['xy_line'].panel,
#     ctrl.views['bars'].panel
# )
#
# app = pn.Row(buttons, graphs)

if __name__ == '__main__':
    pn.serve(app)
elif __name__.startswith('bokeh'):
    app.servable()

