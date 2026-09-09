import argparse
import logging
import os
import re
from datetime import datetime

from idstools.utils.matplotlib_backend import (
    _configure_backend_from_cli_rc,
    _is_jupyter,
)

_configure_backend_from_cli_rc()

logger = logging.getLogger("module")

try:
    import imaspy as imas
except ImportError:
    import imas

# default parent parser for all idstools scripts
uri_parser = argparse.ArgumentParser(add_help=False)
uri_parser.add_argument(
    "-u",
    "--uri",
    type=str,
    required=True,
    help="URI of the dataentry\t(e.g, imas:hdf5?path=./testdb or ./testpulse.nc)",
)

imas_parser = argparse.ArgumentParser(add_help=False)
imas_parser.add_argument(
    "-u",
    "--user_or_path",
    dest="user",
    type=str,
    default="public",  # os.environ["USER"],
    help="user \t\t(default=%(default)s)",
)
db_group = imas_parser.add_mutually_exclusive_group()
db_group.add_argument(
    "-d",
    "--database",
    type=str,
    default="ITER",
    help="database name \t(default=%(default)s)",
)
imas_parser.add_argument(
    "-b",
    "--backend",
    type=str,
    default="MDSPLUS",
    help="backend format \t(default=%(default)s)",
)
imas_parser.add_argument(
    "-v",
    "--version",
    type=str,
    default="3",
    help="data version \t(default=%(default)s)",
)

dbentry_parser = argparse.ArgumentParser(add_help=False, parents=[uri_parser])
dbentry_parser.add_argument(
    "--dd-update",
    action="store_true",
    help=(
        "Convert IDS to the default version of the data dictionary if enabled"
        "otherwise, use the original IDS stored on disk."
    ),
)

rcparam_parser = argparse.ArgumentParser(add_help=False, description="Plot with customizable rcParams flags")

rcparam_parser.add_argument(
    "--rc",
    type=str,
    default="",
    help="Semicolon-separated rcParams string (e.g., 'lines.linewidth=2;axes.titlesize=14')",
)
rcparam_parser.add_argument(
    "--no-provenance",
    action="store_true",
    help="Hide URI provenance information from plot titles",
)


def get_backend_id(name):
    """
    The function `get_backend_id` returns the value of the attribute from the module
    `ids_defs`.

    Args:
        name: The `name` parameter is a string representing the name of a backend system in the code.

    Returns:
        The code snippet is defining a function called `get_backend_id` that takes a parameter `name`.
    Inside the function, it uses the `getattr` function to dynamically access an attribute from the
    module `ids_defs` based on the value of `name` with the suffix "_BACKEND". The value of this
    attribute is then returned by the function.
    """
    return getattr(imas.ids_defs, f"{name}_BACKEND")


def get_slice_mode(name):
    """
    The function `get_slice_mode` returns the interpolation mode for a given name from the `ids_defs`
    module.

    Args:
        name: Thank you for providing the code snippet. Could you please provide the value of the `name`
    parameter so that I can assist you further with the `get_slice_mode` function?

    Returns:
        The `get_slice_mode` function is returning the value of the attribute with the name
    `{name}_INTERP` from the `ids_defs` module.
    """
    return getattr(imas.ids_defs, f"{name}_INTERP")


def get_details_from_uri(uri):
    """
    The function `get_details_from_uri` extracts specific details from a URI string using regular
    expressions and returns them in a dictionary format.

    Args:
        uri: The function `get_details_from_uri` takes a URI as input and extracts various parameters from
    it. The parameters it extracts are:

    Returns:
        The function `get_details_from_uri` returns a dictionary containing details extracted from the
    provided URI string. The dictionary includes information such as user, database, version, backend,
    shot, pulse, run, path, and flags indicating the presence of certain parameters.
    """
    param = {}
    user_pattern = r"user=([^;]+)"
    database_pattern = r"database=([^;]+)"
    version_pattern = r"version=(\d+)"
    backend_pattern = r"imas:(.*?)\?"
    shot_pattern = r"shot=(\d+)"
    pulse_pattern = r"pulse=(\d+)"
    run_pattern = r"run=(\d+)"
    path_pattern = r"path=([^?]+)"

    user_match = re.search(user_pattern, uri)
    database_match = re.search(database_pattern, uri)
    version_match = re.search(version_pattern, uri)
    backend_match = re.search(backend_pattern, uri)
    shot_match = re.search(shot_pattern, uri)
    pulse_match = re.search(pulse_pattern, uri)
    run_match = re.search(run_pattern, uri)
    path_match = re.search(path_pattern, uri)

    param["user"] = user_match.group(1) if user_match else None
    param["database"] = database_match.group(1) if database_match else None
    param["version"] = version_match.group(1) if version_match else None
    param["backend"] = backend_match.group(1) if backend_match else None
    shot = shot_match.group(1) if shot_match else None
    pulse = pulse_match.group(1) if pulse_match else None
    param["pulse"] = None
    if shot is not None:
        param["pulse"] = int(shot)
    elif pulse is not None:
        param["pulse"] = int(pulse)
    param["run"] = run_match.group(1) if run_match else None
    if param["backend"] is not None:
        param["backend"] = param["backend"].upper()
    if param["run"] is not None:
        param["run"] = int(param["run"])
    if path_match:
        param["path"] = path_match.group(1)
        param["pathPresent"] = True
    elif not uri.startswith("imas:"):
        param["path"] = uri
        param["pathPresent"] = True
    else:
        param["pathPresent"] = False
    param["legacyPresent"] = True
    if (
        param["run"] is None
        or param["pulse"] is None
        or param["database"] is None
        or param["backend"] is None
        or param["user"] is None
        or param["version"] is None
    ):
        param["legacyPresent"] = False

    return param


def get_title(imasargs, title="", time_value=None):
    _title = ""
    if title:
        _title += f"{title} "
    if "uri" in imasargs.__dict__ and imasargs.uri:
        param = get_details_from_uri(imasargs.uri)
        if param["pathPresent"]:
            _title += f"PATH={param['path']}"
        else:
            _title += f"(PULSE={param['pulse']},{param['run']})"
    else:
        _title += f"(PULSE={imasargs.pulse},{imasargs.run})"
    if time_value:
        _title += f" TIME:{time_value:.3f}"
    return _title


def get_file_name(imasargs, title="", time_value=None):
    tool_name = title or "plot"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{tool_name}_{timestamp}.png"


def _is_interactive_backend(canvas):
    """Return True for GUI and notebook widget backends."""
    import matplotlib

    backend = matplotlib.get_backend().lower()
    if backend in ("widget", "ipympl", "module://ipympl.backend_nbagg"):
        return True
    return getattr(canvas.fig.canvas, "required_interactive_framework", None) is not None


def show_plot(canvas, imasargs, title="", time_value=None, fname=None, show_kwargs=None):
    """Display interactive plots and save non-interactive plots automatically."""
    noninteractive = not _is_interactive_backend(canvas)
    if not imasargs.save and (_is_jupyter() or not noninteractive):
        canvas.show(**(show_kwargs or {}))
        return

    automatic_save = noninteractive and not imasargs.save
    if fname is None:
        fname = get_file_name(imasargs, title, time_value)
    if automatic_save:
        extension = canvas.fig.canvas.get_default_filetype()
        fname = f"{os.path.splitext(fname)[0]}.{extension}"
    if imasargs.directory:
        os.makedirs(imasargs.directory, exist_ok=True)
        fname = os.path.join(imasargs.directory, fname)
    if automatic_save:
        import matplotlib

        logger.info(
            "Non-interactive Matplotlib backend '%s' detected; saving figure to %s",
            matplotlib.get_backend(),
            fname,
        )
    canvas.save(fname)


def get_database_path(imasargs, time_value=None) -> str:
    """
    The function `get_database_path` returns the absolute path of a database based on the provided arguments.

    Args:
        imasargs: The `imasargs` parameter is an object or dictionary that contains the following attributes:

    Returns:
        the absolute path of the database.
    """
    if getattr(imasargs, "no_provenance", False):
        return ""

    pulse_info = ""
    database_absolute_path = ""
    if "uri" in imasargs.__dict__ and imasargs.uri:
        database_absolute_path = imasargs.uri

    else:
        if imasargs.user == "public":
            publichome = os.getenv("IMAS_HOME", default="")
            if publichome is None:
                return None
            database_absolute_path = (
                f"{publichome}/shared/imasdb/{imasargs.database}/{imasargs.version}/{imasargs.run // 10000}"
            )
        else:
            database_absolute_path = (
                f'{os.path.expanduser(f"~{imasargs.user}")}/public/imasdb/'
                f"{str(imasargs.database)}/{imasargs.version}/{imasargs.run // 10000}"
            )
        pulse_info = f"pulse {imasargs.pulse},{imasargs.run}"
        database_absolute_path = database_absolute_path[:-2]
    time_string = ""
    if time_value:
        time_string = f"time:{time_value:.3f}"
    hostdir = f"{database_absolute_path} "
    if pulse_info:
        hostdir += f"({pulse_info})"
    if time_string:
        hostdir += f"#{time_string}"
    return hostdir
