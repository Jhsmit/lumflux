from __future__ import annotations

import itertools
import logging
import re
import time
from functools import partial
from itertools import groupby, count
from typing import Union, Optional

import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import param
from holoviews.streams import Pipe, Params
from panel.pane.base import PaneBase

from lumflux.sources import Source
from lumflux.transforms import Transform
from lumflux.pane import LoggingMarkdown
from lumflux.base import HasWidgets

from hvplot import hvPlotTabular


class View(HasWidgets):
    """Base view object.

    Inspired by Holoviz Lumen's View objects"""

    _type = None

    opts = param.List(
        default=[],
        doc="List of opts dicts to apply on the plot",
        precedence=-1
    )

    dependencies = param.List(
        default=[],
        doc="Additional dependencies which trigger update when their `updated` event fires",
        precedence=-1,
    )

    source = param.ClassSelector(
        class_=Source
    )

    def __init__(self, **params):
        super().__init__(**params)
        # todo allow for kwargs to be passed to DynamicMap's func

        for dep in self.dependencies:
            dep.param.watch(self.update, ["updated"])

        self._panel = None

    def get_data(self) -> pd.DataFrame:  # refactor get?
        """
        Queries the Source

        Returns
        -------
        DataFrame

        """

        df = self.source.get()
        if df is None:
            return self.empty_df
        else:
            return df

    def _update_panel(self, *events):
        """
        Updates the cached Panel object and returns a boolean value
        indicating whether a rerender is required.
        """

        self._panel = self.get_panel()
        return True

    @property  # todo move to init?
    def opts_dict(self):
        # Combine all opts and merge overlapping lists of opts
        # (currently to merge hooks, might be unwanted behaviour for others)
        opts_dict = {}
        for d in self.opts:  # Iterate over Opts on this view
            for k, v in d.opts.items():  # Iterate over all dict items in the Opt
                if k in opts_dict:
                    if isinstance(v, list) and isinstance(opts_dict[k], list):
                        combined_list = opts_dict[k] + v
                        opts_dict[k] = combined_list
                    else:
                        raise ValueError(
                            f"Overlapping key {k!r} in opt {d.name!r} on view {self.name!r}"
                        )
                else:
                    opts_dict[k] = v

        return opts_dict

# lumen `Panel` view?
# https://github.com/holoviz/lumen/commit/da632cfeee8346991fef772faf54319312cc3642
class DataFrameView(View):

    _type = 'dataframe'

    def get_panel(self):
        data = self.get_data()
        if data is not None:
            return pn.pane.DataFrame(object=data, sizing_mode='stretch_both')

    def _update_panel(self, *events):
        """
        Updates the cached Panel object and returns a boolean value
        indicating whether a rerender is required.
        """
        if self._panel is None:
            self._panel = self.get_panel()
        else:
            self._panel.object = self.get_data()
        return True


    @param.depends("source.updated", watch=True)
    def update(self, *events) -> None:
        self._update_panel()

    @property
    def panel(self):
        return self._panel


class hvView(View):

    source = param.ClassSelector(
        class_=(Source, Transform),
        constant=True,
        precedence=-1,
        doc="""
        The Source to query for the data.""",
    )

    _type = None

    _stream = param.ClassSelector(class_=Pipe)

    def __init__(self, **params):
        super().__init__(**params)
        data = self.get_data()
        self._stream = Pipe(data=data)
        #self._get_params()

    @param.depends("source.updated", watch=True)
    def update(self, *events) -> None:
        """Triggers an update of the view.

        The source is queried for new data and this is sent to the `_stream` object.

        """
        data = self.get_data()
        if data is not None:
            self._stream.send(data)

    def get_panel(self):
        kwargs = self._get_params()
        return pn.pane.HoloViews(linked_axes=False, **kwargs)  # linked_axes=False??

    def _get_params(self):
        # df = self.get_data()
        # if df is None:
        #     df = self.empty_df
        #
        # self._stream = Pipe(data=df)
        return dict(
            object=self.get_plot(), sizing_mode="stretch_both"
        )  # todo update sizing mode

    @property
    def panel(self):
        return self.get_panel()


class hvPlotView(hvView):
    _type = "hvplot"

    kind = param.String()

    def __init__(self, **params):
        self.kwargs = {k: v for k, v in params.items() if k not in self.param}
        super().__init__(**{k: v for k, v in params.items() if k in self.param})

    def get_plot(self):
        """

        Parameters
        ----------
        df

        Returns
        -------

        """

        def func(data, kind, **kwargs):
            return hvPlotTabular(data)(kind=kind, **kwargs)

        pfunc = partial(func, kind=self.kind, **self.kwargs)

        plot = hv.DynamicMap(pfunc, streams=[self._stream])

        print(self.opts_dict)
        plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def empty_df(self):
        df = pd.DataFrame({"null": [np.nan], "y2": [np.nan]})
        return df


class hvXYView(hvView):
    """Base class for hv views with a single XY view"""

    x = param.Selector(
        default=None,
        doc="The column to render on the x-axis."
    )

    x_objects = param.ClassSelector(
        class_= (list, re.Pattern),
        default=None,
        precedence=-1
    )

    y = param.Selector(
        default=None,
        objects=[],
        doc="The column to render on the y-axis.")

    y_objects = param.ClassSelector(
        class_= (list, re.Pattern),
        default=None,
        precedence=-1
    )

    @param.depends("source.updated", watch=True)
    def update(self, *events) -> None:
        """Triggers an update of the view.

        The source is queried for new data and this is sent to the `_stream` object. The
        selector options for x and y are updated.

        """
        data = self.get_data()
        if data is not None:
            self.param['x'].objects = self.resolve_columns(data, self.x_objects)
            self.param['y'].objects = self.resolve_columns(data, self.y_objects)

            # todo check for case whe updated dataframe longer has current value of x in columns
            self._stream.send(data)

    @staticmethod
    def resolve_columns(data: pd.DataFrame, spec: Union[list, re.Pattern, None]) -> list[str]:
        """Resolve the columns of a dataframe to find the ones that match specification.

        Args:
            data: Dataframe to resolve
            spec: Column specification, either explicit list of allowed columns or a regex
                pattern.

        Returns:
            List of names of the columns (or index) which match specification.
        """
        all_objects = list(data.columns)
        if data.index.name is not None:
            all_objects += data.index.name

        if isinstance(spec, list):
            resolved_objects = [obj for obj in all_objects if obj in spec]
        elif isinstance(spec, re.Pattern):
            resolved_objects = [obj for obj in all_objects if spec.match(obj)]
        else:
            resolved_objects = all_objects

        return resolved_objects


class hvCurveView(hvXYView):
    _type = "curve"


    def get_plot(self) -> hv.DynamicMap:
        """Creates the curve plot as DynamicMap.

        Returns:
            Holoviews DynamicMap
        """

        func = partial(hv.Curve, kdims=self.y, vdims=self.x)
        param_stream = Params(
            parameterized=self,
            parameters=['x', 'y'],
            rename={'x': 'kdims', 'y': 'vdims'})
        plot = hv.DynamicMap(func, streams=[self._stream, param_stream])
        plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def empty_df(self):
        dic = {self.x or "x": [], self.y or "y": []}
        return pd.DataFrame(dic)


class hvScatterAppView(hvXYView):
    _type = "scatter"

    def get_plot(self) -> hv.DynamicMap:
        """Creates the scatter plot as DynamicMap

        Returns:
            Holoviews DynamicMap
        """

        func = partial(hv.Scatter, kdims=self.x, vdims=self.y)
        param_stream = Params(
            parameterized=self,
            parameters=['x', 'y'],
            rename={'x': 'kdims', 'y': 'vdims'})
        plot = hv.DynamicMap(hv.Scatter, streams=[self._stream, param_stream])
        plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def empty_df(self):
        dic = {self.x or "x": [], self.y or "y": []}
        if "color" in self.opts_dict:
            dic[self.opts_dict["color"]] = []
        return pd.DataFrame(dic)


class hvBarsAppView(hvXYView):
    _type = "bars"

    def get_plot(self) -> hv.DynamicMap:
        """Creates the scatter plot as DynamicMap

        Returns:
            Holoviews DynamicMap
        """

        func = partial(hv.Bars, kdims=self.x, vdims=self.y)
        param_stream = Params(
            parameterized=self,
            parameters=['x', 'y'],
            rename={'x': 'kdims', 'y': 'vdims'})
        plot = hv.DynamicMap(func, streams=[self._stream, param_stream])
        plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def empty_df(self):
        dic = {self.x or "x": [], self.y or "y": []}
        if "color" in self.opts_dict:
            dic[self.opts_dict["color"]] = []
        return pd.DataFrame(dic)


class hvRectanglesAppView(hvView):
    _type = "rectangles"

    x0 = param.String("x0")

    x1 = param.String("x1")

    y0 = param.String("y0")

    y1 = param.String("y1")

    vdims = param.List(["value"])

    def __init__(self, **params):
        # todo left and right cannot be none?
        super().__init__(**params)

    def get_plot(self):
        """
        Dataframe df must have columns x0, y0, x1, y1 (in this order) for coordinates
        bottom-left (x0, y0) and top right (x1, y1). Optionally a fifth value-column can be provided for colors

        Parameters
        ----------
        df

        Returns
        -------

        """

        func = partial(hv.Rectangles, kdims=self.kdims, vdims=self.vdims)
        plot = hv.DynamicMap(func, streams=[self._stream])

        if self.opts_dict:
            plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def kdims(self):
        return [self.x0, self.y0, self.x1, self.y1]

    @property
    def empty_df(self):
        columns = self.kdims + self.vdims
        return pd.DataFrame([[0] * len(columns)], columns=columns)


class hvErrorBarsAppView(hvView):
    _type = "errorbars"

    pos = param.String(
        "x", doc="Positions of the errobars, x-values for vertical errorbars"
    )

    value = param.String(
        "y", doc="Values of the samples, y-values for vertical errorbars"
    )

    err = param.String(None, doc="Error values in both directions")

    err_pos = param.String(None, doc="Error values in positive direction")

    err_neg = param.String(None, doc="Error values in negative direction")

    horizontal = param.Boolean(False, doc="error bar direction")

    def __init__(self, **params):

        # todo left and right cannot be none?
        super().__init__(**params)

    def get_plot(self):
        """
        Dataframe df must have columns x0, y0, x1, y1 (in this order) for coordinates
        bottom-left (x0, y0) and top right (x1, y1). Optionally a fifth value-column can be provided for colors

        Parameters
        ----------
        df

        Returns
        -------

        """

        func = partial(
            hv.ErrorBars, kdims=self.kdims, vdims=self.vdims, horizontal=self.horizontal
        )
        plot = hv.DynamicMap(func, streams=[self._stream])

        if self.opts_dict:
            plot = plot.apply.opts(**self.opts_dict)

        return plot

    @property
    def vdims(self):
        if self.err is not None and self.err_pos is None and self.err_neg is None:
            return [self.value, self.err]
        elif self.err is None and self.err_pos is not None and self.err_neg is not None:
            return [self.value, self.err_pos, self.err_neg]
        else:
            raise ValueError(
                "Must set either only 'err' or both 'err_pos' and 'err_neg'"
            )

    @property
    def kdims(self):
        return [self.pos]

    @property
    def empty_df(self):
        columns = self.kdims + self.vdims
        return pd.DataFrame([[0] * len(columns)], columns=columns)


class hvOverlayView(View):
    _type = "overlay"

    views = param.List(doc="List of view instances to make overlay")

    def update(self):
        self._update_panel()

    def _cleanup(self):
        pass

    def get_plot(self):
        items = [view.get_plot() for view in self.views]
        plot = hv.Overlay(
            items
        ).collate()  # todo is collate always needed? Does it always return a DynamicMap? -> generalize

        if self.opts_dict:
            plot = plot.apply.opts(**self.opts_dict)

        return plot

    def _get_params(self):
        return dict(object=self.get_plot(), sizing_mode="stretch_both")

    def get_panel(self):
        kwargs = self._get_params()
        # interactive? https://github.com/holoviz/panel/issues/1824
        return pn.pane.HoloViews(**kwargs)

    @property
    def panel(self):
        if isinstance(self._panel, PaneBase):
            pane = self._panel
            if len(pane.layout) == 1 and pane._unpack:
                return pane.layout[0]
            return pane._layout
        return self._panel


class LoggingView(View):
    _type = "logging"

    logger = param.ClassSelector(
        logging.Logger, doc="Logger object to show in Log view"
    )

    level = param.Integer(
        default=10,
        doc="Logging level of the streamhandler redirecting logs to the view",
    )

    def __init__(self, *args, **params):
        super(LoggingView, self).__init__(**params)
        title = self.opts_dict.get("title", "Log Window")
        self.markdown = LoggingMarkdown(f"### {title} \n", sizing_mode="stretch_both")

        self.sh = logging.StreamHandler(self.markdown)
        self.sh.terminator = "  \n"
        self.sh.setLevel(self.level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        self.sh.setFormatter(formatter)
        self.logger.addHandler(self.sh)

    @param.depends("level", watch=True)
    def _level_updated(self):
        self.sh.setLevel(self.level)

    @property
    def panel(self):
        return self.markdown

    def update(self, *events, invalidate_cache=True):
        pass
