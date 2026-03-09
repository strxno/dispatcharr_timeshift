"""
Dispatcharr Timeshift Plugin

GitHub: https://github.com/cedric-marcoux/dispatcharr_timeshift

Note: Auto-install logic is in plugin.py (which Dispatcharr imports directly).
"""

from .plugin import Plugin, _read_plugin_version

__all__ = ['Plugin']
__version__ = _read_plugin_version()
