"""The function under test for the no-dependency recipe."""
import re
import unicodedata


def slugify(text: str) -> str:
    """Lowercase ASCII words joined by hyphens: 'Hello, World!' -> 'hello-world'."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
