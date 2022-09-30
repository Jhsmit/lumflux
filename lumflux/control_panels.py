import param
from lumflux.main_controllers import MainController
from lumflux.base import HasWidgets

import panel as pn


class ControlPanel(HasWidgets):
    """Base class for control panels.

    Control panels typically have buttons and input widgets, triggering data operations,
    and publishing the result on the respective sources, thereby pushing it to the views.
    All control panels have access to the app's main controller as `parent` attribute. This
    main controller has dicts containing all views, transforms and sources in the app.

    """

    _type = None

    header = param.String("Default Header") # todo derive header from _type

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

    def set_objects(self, param_name: str, objects, default=None, empty_default=False):

        if isinstance(objects, set):
            objects = list(objects)
        if isinstance(objects, list):
            autodefault = objects[0]
        elif isinstance(objects, dict):
            autodefault = next(iter(objects.values()))
        else:
            raise TypeError("Invalid type for 'objects', must be 'set', 'list' or 'dict'")

        self.param[param_name].objects = objects

        default = autodefault if (not empty_default and default is None) else default
        if default:
            setattr(self, param_name, default)


    # todo check if this is the right thing to implement for panel
    @property
    def panel(self):
        return self._box
