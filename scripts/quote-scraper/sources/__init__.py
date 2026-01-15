"""Quote sources package."""
from .base import BaseSource
from .gutenberg import GutenbergSource
from .scripts import ScriptSource

__all__ = ["BaseSource", "GutenbergSource", "ScriptSource"]
