from typing import Generator, Any, Type, TypeVar, Optional, Union

import pandas as pd
import numpy as np
from matplotlib.colors import Colormap, Normalize

import hashlib



def hash_dataframe(df: pd.DataFrame, method="builtin") -> str:
    if method == "builtin":
        tup = (
            *pd.util.hash_pandas_object(df, index=True).values,
            *df.columns,
            *df.columns.names,
            df.index.name,
        )

        return str(hash(tup))

    elif method == "md5":
        pd_values = list(pd.util.hash_pandas_object(df, index=True).values)
        if isinstance(df.columns, pd.MultiIndex):
            columns = [name for cols in df.columns for name in cols]
        else:
            columns = list(df.columns)

        all_vals = pd_values + columns + list(df.index.names) + list(df.columns.names)
        h = hashlib.md5()
        for val in all_vals:
            h.update(str(val).encode("UTF-8"))

        return h.digest().hex()

    else:
        raise ValueError(f"Invalid method {method!r}, must be 'builtin' or 'md5'")


T = TypeVar('T')


def gen_subclasses(cls: Type[T]) -> Generator[Type[T], None, None]:
    """Generator yielding subclasses of `cls`.

    Args:
        cls: Class to find subclasses for.

    Returns:
        Generator yielding subclasses.
    """

    for sub_cls in cls.__subclasses__():
        yield sub_cls
        yield from gen_subclasses(sub_cls)


base_v = np.vectorize(np.base_repr)


def rgb_to_hex(rgb_a):
    """Converts rgba
    input values are [0, 255]

    alpha is set to zero

    returns as '#000000'

    """
    # Single value
    if isinstance(rgb_a, tuple):
        try:
            r, g, b, a = rgb_a
        except ValueError:
            r, g, b = rgb_a
        return f"#{r:02x}{g:02x}{b:02x}"

    elif isinstance(rgb_a, list):
        try:
            rgba_array = np.array(
                [[b, g, r, 0] for r, g, b, a in rgb_a], dtype=np.uint8
            )
        except ValueError:
            # todo this only works with lists of list and gives to wrong result? tests needed
            rgba_array = np.array([[b, g, r, 0] for r, g, b in rgb_a], dtype=np.uint8)

    elif isinstance(rgb_a, np.ndarray):
        # todo: allow rgb arrays
        assert rgb_a.shape[-1] == 4
        if rgb_a.data.c_contiguous:
            # todo check for c-contigious
            rgba_array = rgb_a
        else:
            rgba_array = np.array(rgb_a)
    else:
        raise TypeError(f"Invalid type for 'rgb_a': {rgb_a}")

    ints = rgba_array.astype(np.uint8).view(dtype=np.uint32).byteswap()
    padded = np.char.rjust(base_v(ints // 2 ** 8, 16), 6, "0")
    result = np.char.add("#", padded).squeeze()

    return result


def apply_cmap(pd_series_or_df: Union[pd.DataFrame, pd.Series], cmap: Colormap, norm: Optional[Normalize]=None):
    values = pd_series_or_df if norm is None else norm(pd_series_or_df)
    rgb_colors = cmap(values, bytes=True)
    hex_colors = rgb_to_hex(rgb_colors)

    if isinstance(pd_series_or_df, pd.Series):
        return pd.Series(hex_colors, index=pd_series_or_df.index)
    elif isinstance(pd_series_or_df, pd.DataFrame):
        return pd.DataFrame(
            hex_colors, index=pd_series_or_df.index, columns=pd_series_or_df.columns
        )


def make_tuple(item: Any) -> Any:
    """Takes mutable nested dicts/lists and turns them into immutable nested tuples"""
    if isinstance(item, list):
        return tuple(make_tuple(i) for i in item)
    elif isinstance(item, dict):
        return tuple((key, make_tuple(value)) for key, value in item.items())
    else:
        return item