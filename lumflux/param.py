from collections import OrderedDict

import panel as pn

class Param(pn.Param):

    def get_widgets(self) -> OrderedDict:
        return self._widgets