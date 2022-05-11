from __future__ import annotations

import pandas as pd
import param

from lumflux.support import hash_dataframe


class Source(param.Parameterized):
    """Base class for sources"""

    _type = None

    updated = param.Event()

    def get(self) -> None:
        raise NotImplementedError()


class TableSource(Source):

    tables = param.Dict(default={}, doc="Dictionary of tables (pd.DataFrames)")

    hashes = param.Dict(default={}, doc="Dictionary of table hashes")

    _type = "table"

    def get(self):
        if len(self.tables) == 0:
            return None
        elif len(self.tables) == 1:
            return next(iter(self.tables.values()))

        else:
            raise ValueError("TableSource has multiple tables, use `get_table`")

    def set(self, df: pd.DataFrame) -> None:
        if len(self.tables) > 1:
            raise ValueError(
                "Can only use the `set` method when the number of tables is below 1. "
                "Use `set_table`"
            )

        table = next(iter(self.tables.keys())) if self.tables else 'main'
        self.set_table(table, df)

    def set_table(self, table: str, df: pd.DataFrame) -> None:
        """Adds a new dataframe to the source.

        Args:
            table:
            df:

        Returns:

        """
        table_hash = hash_dataframe(df)
        self.hashes[table] = table_hash
        self.tables[table] = df

        self.updated = True

    def get_table(self, table: str) -> pd.DataFrame:
        """Get dataframe from the source

        Args:
            table:

        Returns:

        """
        df = self.tables.get(table, None)

        return df

    def get_tables(self) -> list[str]:
        """Get a list of tables available on this source.

        Returns:
            The list of available tables on this source.
        """

        return list(self.tables.keys())



