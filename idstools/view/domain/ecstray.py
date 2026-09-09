import logging

import matplotlib.pyplot as plt

from idstools.compute.equilibrium import EquilibriumCompute
from idstools.domain.ecstray import EcStrayCompute

# Font/Colour definition
bndcolor = "chocolate"
shotcolors = ["b", "r", "c", "y", "m", "b"]
shotstyle = ["-", "--", "-.", ":", ".", ","]
colorcounter = 0
lpad = -1

logger = logging.getLogger("module")


class EcStrayView:
    def __init__(self, equilibrium_ids: object, core_profiles_ids: object, waves_ids: object):
        self.ecstray_object = EcStrayCompute(equilibrium_ids, core_profiles_ids, waves_ids)
        self.equilibrium_compute = EquilibriumCompute(equilibrium_ids)
        self.equilibrium_ids = equilibrium_ids
        self.core_profiles_ids = core_profiles_ids
        self.waves_ids = waves_ids

    def plot_resonance_layer(self, ax, coherent_wave_index, time_slice, init=1, verbose=False):
        """
        Plot the resonance layer on the given `ax` object.

        Args:
            ax (matplotlib.axes.Axes): The matplotlib Axes object on which the resonance layer will be plotted.
            time_slice (int): The time slice for accessing wave-related data.
            init (int): Indicates if the function is called for the initial setup. Set to 1 for initial setup.
                Default is 1.
            verbose (bool): Controls whether verbose output should be displayed. Default is False.

        Returns:
            matplotlib.lines.Line2D: The Line2D object representing the resonance layer plot.

        Example:
            .. code-block:: python

                from idstools.view.domain.ecstray import EcStrayView
                import imas
                from idstools.view.common import PlotCanvas

                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3", "r")
                connection.open()
                equilibriumIds = connection.get('equilibrium')
                wavesIds = connection.get('waves')
                coreProfilesIds = connection.get('core_profiles')

                canvas = PlotCanvas(1, 1) # create canvas
                ax = canvas.add_axes(title="Resonance Layer", xlabel="R [m]", ylabel="Z [m]", row=0, col=0, rowspan=1)
                ax.set_title("uri=imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3")
                ecstrayView = EcStrayView(equilibriumIds, coreProfilesIds, wavesIds)
                ecstrayView.plot_resonance_layer(ax, time_slice_wv=0, time_slice_eq=0, verbose=True)

                ax.plot()
                canvas.show()

            .. image:: /_static/images/EcstrayView_plotResonanceLayer.png
                        :alt: image not found
                        :align: center

        See also:
            :func:`idstools.domain.ecstray.EcStrayCompute.get_resonance_layer`

        """
        result_dict = self.ecstray_object.get_resonance_layer(coherent_wave_index, time_slice)
        res_layer = result_dict["resonance_layer"]

        for i_harm in range(len(res_layer)):
            if len(res_layer[i_harm]["r"]) > 1:
                if verbose:
                    print("Resonance at n = %i" % (i_harm + 1))
                if init == 1:
                    (ax_polview_plot_res,) = ax.plot(
                        res_layer[i_harm]["r"],
                        res_layer[i_harm]["z"],
                        color="r",
                    )
                    return ax_polview_plot_res
                else:
                    ax.set_data(res_layer[i_harm]["r"], res_layer[i_harm]["z"])

    def plot_poloidal_view(self, ax, coherent_wave_index, time_slice, equilibrium_time_slice=None):
        n_harm = [1, 2, 3, 4]
        if equilibrium_time_slice is None:
            equilibrium_time_slice = time_slice

        resonance_data = self.ecstray_object.get_resonance_layer(
            coherent_wave_index,
            time_slice,
            n_harm=n_harm,
            equilibrium_time_slice=equilibrium_time_slice,
        )
        profile2d_index = resonance_data["profile2d_index"]
        resonance_layer = resonance_data["resonance_layer"]

        grid_data = self.equilibrium_compute.get2d_cartesian_grid(equilibrium_time_slice, profile2d_index)
        r2d = grid_data["r2d"]
        z2d = grid_data["z2d"]
        psi2d = grid_data["psi2d"]
        phi2d = self.equilibrium_compute.get_phi2d(equilibrium_time_slice, profile2d_index)

        # Poloidal view plot
        contour_lines = ax.contour(r2d, z2d, psi2d.T, 50, cmap="summer")
        cbar_psi = plt.colorbar(contour_lines, ax=ax, orientation="horizontal", pad=0.08, fraction=0.03)
        cbar_psi.set_label(r"$\psi$ [Wb]")
        if phi2d is not None and len(phi2d) > 0:
            contour_lines_rho = ax.contour(r2d, z2d, phi2d.T, 50, cmap="YlOrBr")
            cbar_rho = plt.colorbar(contour_lines_rho, ax=ax, orientation="horizontal", pad=0.08, fraction=0.03)
            cbar_rho.set_label(r"$\Phi$ [Wb]")
        # ax_polview.set_xlim(r2d.min(),r2d.max())
        ax.set_title("Poloidal view (R,Z)")
        ax.set_xlabel("R [m]", labelpad=lpad)
        ax.set_ylabel("Z [m]", labelpad=lpad)
        ax.set_xlim(3.4, r2d.max())
        ax.set_ylim(z2d.min() * 0.7, z2d.max() * 0.7)
        ax.set_aspect("equal", adjustable="box")
        for i_harm in range(len(n_harm)):
            if len(resonance_layer[i_harm]["r"]) > 1:
                logger.info(f"Resonance at n = {i_harm}")
                ax.plot(
                    resonance_layer[i_harm]["r"],
                    resonance_layer[i_harm]["z"],
                    color="r",
                )

    def plot_cut_off_layer(
        self,
        ax,
        coherent_wave_index,
        time_slice,
        init=1,
        verbose=False,
    ):
        """
        Plot the cutoff layer on the given `ax` object.

        Args:
            ax (matplotlib.axes.Axes): The matplotlib Axes object on which the cutoff layer will be plotted.
            time_slice (int): The time index for accessing wave-related data. Default is 0.
            init (int): Indicates if the function is called for the initial setup. Set to 1 for initial setup.
                Default is 1.
            verbose (bool): Controls whether verbose output should be displayed. Default is False.

        Returns:
            matplotlib.lines.Line2D: The Line2D object representing the cutoff layer plot.

        Example:
            .. code-block:: python

                from idstools.view.domain.ecstray import EcStrayView
                import imas
                from idstools.view.common import PlotCanvas

                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3", "r")
                connection.open()
                equilibriumIds = connection.get('equilibrium')
                wavesIds = connection.get('waves')
                coreProfilesIds = connection.get('core_profiles')

                canvas = PlotCanvas(1, 1) # create canvas
                ax = canvas.add_axes(title="Resonance Layer", xlabel="R [m]", ylabel="Z [m]", row=0, col=0, rowspan=1)
                ax.set_title("uri=imas:mdsplus?user=public;pulse=134173;run=2326;database=TEST;version=3")
                ecstrayView = EcStrayView(equilibriumIds, coreProfilesIds, wavesIds)
                ecstrayView.plot_cut_off_layer(ax, time_slice=0,verbose=True)

                ax.plot()
                canvas.show()

            .. image:: /_static/images/EcstrayView_plotCutOffLayer.png
                :alt: image not found
                :align: center

        See also:
            :func:`idstools.domain.ecstray.EcStrayCompute.getCutoffLayer`
        """
        # Calculate density cutoff layer position
        cutoff_layer = self.ecstray_object.get_cutoff_layer(coherent_wave_index, time_slice)

        # TODO Work on this function to keep call back function and events and not to pass init=1
        if init == 1:
            (ax_polview_plot_cut,) = ax.plot(cutoff_layer["r"], cutoff_layer["z"], color="g")
            return ax_polview_plot_cut
        else:
            ax.set_data(cutoff_layer["r"], cutoff_layer["z"])
