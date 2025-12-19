"""Log shipping module for external systems."""

from .shipper import LogShipper
from .channels.local import LocalChannel

__all__ = [
    "LogShipper",
    "LocalChannel",
]
