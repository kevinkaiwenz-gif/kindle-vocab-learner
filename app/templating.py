"""Shared Jinja2 templates configuration with custom filters."""

import html as html_module

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

templates = Jinja2Templates(directory="app/templates")


def highlight_word(text: str, word: str) -> Markup:
    """Highlight a word in text with <mark> tags, safely escaping HTML."""
    escaped = html_module.escape(text)
    escaped_word = html_module.escape(word)
    highlighted = escaped.replace(escaped_word, f"<mark>{escaped_word}</mark>")
    return Markup(highlighted)


templates.env.filters["highlight"] = highlight_word
