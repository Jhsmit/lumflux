from typing import Union, Iterable

import panel as pn
import param

from asyncio import as_completed, Future
from abc import abstractmethod


class WidgetView(param.Parameterized):
    """A custom widget implementing the `view()` method"""

    @abstractmethod
    def view(self):
        ...


class ASyncProgressBar(WidgetView):
    completed = param.Integer(default=0, doc="Number of completed jobs")

    num_tasks = param.Integer(default=10, doc="Total number of tasks", bounds=(1, None))

    active = param.Boolean(False, doc="Toggles the progress bar 'active' display mode")

    async def run(self, futures: Iterable[Future]) -> None:
        self.active = True
        for task in as_completed(futures):
            await task
            self.active = False
            self.completed += 1

        self.reset()

    @property
    def value(self) -> int:
        value = int(100 * (self.completed / self.num_tasks))
        value = max(0, min(value, 100))

        if value == 0 and self.active:
            return -1
        else:
            return value

    def reset(self) -> None:
        self.completed = 0

    def increment(self) -> None:
        self.completed += 1

    @param.depends("completed", "num_tasks", "active")
    def view(self) -> Union[pn.widgets.Progress, pn.layout.Spacer]:
        if self.value != 0:
            return pn.widgets.Progress(
                active=self.active,
                value=self.value,
                align="center",
                sizing_mode="stretch_width",
            )
        else:
            return pn.layout.Spacer()



