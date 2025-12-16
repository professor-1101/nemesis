"""Log shipping module for external systems."""

from .manager import ShippingManager
from .channels.local import LocalChannel

__all__ = [
    "ShippingManager",
    "LocalChannel",
]
