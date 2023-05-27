"""Top-level entry-point for the <project_name> package"""

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__: str = version("lsl-relay")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
