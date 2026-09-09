"""Configure Matplotlib before importing Matplotlib itself."""

import ast
import os
import sys


def _backend_from_cli_rc(argv):
    """Return a backend requested by a ``--rc backend=...`` option."""
    for index, argument in enumerate(argv):
        if argument == "--rc" and index + 1 < len(argv):
            rc_string = argv[index + 1]
        elif argument.startswith("--rc="):
            rc_string = argument.split("=", 1)[1]
        else:
            continue
        for item in rc_string.split(";"):
            key, separator, value = item.partition("=")
            if separator and key.strip() == "backend":
                value = value.strip()
                try:
                    value = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    pass
                return str(value)
    return None


def _configure_backend_from_cli_rc(argv=None):
    """Set ``MPLBACKEND`` from command-line rcParams before Matplotlib loads."""
    requested_backend = _backend_from_cli_rc(sys.argv if argv is None else argv)
    if requested_backend:
        os.environ["MPLBACKEND"] = requested_backend
    return requested_backend


def _is_jupyter():
    """Return True if running inside a Jupyter notebook/lab/Colab kernel."""
    try:
        from IPython import get_ipython

        shell = get_ipython()
        if shell is None:
            return False
        return shell.__class__.__name__ in ("ZMQInteractiveShell", "Shell")
    except ImportError:
        return False
