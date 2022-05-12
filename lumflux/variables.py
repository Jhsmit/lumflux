from lumflux.base import HasWidgets
import param
from functools import partial



class Variables(HasWidgets):

    def __init__(self, **params):
        super().__init__(**params)
        ...
        """dynamically add variables from spec"""

    def add_variable(self, var):
        """
        Adds a new variable to the Variables instance and sets up
        a parameter that can be watched.
        """
        self._vars[var.name] = var
        self.param.add_parameter(var.name, param.Parameter(default=var.value))
        var.param.watch(partial(self._update_value, var.name), 'value')

    def _update_value(self, name, event):
        self.param.update({name: event.new})