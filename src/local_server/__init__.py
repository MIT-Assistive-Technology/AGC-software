"""Local Server component.

This package hosts a local API surface for external devices to control
and query the AGC application using FastAPI.
"""

from .main import app

__all__ = ["app"]


