from __future__ import annotations
from pathlib import Path
from typing import Any, Union

import yaml
import re
import os

yaml.SafeLoader.add_constructor(u'!regexp', lambda l, n: re.compile(l.construct_scalar(n)))


def load_spec(yaml_path: Union[os.PathLike, str]) -> Any:
    """Loads an app's `yaml` spec from a file"""
    stream = Path(yaml_path).read_text(encoding='utf-8')

    spec = yaml.safe_load(stream)

    return spec
