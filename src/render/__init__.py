"""Render trip plans as Markdown or terminal-friendly text."""

from src.render.markdown import render_trip_markdown
from src.render.terminal import render_trip_terminal

__all__ = ["render_trip_markdown", "render_trip_terminal"]
