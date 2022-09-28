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

    max_items = param.Integer(
        default=0,
        doc="""Maximum number of items allowed in this source"""
    )

    def make_room(self):
        if self.max_items and self.contents:
            first_key = next(iter(self.contents))
            self.contents.pop(first_key)

    def set(self, item, name=None):
        self.make_room()
        name = name or uuid.uuid4()
        self.hashes[name] = self.hash_item(item)
        self.contents[name] = item

        self.updated = True

    def get(self, name: Optional[str] = None) -> Any:
        if not self.contents:
            return None
        else:
            name = name or next(iter(self.keys()))
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




