try:
    from _version import __version__
except ImportError:
    from ._version import __version__

try:
    from loginpath import get_login_info
except ImportError:
    from .loginpath import get_login_info

__all__ = ["exception", "ip_parser", "loginpath", "my_print_defaults"]
