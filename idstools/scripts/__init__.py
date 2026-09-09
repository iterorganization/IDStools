"""
CLI script entry points for idstools.

These modules provide command-line entry points for the visualization and
analysis tools. Each entry point corresponds to a script in the bin/ directory
within this package, which is included in the installed package data.
"""

import os


def _load_script_main(script_name):
    """
    Load and execute a packaged script as a main function.

    The scripts are stored in the bin/ subdirectory of this package and are
    included as package data, so they are always available at a fixed path
    relative to this module regardless of how the package was installed.

    Args:
        script_name (str): Name of the script file

    Returns:
        function: A callable that executes the script's main logic
    """
    script_path = os.path.join(os.path.dirname(__file__), "bin", script_name)

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    def main():
        """Execute the script's main function."""
        import builtins

        with open(script_path, "r", encoding="utf-8") as f:
            script_code = f.read()
        namespace = {"__name__": "__main__", "__file__": script_path, "__builtins__": builtins}
        try:
            exec(script_code, namespace)
        except SystemExit:
            raise

    return main


# Create wrapper functions for each script
def plotequilibrium():
    """Plot plasma equilibrium from equilibrium IDS."""
    _load_script_main("plotequilibrium")()


def idslist():
    """List IDS shots and runs from a database."""
    _load_script_main("idslist")()


def idsprint():
    """Print IDS structure and data."""
    _load_script_main("idsprint")()


def idsperf():
    """Analyze and display IDS performance metrics."""
    _load_script_main("idsperf")()


def plothcd():
    """Plot heating and current drive data."""
    _load_script_main("plothcd")()


def plotpressure():
    """Plot pressure profiles."""
    _load_script_main("plotpressure")()


def plotrotation():
    """Plot rotation and velocity profiles."""
    _load_script_main("plotrotation")()


def plotequicomp():
    """Compare equilibrium data."""
    _load_script_main("plotequicomp")()


def plotcoresources():
    """Plot core resource data."""
    _load_script_main("plotcoresources")()


def plotcoretransport():
    """Plot core transport data."""
    _load_script_main("plotcoretransport")()


def plotkineticprofiles():
    """Plot kinetic profiles."""
    _load_script_main("plotkineticprofiles")()


def plothcdwaves():
    """Plot HCD wave data."""
    _load_script_main("plothcdwaves")()


def plotecray():
    """Plot EC ray tracing data."""
    _load_script_main("plotecray")()


def plothcddistributions():
    """Plot HCD distributions."""
    _load_script_main("plothcddistributions")()


def plotedgeprofiles():
    """Plot edge profile data."""
    _load_script_main("plotedgeprofiles")()


def plotmachinedescription():
    """Plot machine description geometry."""
    _load_script_main("plotmachinedescription")()


def plotspectrometry():
    """Plot spectrometry data."""
    _load_script_main("plotspectrometry")()


def plotneutron():
    """Plot neutron diagnostic data."""
    _load_script_main("plotneutron")()


def ploteccomposition():
    """Plot electron cyclotron composition data."""
    _load_script_main("ploteccomposition")()


def plotecstrayradiation():
    """Plot EC stray radiation."""
    _load_script_main("plotecstrayradiation")()


def plotscenario():
    """Plot scenario data."""
    _load_script_main("plotscenario")()


def idsquery():
    """Query IDS data."""
    _load_script_main("idsquery")()


def idsresample():
    """Resample IDS data."""
    _load_script_main("idsresample")()


def idsdiff():
    """Diff two IDS files."""
    _load_script_main("idsdiff")()


def idscp():
    """Copy IDS data."""
    _load_script_main("idscp")()


def idssize():
    """Display IDS size information."""
    _load_script_main("idssize")()


def idsrescale_equilibrium():
    """Rescale equilibrium data."""
    _load_script_main("idsrescale_equilibrium")()


def idsshift_equilibrium():
    """Shift equilibrium coordinates."""
    _load_script_main("idsshift_equilibrium")()


def idsrosettacode():
    """Convert between IDS formats."""
    _load_script_main("idsrosettacode")()


def eqdsk2ids():
    """Convert EQDSK file to IDS format."""
    _load_script_main("eqdsk2ids")()


def dbconverter():
    """Convert database formats."""
    _load_script_main("dbconverter")()


def dbscraper():
    """Scrape database metadata."""
    _load_script_main("dbscraper")()


def dbselector():
    """Select data from database."""
    _load_script_main("dbselector")()


def dblist():
    """List database contents."""
    _load_script_main("dblist")()


def dbperf():
    """Analyze database performance."""
    _load_script_main("dbperf")()


def printcoresources():
    """Print core resource information."""
    _load_script_main("printcoresources")()


def printplasmacompo():
    """Print plasma composition."""
    _load_script_main("printplasmacompo")()


def printfluxes():
    """Print magnetics flux values."""
    _load_script_main("printfluxes")()


def scenario_status():
    """Show scenario status."""
    _load_script_main("scenario_status")()


def scenario_summary():
    """Show scenario summary."""
    _load_script_main("scenario_summary")()


def disruption_summary():
    """Show disruption summary."""
    _load_script_main("disruption_summary")()


def create_db_entry():
    """Create database entry."""
    _load_script_main("create_db_entry")()


def create_db_entry_disruption():
    """Create disruption database entry."""
    _load_script_main("create_db_entry_disruption")()


def show_db_entry():
    """Display database entry."""
    _load_script_main("show_db_entry")()


def watch_db_entry():
    """Watch database entry for changes."""
    _load_script_main("watch_db_entry")()


def md_status():
    """Show machine description status."""
    _load_script_main("md_status")()


def md_summary():
    """Show machine description summary."""
    _load_script_main("md_summary")()


__all__ = [
    "plotequilibrium",
    "idslist",
    "idsprint",
    "idsperf",
    "plothcd",
    "plotpressure",
    "plotrotation",
    "plotequicomp",
    "plotcoresources",
    "plotcoretransport",
    "plotkineticprofiles",
    "plothcdwaves",
    "plotecray",
    "plothcddistributions",
    "plotedgeprofiles",
    "plotmachinedescription",
    "plotspectrometry",
    "plotneutron",
    "ploteccomposition",
    "plotecstrayradiation",
    "plotscenario",
    "idsquery",
    "idsresample",
    "idsdiff",
    "idscp",
    "idssize",
    "idsrescale_equilibrium",
    "idsshift_equilibrium",
    "idsrosettacode",
    "eqdsk2ids",
    "dbconverter",
    "dbscraper",
    "dbselector",
    "dblist",
    "dbperf",
    "printcoresources",
    "printplasmacompo",
    "printfluxes",
    "scenario_status",
    "scenario_summary",
    "disruption_summary",
    "create_db_entry",
    "create_db_entry_disruption",
    "show_db_entry",
    "watch_db_entry",
    "md_status",
    "md_summary",
]


def register_magics():
    """
    Register all idstools CLI tools as IPython line magics.

    After calling this, you can use ``%plotequilibrium``, ``%idslist``, etc.
    directly in Jupyter/Colab cells instead of ``!plotequilibrium``.

    This is called automatically when ``idstools.scripts`` is imported inside
    a Jupyter or Colab kernel.

    Examples:
        >>> import idstools.scripts  # magics auto-registered in Jupyter/Colab
        >>> # Then in a cell:
        >>> # %plotequilibrium -u "iter_scenario_53298_seq1_DD4.nc"
    """
    try:
        import shlex
        import sys
        from IPython import get_ipython

        ip = get_ipython()
        if ip is None:
            return

        for name in __all__:

            def _make_magic(magic_name):
                def magic_fn(line):
                    orig_argv = sys.argv[:]
                    try:
                        sys.argv = [magic_name] + (shlex.split(line) if line.strip() else [])
                        _load_script_main(magic_name)()
                    except SystemExit:
                        pass
                    finally:
                        sys.argv = orig_argv

                magic_fn.__name__ = magic_name
                return magic_fn

            ip.register_magic_function(_make_magic(name), magic_kind="line", magic_name=name)

    except ImportError:
        pass
