"""FalconSignals CLI package."""

# Import commands to register them with the app
import src.cli.commands  # noqa: F401
from src.cli.app import app

__all__ = ["app"]
