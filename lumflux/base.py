from __future__ import annotations

from pathlib import Path

import panel as pn
import param

from lumflux.main_controllers import MainController
from lumflux.template import SIDEBAR_WIDTH # TODO move to layout config file
from lumflux.support import get_view
from lumflux.param import Param

STATIC_DIR = Path(__file__).parent / "static"


def has_precedence(p: param.Parameter) -> bool:
    """Checks the precedence of a parameter.

    Returns:
        `True` if the `precedence` is None or larger or equal then zero, else `False`.

    """
    if p.precedence is None:
        return True
    elif p.precedence >= 0:
        return True
    else:
        return False


class HasWidgets(param.Parameterized):
    """Base class for object which generate widgets from their parameters."""

    _type = None

    _excluded = param.List(
        [],
        precedence=-1,
        doc="Parameters whose widgets are excluded from the control panel view. "
            "This list can be modified to update widget layout",
    )

    def __init__(self, **params):
        super().__init__(**params)
        self.widgets = self.generate_widgets()
        self._box = self.make_box()

    @property
    def own_widget_names(self) -> list[str]:
        return [name for name in self.widgets.keys() if name not in self._excluded]

    @property
    def layout(self) -> list[tuple]:
        return [
            ("self", self.own_widget_names),
        ]

    def make_box(self):
        name = getattr(self, 'header', None)
        return pn.Column(*self.widget_list, name=name, width=SIDEBAR_WIDTH)

    def update_box(self, *events):
        self._box[:] = self.widget_list

    def generate_widgets(self, **kwargs) -> dict[str, pn.widgets.Widget]:
        """Creates a dict with keys parameter names and values default mapped widgets"""

        # Get all parameters with precedence >= 1 and not starting with '_', excluding 'name'
        parameters = {p_name for p_name in self.param if not p_name.startswith('_')}
        parameters -= {'name'}
        parameters -= {p_name for p_name, par in self.param.objects().items() if not has_precedence(par)}

        widgets_layout = Param(
            self.param, show_labels=True, show_name=False, widgets=kwargs, parameters=list(parameters)
        )

        return widgets_layout.get_widgets()

    # TODO this should move to some kind of layout resolving class
    @property
    def widget_list(self) -> list:
        """Resolves a `layout` definition to a list of widgets

        Returns:
            List of widgets

        """

        widget_list = []
        for widget_source, contents in self.layout:
            if widget_source == "self":
                obj = self
            else:
                _type, name = widget_source.split(".")
                obj = getattr(self, _type)[name]

            if isinstance(contents, list):
                for item in contents:
                    widget_list.append(get_view(obj.widgets[item]))
            elif isinstance(contents, str):
                widget_list.append(get_view(obj.widgets[contents]))
            elif contents is None:
                if hasattr(obj, "widgets"):
                    for item in obj.widgets.values():
                        widget_list.append(get_view(item))
                # Not sure if we should keep supporting putting .panels in layouts
                else:
                    print(f'The object {obj!r} has a panel property')
                    panel = obj.panel
                    if isinstance(panel, pn.layout.ListLike):
                        for item in panel:
                            widget_list.append(get_view(item))
                    else:
                        widget_list.append(get_view(panel))

        return widget_list


class ControlPanel(HasWidgets):
    """Base class for control panels.

    Control panels typically have buttons and input widgets, triggering data operations,
    and publishing the result on the respective sources, thereby pushing it to the views.
    All control panels have access to the app's main controller as `parent` attribute. This
    main controller has dicts containing all views, transforms and sources in the app.

    """

    _type = None

    header = "Default Header"

    parent = param.ClassSelector(MainController, precedence=-1)

    def __init__(self, parent, **params):
        super(ControlPanel, self).__init__(parent=parent, **params)


        # bind update function when any transform triggers a redraw of widgets
        if self.layout:
            for widget_source, contents in self.layout:
                if widget_source != "self":
                    _type, name = widget_source.split(".")
                    if _type == "transforms":
                        obj = getattr(self, _type)[name]
                        obj.param.watch(self.update_box, ["redrawn"])

    @property
    def sources(self):
        return self.parent.sources

    @property
    def transforms(self):
        return self.parent.transforms

    @property
    def opts(self):
        return self.parent.opts

    @property
    def views(self):
        return self.parent.views

    def get_widget(self, param_name, widget_type, **kwargs):
        """get a single widget with for parameter param_name with type widget_type"""

        # not sure if this function still exists
        return pn.Param.get_widget(
            getattr(self.param, param_name), widget_type, **kwargs
        )[0]

    # todo check if this is the right thing to implement for panel
    @property
    def panel(self):
        return self._box
