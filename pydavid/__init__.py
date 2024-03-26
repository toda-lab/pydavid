# pydavid: A simple Python interface of Open-David

import importlib.metadata

__version__ = importlib.metadata.version(__package__)

from .pydavid import OpenDavid

__all__ = [
    "OpenDavid",
]
