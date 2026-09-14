import logging
import os
import sys

from idstools.utils.matplotlib_backend import (
    _configure_backend_from_cli_rc,
    _is_jupyter,
)

_configure_backend_from_cli_rc()

import matplotlib  # noqa: E402 - backend env must be set before importing matplotlib

import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger("module")

PROVENANCE_TITLE_STYLE = {"fontsize": 8, "fontweight": "normal"}

current_directory = os.path.abspath(os.path.dirname(__file__))
# reach to `share` directory (sys.prefix won't work if using --prefix option)
share_directory = os.path.abspath(os.path.join(current_directory, "../../../../../"))
mplstyle_filepath = os.path.join(share_directory, r"share/styles/scientific.mplstyle")

if os.path.exists(mplstyle_filepath):
    plt.style.use(mplstyle_filepath)
else:
    plt.style.use(os.path.join(current_directory, r"styles/scientific.mplstyle"))


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty, pprint

    rich_available = True
except ImportError:
    rich_available = False


class PlotCanvas:
    # https://matplotlib.org/stable/tutorials/intermediate/arranging_axes.html

    def __init__(self, nrows=1, ncols=1, *args, **kwargs) -> None:
        # self.fig, self.axes_array = plt.subplots(nrows, ncols)
        self.nrows = nrows
        self.ncols = ncols
        self.fig = plt.figure(*args, **kwargs)
        self.fig.subplots_adjust(hspace=0.5, wspace=0.5)

    # Share axes
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/shared_axis_demo.html#sphx-glr-gallery-subplots-axes-and-figures-shared-axis-demo-py
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/share_axis_lims_views.html#sphx-glr-gallery-subplots-axes-and-figures-share-axis-lims-views-py
    def add_axes(
        self,
        title=None,
        xlabel=None,
        ylabel=None,
        row=0,
        col=0,
        rowspan=1,
        colspan=1,
        **kwargs,
    ):
        """
        Add a new subplot axes to the figure at a specified grid position.

        Creates a subplot at the given row/column location with optional spanning
        across multiple grid cells. Automatically sets title and axis labels if provided.

        Args:
            title (str, optional): Title for the axes. Defaults to None.
            xlabel (str, optional): Label for the x-axis. Defaults to None.
            ylabel (str, optional): Label for the y-axis. Defaults to None.
            row (int, optional): Row index in the grid (0-indexed). Defaults to 0.
            col (int, optional): Column index in the grid (0-indexed). Defaults to 0.
            rowspan (int, optional): Number of rows this axes spans. Defaults to 1.
            colspan (int, optional): Number of columns this axes spans. Defaults to 1.
            kwargs: Additional keyword arguments passed to plt.subplot2grid().

        Returns:
            matplotlib.axes.Axes: The created axes object for plotting.

        Examples:
            >>> canvas = PlotCanvas(nrows=2, ncols=2)
            >>> ax = canvas.add_axes(title="Main Plot", xlabel="X", ylabel="Y", row=0, col=0)
            >>> ax.plot([1, 2, 3], [1, 4, 9])
        """
        ax = plt.subplot2grid(
            shape=(self.nrows, self.ncols),
            loc=(row, col),
            rowspan=rowspan,
            colspan=colspan,
            fig=self.fig,
            **kwargs,
        )
        if title is not None:
            ax.set_title(title)
        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
        return ax

    def save(
        self,
        fname,
        width=11.69,
        height=8.27,
        dpi="figure",
    ):
        """
        Save the current matplotlib figure to a file.

        Saves the figure with specified dimensions and resolution. Supports all
        matplotlib-compatible file formats (PDF, PNG, SVG, etc.) based on file extension.

        Args:
            fname (str): Output filename (e.g., 'figure.pdf', 'plot.png'). The file
                extension determines the format.
            width (float, optional): Figure width in inches. Defaults to 11.69 (A4 width).
            height (float, optional): Figure height in inches. Defaults to 8.27 (A4 height).
            dpi (int or str, optional): Resolution in dots per inch. If 'figure',
                uses the default figure DPI. Defaults to 'figure'.

        Returns:
            None

        Examples:
            >>> canvas = PlotCanvas()
            >>> ax = canvas.add_axes()
            >>> ax.plot([1, 2, 3], [1, 2, 3])
            >>> canvas.save('my_plot.pdf')  # Save as PDF
            >>> canvas.save('my_plot.png', dpi=300)  # Save as PNG with high resolution
        """
        fig = plt.gcf()
        fig.set_size_inches(width, height)
        try:
            fig.savefig(fname, dpi=dpi)
            print(f"----> Figure saved to {fname}", file=sys.stderr)
        except Exception as e:
            logger.debug(f"{e}")

    def set_text(self, x=0.001, y=0.985, text="", ha="left", fontsize=7):
        """
        Add text annotation to the figure at a specific position.

        Places text at figure coordinates (independent of axes), useful for adding
        annotations, credits, or metadata to the entire figure.

        Args:
            x (float, optional): X-coordinate in figure coordinates (0=left, 1=right).
                Defaults to 0.001 (near left edge).
            y (float, optional): Y-coordinate in figure coordinates (0=bottom, 1=top).
                Defaults to 0.985 (near top).
            text (str, optional): Text string to display. Defaults to empty string.
            ha (str, optional): Horizontal alignment ('left', 'center', 'right').
                Defaults to 'left'.
            fontsize (int, optional): Font size in points. Defaults to 7.

        Returns:
            None

        Examples:
            >>> canvas = PlotCanvas()
            >>> canvas.set_text(x=0.5, y=0.95, text="Main Title", ha="center", fontsize=14)
        """
        plt.figtext(
            x,
            y,
            text,
            ha=ha,
            fontsize=fontsize,
        )

    def set_sup_title(self, text="", *args, **kwargs):
        """
        Set the super-title (title spanning all subplots) for the figure.

        Args:
            text (str, optional): Super-title text. Defaults to empty string.
            args: Positional arguments passed to matplotlib's suptitle().
            kwargs: Keyword arguments (e.g., fontsize, color) passed to matplotlib's suptitle().

        Returns:
            None

        Examples:
            >>> canvas = PlotCanvas(nrows=2, ncols=2)
            >>> canvas.set_sup_title("Main Figure Title", fontsize=16, fontweight='bold')
        """
        for key, value in PROVENANCE_TITLE_STYLE.items():
            kwargs.setdefault(key, value)
        kwargs.setdefault("y", 0.985)
        plt.suptitle(text, *args, **kwargs)

    def show(self, *args, **kwargs):
        """
        Display the figure in a window and maximize it if possible.

        Attempts to maximize the figure window and show it. If window resizing is not
        supported by the current matplotlib backend, the figure is displayed normally.

        Args:
            args: Positional arguments passed to plt.show().
            kwargs: Keyword arguments passed to plt.show().

        Returns:
            None

        Notes:
            Window maximization depends on the backend selected by Matplotlib.
            Some backends may not support it.

        Examples:
            >>> canvas = PlotCanvas()
            >>> ax = canvas.add_axes()
            >>> ax.plot([1, 2, 3], [1, 4, 9])
            >>> canvas.show()
        """
        backend = matplotlib.get_backend().lower()
        if _is_jupyter():
            try:
                from IPython.display import display

                display(self.fig)
                if backend not in ("widget", "ipympl", "module://ipympl.backend_nbagg"):
                    plt.close(self.fig)
            except ImportError:
                pass
            return
        wm = self.get_current_fig_manager()
        try:
            # Try to maximize the window when the active backend exposes one.
            window = wm.window
            screen_y = window.winfo_screenheight()
            screen_x = window.winfo_screenwidth()
            wm.resize(screen_x, screen_y)
        except AttributeError:
            # Backend doesn't support window resizing (e.g., 'agg', 'Qt', etc.)
            logger.debug("Window resizing not supported for current matplotlib backend")
        plt.show(*args, **kwargs)

    def get_current_fig_manager(self):
        """
        Get the current matplotlib figure manager.

        Returns the matplotlib figure manager for the active figure, which can be used
        to interact with the figure window and backend.

        Returns:
            matplotlib.backend_bases.FigureManagerBase: The current figure manager object.

        Examples:
            >>> canvas = PlotCanvas()
            >>> fig_mgr = canvas.get_current_fig_manager()
            >>> # Can access window properties, etc.
        """
        return plt.get_current_fig_manager()

    @staticmethod
    def is_axes_empty(ax):
        """
        Check if a given Matplotlib Axes object is empty.

        An Axes object is considered empty if it has no data, no lines, no patches, and no texts.

        Parameters:
        ax (matplotlib.axes.Axes): The Axes object to check.

        Returns:
        bool: True if the Axes object is empty, False otherwise.
        """
        return not ax.has_data() and len(ax.lines) == 0 and len(ax.patches) == 0 and len(ax.texts) == 0

    def remove_empty_axes(self):
        """
        Remove empty axes from the figure.

        This method iterates over all axes in the figure and removes those that are empty.
        An axis is considered empty if the `PlotCanvas.is_axes_empty` method returns True.

        Returns:
            None
        """
        for ax in self.fig.axes[:]:  # Iterate over a copy of the axes list
            if PlotCanvas.is_axes_empty(ax):
                self.fig.delaxes(ax)

    def set_style(self, style="default"):
        """
        The function `setStyle` in allows you to set different color schemes for plots using Matplotlib based
        on the specified style parameter. Available styles are vibrant, retro, muted, high-vis, contrast, bright

        Args:
            style: The `setStyle` function allows you to set different color schemes for your plots based on the
                `style` parameter you provide. Defaults to default
        """
        if style == "default":
            # Standard SciencePlots color cycle

            # Set color cycle: blue, green, yellow, red, violet, gray
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color",
                ["0C5DA5", "00B945", "FF9500", "FF2C00", "845B97", "474747", "9e9e9e"],
            )
        if style == "vibrant":
            # Vibrant color scheme
            # color-blind safe
            # from Paul Tot's website: https://personal.sron.nl/~pault/

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color",
                ["EE7733", "0077BB", "33BBEE", "EE3377", "CC3311", "009988", "BBBBBB"],
            )
        if style == "retro":
            # Retro color style

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color", ["4165c0", "e770a2", "5ac3be", "696969", "f79a1e", "ba7dcd"]
            )
        if style == "muted":
            # Muted color scheme
            # color-blind safe
            # from Paul Tot's website: https://personal.sron.nl/~pault/

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color",
                [
                    "CC6677",
                    "332288",
                    "DDCC77",
                    "117733",
                    "88CCEE",
                    "882255",
                    "44AA99",
                    "999933",
                    "AA4499",
                    "DDDDDD",
                ],
            )
        if style == "light":
            # Light color scheme
            # color-blind safe
            # from Paul Tot's website: https://personal.sron.nl/~pault/

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color",
                [
                    "77AADD",
                    "EE8866",
                    "EEDD88",
                    "FFAABB",
                    "99DDFF",
                    "44BB99",
                    "BBCC33",
                    "AAAA00",
                    "DDDDDD",
                ],
            )

        if style == "high-vis":
            # Matplotlib style for high visability plots (i.e., bright colors!!!)

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color", ["0d49fb", "e6091c", "26eb47", "8936df", "fec32d", "25d7fd"]
            ) + matplotlib.cycler("ls", ["-", "--", "-.", ":", "-", "--"])

        if style == "contrast":
            # High-contrast color scheme
            # color-blind safe
            # from Paul Tot's website: https://personal.sron.nl/~pault/

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler("color", ["004488", "DDAA33", "BB5566"])

        if style == "bright":
            # Bright color scheme
            # color-blind safe
            # from Paul Tot's website: https://personal.sron.nl/~pault/

            # Set color cycle
            matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(
                "color",
                ["4477AA", "EE6677", "228833", "CCBB44", "66CCEE", "AA3377", "BBBBBB"],
            )

    def update_style(self, param_string=""):
        """
        Updates matplotlib rcParams using a semicolon-separated string.
        Example input: "lines.linewidth=2;axes.titlesize=16"
        """
        for item in param_string.split(";"):
            if not item.strip():
                continue
            try:
                key, value = item.split("=", 1)
                key = key.strip()
                value = eval(value.strip(), {}, {})  # Convert to actual Python type
                matplotlib.rcParams[key] = value
            except Exception as e:
                print(f"Error applying rcParam '{item}': {e}")


class BasePlot:
    def database_info(self, ax, title, hostdir, shot, run, t):
        """
        Add database and shot information as text annotation to a plot axes.

        Displays metadata (host directory, shot number, run number, and time) as text
        on the right side of the plot axis. Useful for tracking the source and time
        point of plotted data.

        Args:
            ax (matplotlib.axes.Axes): The axes object to annotate.
            title (str): Title for the plot. Time information is appended to this.
            hostdir (str): Host directory or database name (e.g., 'mdsplus', 'localhost').
            shot (int): Tokamak shot number.
            run (int): Run number within the shot.
            t (float): Time point in seconds.

        Returns:
            None

        Examples:
            >>> ax = plt.gca()
            >>> plot = BasePlot()
            >>> plot.database_info(ax, "Plasma Profile", "mdsplus", 134174, 1, 0.5)
        """
        plottitle = title
        plottitle += " (t={:.3f})".format(t)
        ax.set_title(plottitle)

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        ax.text(
            xmax + 0.01 * abs(xmax),
            ymin + 0.5 * abs(ymax - ymin),
            "{0}-Shot:{1},{2}".format(hostdir, shot, run),
            horizontalalignment="left",
            verticalalignment="center",
            rotation="vertical",
            fontsize=7,
        )


class Terminal:
    tabsize = 10
    TAB = " " * 16
    LINE = "-" * 8

    def __init__(self) -> None:
        if rich_available:
            self.console = Console()

    def print(self, text, style=None, panel=False, pretty=False):
        """
        Print formatted text to the console with optional styling.

        Prints text with optional Rich library formatting and styling. If Rich is available,
        supports styled output, panels, and pretty-printing. Falls back to standard print
        if Rich is not installed.

        Args:
            text (str or dict): Text string to print, or dictionary to pretty-print.
            style (str, optional): Rich text styling (e.g., 'green', 'bold red').
                Defaults to 'green' if Rich is available.
            panel (bool, optional): If True, text is displayed in a Rich panel box.
                Ignored if Rich is unavailable. Defaults to False.
            pretty (bool, optional): If True, uses Rich Pretty formatting for better
                display of complex objects. Ignored if Rich is unavailable. Defaults to False.

        Returns:
            None

        Notes:
            - Dictionaries are automatically pretty-printed regardless of other options
            - Requires 'rich' package for advanced formatting. Falls back to standard print.
            - Set style=None to disable coloring with Rich.

        Examples:
            >>> terminal = Terminal()
            >>> terminal.print("Hello World", style="green")
            >>> terminal.print({"data": [1, 2, 3]})  # Pretty prints dict
            >>> terminal.print("Warning!", style="bold red", panel=True)
        """
        if type(text) is dict:
            pprint(text, expand_all=True)
            return
        if style is None:
            style = "green"
        if rich_available:
            if pretty:
                text = Pretty(text)
            if panel:
                text = Panel(text)
            self.console.print(text, style=style, highlight=False)
            return
        print(text)
