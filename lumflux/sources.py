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

    content = param.Dict(default={})

    hashes = param.Dict(default={})

    max_items = param.Integer(
        default=0,
        doc="""Maximum number of items allowed in this source"""
    )

    def make_room(self):
        if self.max_items and self.content:
            first_key = next(iter(self.content))
            self.content.pop(first_key)

    def set(self, item, name=None):
        self.make_room()
        name = name or uuid.uuid4()
        self.hashes[name] = self.hash_item(item)
        self.content[name] = item

        self.updated = True

    def get(self, name: Optional[str] = None) -> Any:
        if not self.content:
            return None
        else:
            name = name or next(iter(self.keys()))
            return self.content.get(name)

    def hash_item(self, item) -> int:
        return hash(item)

    def keys(self) -> KeysView:
        return self.content.keys()

    def items(self) -> ItemsView:
        return self.content.items()

    def values(self) -> ValuesView:
        return self.content.values()


class TableSource(GenericSource):


    _type = "table"

    def hash_item(self, item) -> str:
        return hash_dataframe(item)




