from __future__ import annotations

import uuid
from collections.abc import KeysView, ItemsView, ValuesView
from typing import Optional, Any

import pandas as pd
import param

from lumflux.support import hash_dataframe


class Source(param.Parameterized):
    """Base class for sources"""

    _type = None

    updated = param.Event()

    # def get(self) -> None:
    #     raise NotImplementedError()


class GenericSource(Source):

    contents = param.Dict(default={})

    hashes = param.Dict(default={})

    @property
    def singular(self) -> bool:
        return len(self.contents) == 1

    @property
    def empty(self) -> bool:
        return len(self.contents) == 0

    def set(self, item, name=None):
        if self.empty and name is None:
            name = uuid.uuid4()
        # Overwriting the current item
        elif self.singular and name is None:
            name = next(iter(self.keys()))
        elif name is None:
            raise ValueError("No name given for new source item.")

        self.hashes[name] = self.hash_item(item)
        self.contents[name] = item
        self.updated = True

    def get(self, name: Optional[str] = None) -> Any:
        if self.empty:
            return None
        elif self.singular and name is None:
            name = next(iter(self.keys()))

        return self.contents.get(name)

    def hash_item(self, item) -> int:
        return hash(item)

    def keys(self) -> KeysView:
        return self.contents.keys()

    def items(self) -> ItemsView:
        return self.contents.items()

    def values(self) -> ValuesView:
        return self.contents.values()



class TableSource(GenericSource):


    _type = "table"

    def hash_item(self, item) -> str:
        return hash_dataframe(item)




