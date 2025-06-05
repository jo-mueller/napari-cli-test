
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .function import threshold_otsu, threshold_mean, threshold_manual
from .main import make_cli_executable

__all__ = (
    "threshold_otsu",
    "threshold_mean",
    "threshold_manual",
    "make_cli_executable",
    )