"""SOUNDTRACKER - Sistema de investigación de compositores de cine.

Este paquete proporciona herramientas para:
- Obtener información de compositores desde múltiples APIs
- Generar perfiles completos en Markdown
- Construir rankings Top 10 de bandas sonoras
- Gestionar filmografías y premios
"""

from soundtracker.config import Settings, get_settings, settings
from soundtracker.logging_config import get_logger, setup_logging
from soundtracker.models import Award, AwardStatus, ComposerInfo, ExternalSource, Film

__version__ = "2.0.0"
__author__ = "SOUNDTRACKER Team"

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Logging
    "get_logger",
    "setup_logging",
    # Models
    "Award",
    "AwardStatus",
    "ComposerInfo",
    "ExternalSource",
    "Film",
]
