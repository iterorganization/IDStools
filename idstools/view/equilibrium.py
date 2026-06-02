"""
This module provides view functions and classes for equilibrium ids data

`refer data dictionary <https://imas-data-dictionary.readthedocs.io/en/latest/>`_.

"""

import copy
import logging

try:
    import imaspy as imas
except ImportError:
    import imas
import matplotlib.pyplot as plt
import numpy as np

from idstools.compute.equilibrium import EquilibriumCompute
from idstools.view.common import BasePlot

logger = logging.getLogger("module")


class EquilibriumView(BasePlot):
    def __init__(self, ids: object):
        """
        This is a constructor function that initializes an object with an input object and creates
        another object using the input object.

        Args:
            ids (object): The parameter `ids` is an object that is being passed to the constructor
                of the class. It is not clear from the code snippet what type of object it is, but it is being
                stored as an instance variable `self.ids`.
        """
        self.ids = ids
        self.compute_obj = EquilibriumCompute(ids)

    def view_magnetic_poloidal_flux(
        self,
        ax: plt.axes,
        time_slice: int,
        profiles2d_index: int = 0,
        plot_rho: bool = False,
    ):
        """
        This function plots the magnetic poloidal flux contours on a 2D Cartesian grid.

        Args:
            ax: `ax` is a matplotlib axis object on which the magnetic poloidal flux contour plot will be drawn.

        Example:
            .. code-block:: python

                import imas
                from idstools.view.equilibrium import EquilibriumView
                from idstools.view.common import PlotCanvas

                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3","r")
                connection.open()
                idsObj = connection.get('equilibrium')

                canvas = PlotCanvas(1, 1) # create canvas
                ax = canvas.add_axes(title="", xlabel="", row=0, col=0)

                viewObj = EquilibriumView(idsObj)
                viewObj.viewMagneticPoloidalFlux(ax) # plot contour on the canvas axes

                ax.set_title("uri=imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3")
                ax.plot()
                canvas.show()

            .. image:: /_static/images/EquilibriumView_viewMagneticPoloidalFlux.png
                :alt: image not found
                :align: center

        See also:
            :func:`idstools.compute.equilibrium.EquilibriumCompute.get2DCartesianGrid`
            :func:`idstools.compute.equilibrium.EquilibriumCompute.getRho2D`

            :meth:`plotIP`
        """
        contour_lines_psi = contour_lines_rho = None
        cartestion_grid = self.compute_obj.get2d_cartesian_grid(time_slice, profiles2d_index)
        if cartestion_grid is not None:
            levels = 50

            # As per IMAS data dictionary psi is stored as [R, Z] with shape (N_R, N_Z).
            # Check this reference :
            # https://imas-data-dictionary.readthedocs.io/en/latest/generated/identifier/poloidal_plane_coordinates_identifier.html

            # For matplotlib contour as per the documentation:
            # https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.contour.html
            # matplotlib.contour(r, z, Zdata) expects Zdata as [rows=z, cols=r], so the shape must be (N_Z, N_R).
            # Therefore we transpose psi before plotting.
            contour_lines_psi = ax.contour(
                cartestion_grid["r2d"], cartestion_grid["z2d"], cartestion_grid["psi2d"].T, levels, cmap="summer"
            )
            # ax.clabel(
            #     contour_lines_psi,
            #     colors="black",
            #     inline=False,
            #     fontsize=10,
            #     # fmt="%.2e",
            #     inline_spacing=1,
            # )
            if plot_rho:
                rho2d = self.compute_obj.get_rho2d(time_slice)
                if rho2d is not None:
                    contour_lines_rho = ax.contour(
                        cartestion_grid["r2d"], cartestion_grid["z2d"], rho2d, levels=levels, cmap="YlOrBr"
                    )

            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("$R$ [m]")
            ax.set_ylabel("$Z$ [m]")
            # ax.set_xlim(3.4, cartestionGrid["r2d"].max())
            # ax.set_ylim(cartestionGrid["z2d"].min() * 0.7, cartestionGrid["z2d"].max() * 0.7)
        return contour_lines_psi, contour_lines_rho

    def view_pulse_info(self, ax: plt.axes, title: str, hostdir: str, shot: int, run: int, t: float):
        self.database_info(ax, title, hostdir, shot, run, t)

    def plot_ip(self, ax):
        """
        This function plots the plasma current over time on a given axis.

        Args:
            ax: The parameter "ax" is a matplotlib axis object.
        """
        plasma_current = self.compute_obj.get_ip()
        time_array = self.ids.time
        if len(plasma_current) <= 3:
            ax.plot(time_array, plasma_current, color="b", marker="o", label="$I_p$ [MA]")
        else:
            ax.plot(time_array, plasma_current, color="b", label="$I_p$ [MA]")
        if len(time_array) != 1:
            ax.set_xlim(min(time_array), max(time_array))
        # ax_waveform.set_ylim(0,max(plasmaCurrent)*1.2)
        ax.legend(
            bbox_to_anchor=(1.0, 0.5),
            loc="center left",
            borderaxespad=0.0,
            frameon=False,
        )
        ax.set_ylim(0, 20)

    def plot_poloidal_equilibrium(self, ax, time_slice: int):
        """
        This function plots a poloidal equilibrium contour plot using flux surface quantities extracted from the
        equilibrium.

        Args:
            ax: `ax` is a matplotlib axis object.
            time_slice (int): time_slice is an integer index.

        Returns:
            the contour plot object `cntr`.
        """
        # Extract flux surface quantities from equilibrium
        data = self.compute_obj.get_flux_surfaces(time_slice)
        r2d = data["r2d"]
        z2d = data["z2d"]
        # rho2d = data["rho2d"]
        psi2d = data["psi2d"]
        cntr = ax.contour(r2d, z2d, psi2d, 50, cmap="summer")
        cbar = plt.colorbar(cntr, ax=ax, pad=0.08, fraction=0.03)
        cbar.set_label(r"$\psi$ [Wb]")
        # if len(rho2d)>0:
        #    cntr = ax.contour(r2d,z2d,rho2d,50,cmap='YlOrBr')

        # ax_polview.set_xlim(r2d.min(),r2d.max())
        ax.set_xlim(3.4, r2d.max())
        ax.set_ylim(z2d.min() * 0.7, z2d.max() * 0.7)
        ax.set_aspect("equal", adjustable="box")

        return cntr

    def plot_topplotequilibrium(self, ax, time_slice, label="Plasma Boundaries"):
        """
        This function plots the top view equilibrium of a plasma and updates the plot if specified.

        Args:
            ax: `ax` is a matplotlib axis object.
            time_slice: The time index is an integer

        Returns:
            list containing two plot objects: ax_topview_plot_eq1 and ax_topview_plot_eq2.
        """
        # TODO: Refactor update mechanism of the plot
        data = self.compute_obj.get_top_view(time_slice)
        bndcolor = "chocolate"
        colorcounter = 0

        if colorcounter == 1:
            ax.plot(
                data["xpla"],
                data["ypla"],
                color=bndcolor,
                label=label,
            )
        else:
            ax.plot(data["xpla"], data["ypla"], color=bndcolor)
        ax.plot(data["xplap"], data["yplap"], color=bndcolor)
        ax.set_xlim((-data["r0"] - data["amin"]) * 1.1, (data["r0"] + data["amin"]) * 1.1)
        ax.set_aspect("equal", adjustable="box")

    def plotequilibrium(self, ax, time_slice):
        quantities = self.compute_obj.get2d_cartesian_grid(time_slice)
        if quantities is not None:
            r2d, z2d, psi2d = (
                quantities["r2d"],
                quantities["z2d"],
                quantities["psi2d"],
            )
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position("top")

            contour_lines = ax.contour(r2d, z2d, psi2d.T, levels=50, cmap="summer")  # ,label=r'$\Psi_{pol}$')
            cbar = plt.colorbar(contour_lines, ax=ax, pad=0.08, fraction=0.03)
            cbar.set_label(r"$\psi$ [Wb]")
            ax.set_xlim(r2d.min(), r2d.max())
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("R (m)")
            ax.set_ylabel("Z (m)")

            ax.set_xlabel("$R\\/\\mathrm{[m]}$")
            ax.set_ylabel(r"$Z\/\mathrm{[m]}$")
            ax.set_title("2D equilibrium")
        else:
            ax.text(0.2, 0.5, "2D equilibrium")
            ax.text(0.2, 0.45, "not available")

    def plot_profiles_1d_quantities(self, axes_list, time_slice, attributes=None):
        quantities = self.compute_obj.get_profiles_1d_quantities(time_slice, attributes)
        if not quantities:
            return
        counter = 0
        for name, field in quantities.items():
            if field.has_value:
                copied_field = copy.deepcopy(field)
                if isinstance(copied_field.value, np.floating) or isinstance(copied_field.value, np.ndarray):
                    copied_field[copied_field == imas.ids_defs.EMPTY_FLOAT] = np.nan
                if np.all(np.isnan(copied_field.value)):
                    continue
                coordinate = coordinate_normalized = copied_field.coordinates[0]
                if coordinate.metadata.name == "psi":
                    psi_norm_attr = getattr(self.ids.time_slice[time_slice].profiles_1d, "psi_norm", None)
                    if psi_norm_attr and psi_norm_attr.has_value:
                        coordinate_normalized = psi_norm_attr
                    else:
                        logger.warning("psi_norm not found in the ids, using normalized psi..")
                        psi = coordinate
                        psi_first = psi[0]
                        psi_last = psi[-1]

                        coordinate_normalized = (psi - psi_first) / (psi_last - psi_first)
                axes_list[counter].plot(
                    coordinate_normalized, copied_field, label=f"{field.metadata.name} ({field.metadata.units})"
                )
                if coordinate.metadata.name == "psi":
                    axes_list[counter].set_xlabel(f"{coordinate.metadata.name} (normalized)")
                else:
                    axes_list[counter].set_xlabel(f"{coordinate.metadata.name} ({coordinate.metadata.units})")
                axes_list[counter].set_ylabel(name)
                axes_list[counter].legend(loc="upper right")
                counter = counter + 1

    def plot_global_quantities(self, axes_list, time_slice, attributes=None):
        quantities = self.compute_obj.get_global_quantities(time_slice, attributes)
        if not quantities:
            return
        counter = 0
        for name, field in quantities.items():
            if isinstance(field["node"], np.floating) or isinstance(field["node"], np.ndarray):
                field["node"][field["node"] == imas.ids_defs.EMPTY_FLOAT] = np.nan
            if field["has_value"]:
                if len(field["node"]) < 5:
                    axes_list[counter].scatter(field["coordinate"], field["node"], label=f"{name} ({field['unit']})")
                else:
                    axes_list[counter].plot(field["coordinate"], field["node"], label=f"{name} ({field['unit']})")
                axes_list[counter].set_xlabel(f"{field['coordinate_name']} ({field['coordinate_unit']})")
                axes_list[counter].set_ylabel(name)
                self.view_time_line(axes_list[counter], time_slice)
                axes_list[counter].legend(loc="upper right")
                counter = counter + 1

    def view_time_line(self, ax, time):
        """
        The function `view_time_line` plots a vertical dashed line on a given matplotlib axis at a specified time.

        Args:
            ax: The parameter "ax" is a reference to the second y-axis of a matplotlib figure. It is used to plot
                the timeline on the same figure as the other data.
            time: The "time" parameter is the value at which you want to plot a vertical line on the timeline. It
                represents the specific point in time that you want to highlight on the timeline.
        """
        ymin, ymax = ax.get_ylim()
        ax.plot(
            [time, time],
            [ymin, ymax],
            color="gray",
            linestyle="--",
            linewidth=1,
            label=r"$t_{slice}$",
        )
        # ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_ylim(ymin, ymax)

    def show_info_on_plot(self, ax, info: str = "", location="right"):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ax.text(
            (xmax) + 0.2,
            (ymax / 4) + 0.01,
            info,
            verticalalignment="center",
            rotation="vertical",
            fontsize=6,
        )

    def _get_profile(self, jtor2D, z, time_index1, jtor2DE=None, zE=None, time_index2=None):
        #
        #  sets up parameters for the profile plot on the mid-plane
        #
        new_y11 = None
        new_y12 = None
        y_min = +1e80
        y_max = -1e80

        #  work out index for mid-plane (z=0), or thereabouts...
        targetZValue = 0
        diff = np.abs(z - targetZValue)
        k = np.argmin(diff)
        kE = None
        if zE is not None:
            diff = np.abs(zE - targetZValue)
            kE = np.argmin(diff)

        try:
            new_y11 = jtor2D[time_index1, :, k]
            y_min = new_y11.min()
            y_max = new_y11.max()
        except Exception as e:
            logger.error(f"Exception occurred, detailed error {e}")
        try:
            if kE:
                new_y12 = jtor2DE[time_index2, :, kE]
                y_min = min(y_min, new_y12.min())
                y_max = max(y_max, new_y12.max())
        except Exception as e:
            logger.error(f"Exception occurred, detailed error {e}")

        delta = (y_max - y_min) * 0.03
        y_min -= delta
        y_max += delta
        yabs = max(abs(y_max), abs(y_min))
        if yabs < 1e-3:
            scal = 1e-3
            scalStr = "m"
        elif yabs < 1e3:
            scal = 1
            scalStr = ""
        elif yabs < 1e6:
            scal = 1e3
            scalStr = "k"
        else:
            scal = 1e6
            scalStr = "M"
        if new_y11 is not None:
            new_y11 /= scal
        if new_y12 is not None:
            new_y12 /= scal
        y_min /= scal
        y_max /= scal
        return new_y12, new_y11, y_min, y_max, scalStr

    def view_profile_plot(self, ax, time_index1, equilibrium2_ids=None, time_index2=None):
        data = self.compute_obj.get_equilibria(selection=["name", "jtor2D", "r", "z"])
        data2 = None
        if equilibrium2_ids is not None:
            compute_obj2 = EquilibriumCompute(equilibrium2_ids)
            data2 = compute_obj2.get_equilibria(selection=["name", "jtor2D", "r", "z"])
            nameE = data2["name"]
            jtor2DE = data2["jtor2D"]
            rE = data2["r"]
            zE = data2["z"]
        name = data["name"]
        jtor2D = data["jtor2D"]
        r = data["r"]
        z = data["z"]

        # Debug logging
        logger.debug(f"jtor2D shape: {jtor2D.shape if jtor2D is not None else 'None'}")
        logger.debug(f"jtor2D[{time_index1}] min: {np.min(jtor2D[time_index1]) if jtor2D is not None else 'N/A'}")
        logger.debug(f"jtor2D[{time_index1}] max: {np.max(jtor2D[time_index1]) if jtor2D is not None else 'N/A'}")
        if equilibrium2_ids and jtor2DE is not None:
            logger.debug(f"jtor2DE shape: {jtor2DE.shape}")
            logger.debug(f"jtor2DE[{time_index2}] min: {np.min(jtor2DE[time_index2])}")
            logger.debug(f"jtor2DE[{time_index2}] max: {np.max(jtor2DE[time_index2])}")
        if data2:
            new_y12, new_y11, y_min, y_max, scaleStr = self._get_profile(
                jtor2D, z, time_index1, jtor2DE, zE, time_index2
            )
            (line12,) = ax.plot([], color="blue", label=" ")

            line12.set_label(nameE + " [$run_2$]")

            if rE is not None and new_y12 is not None:
                line12.set_xdata(rE)
                line12.set_ydata(new_y12)

                # Check if data is all zeros or near-zero
                if np.allclose(new_y12, 0.0, atol=1e-10):
                    logger.warning(f"Equilibrium2 {nameE}: jtor profile is all zeros or near-zero")
            else:
                logger.warning(f"Equilibrium2 {nameE}: No valid r or jtor data available")
        else:
            new_y12, new_y11, y_min, y_max, scaleStr = self._get_profile(jtor2D, z, time_index1)

        (line11,) = ax.plot([], color="green", label=" ")
        line11.set_label(name + " [$run_1$]")
        if r is not None and new_y11 is not None:
            line11.set_xdata(r)
            line11.set_ydata(new_y11)
            ax.set_xlim([min(r), max(r)])

            # Check if data is all zeros or near-zero
            if np.allclose(new_y11, 0.0, atol=1e-10):
                logger.warning(f"Equilibrium1 {name}: jtor profile is all zeros or near-zero")
        else:
            logger.warning(f"Equilibrium1 {name}: No valid r or jtor data available")

        # Set ylim with check for identical values to avoid matplotlib warning
        if not np.isfinite(y_min) or not np.isfinite(y_max):
            y_min, y_max = -1.0, 1.0
        elif abs(y_max - y_min) < 1e-10:
            # If y_min and y_max are essentially equal, create a small range around the value
            if abs(y_min) < 1e-10:
                # If both are near zero, use a default range
                y_min, y_max = -0.1, 0.1
            else:
                # Otherwise expand by a small percentage
                delta = abs(y_min) * 0.1
                y_min -= delta
                y_max += delta
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel("$" + scaleStr + "A/m^2$")
        ax.set_title("$J_{tor}$(mid-plane)")
        ax.set_xlabel("R [m]")

        # Add warning text if data is problematic
        if new_y11 is not None and np.allclose(new_y11, 0.0, atol=1e-10):
            ax.text(
                0.5,
                0.5,
                "Warning: Jtor data is all zeros\nCheck equilibrium reconstruction",
                transform=ax.transAxes,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
                fontsize=9,
            )

        ax.legend(loc="upper right", fancybox=True, shadow=True)

    def view_equilibrium_plot(self, ax, time_index1, equilibrium2_ids=None):
        data = self.compute_obj.get_equilibria(
            selection=["time", "psi2D", "rb", "zb", "r", "z", "psi_axis", "psi_boundary"]
        )

        # Validate time_index1 bounds
        if time_index1 < 0 or time_index1 >= len(data["time"]):
            logger.error(f"time_index1 {time_index1} is out of bounds for time array of length {len(data['time'])}")
            return

        data2 = None
        if equilibrium2_ids:
            try:
                compute_obj2 = EquilibriumCompute(equilibrium2_ids)
                data2 = compute_obj2.get_equilibria(
                    selection=["time", "psi2D", "rb", "zb", "r", "z", "psi_axis", "psi_boundary"]
                )

                timeE = data2["time"]
                psi2DE = data2["psi2D"]
                rbE = data2["rb"]
                zbE = data2["zb"]
                rE = data2["r"]
                zE = data2["z"]
                psi_axisE = data2["psi_axis"]
                psi_boundaryE = data2["psi_boundary"]
            except Exception as e:
                logger.error(f"Error processing second equilibrium data: {e}")
                return

        time = data["time"]
        psi2D = data["psi2D"]
        rb = data["rb"]
        zb = data["zb"]
        r = data["r"]
        z = data["z"]
        psi_axis = data["psi_axis"]
        psi_boundary = data["psi_boundary"]

        if data2:
            c, cE = self.compute_obj.get_contour(
                psi_axis,
                psi_boundary,
                time,
                time_index1,
                psi_axis2=psi_axisE,
                psi_boundary2=psi_boundaryE,
                time2=timeE,
                psi2D1=psi2D,
                psi2D2=psi2DE,
            )
        else:
            c, cE = self.compute_obj.get_contour(psi_axis, psi_boundary, time, time_index1, psi2D1=psi2D)

        # Debug logging
        logger.debug(f"Contour levels c: {c}")
        logger.debug(f"Contour levels cE: {cE}")
        logger.debug(
            f"psi_axis[{time_index1}]: {psi_axis[time_index1]}, "
            f"psi_boundary[{time_index1}]: {psi_boundary[time_index1]}"
        )

        ax.set_aspect("equal", adjustable="box")
        ax.set_title("Poloidal Flux")
        ax.set_xlabel("R[m]")
        ax.set_ylabel("Z[m]")

        plot1_success = False
        plot2_success = False

        try:
            psi_min = np.min(psi2D[time_index1])
            psi_max = np.max(psi2D[time_index1])
            logger.debug(f"Equilibrium1: psi2D range [{psi_min}, {psi_max}]")

            if psi_min < psi_max and len(c) > 0:
                ax.contour(r, z, np.transpose(psi2D[time_index1]), colors="green", levels=c, linewidths=0.85)
                (lineb1,) = ax.plot([], linewidth=2, color="green")
                lineb1.set_xdata(rb[time_index1])
                lineb1.set_ydata(zb[time_index1])
                plot1_success = True
            else:
                logger.warning(
                    f"Cannot plot equilibrium1 contours: psi_min={psi_min}, psi_max={psi_max}, levels={len(c)}"
                )
        except (IndexError, ValueError) as e:
            logger.error(f"Error plotting primary equilibrium: {e}")

        if data2:
            try:
                if len(timeE) == 0 or len(time) == 0:
                    logger.warning("Empty time arrays for equilibrium comparison")
                    return

                time_index2 = np.argmin(abs(timeE - time[time_index1]))
                time_index2 = min(time_index2, len(psi2DE) - 1)

                psi_min2 = np.min(psi2DE[time_index2])
                psi_max2 = np.max(psi2DE[time_index2])
                logger.debug(f"Equilibrium2: psi2D range [{psi_min2}, {psi_max2}]")
                logger.debug(
                    f"psi_axisE[{time_index2}]: {psi_axisE[time_index2]}, "
                    f"psi_boundaryE[{time_index2}]: {psi_boundaryE[time_index2]}"
                )

                # Check for fill values (but we can still plot if psi2D has valid range and contours are valid)
                is_fill_value = abs(psi_axisE[time_index2]) > 1e30 or abs(psi_boundaryE[time_index2]) > 1e30
                if is_fill_value:
                    logger.info(
                        "Equilibrium2 psi_axis/boundary are fill values, "
                        "but will attempt to use calculated contours from psi2D"
                    )

                # Check if we have valid data to plot (psi2D has range and contour levels are not fill values)
                contours_valid = len(cE) > 0 and not (len(cE) == 1 and abs(cE[0]) > 1e30)

                if time_index2 >= 0 and len(psi2DE) > 0 and psi_min2 < psi_max2 and contours_valid:
                    ax.contour(rE, zE, np.transpose(psi2DE[time_index2]), colors="blue", levels=cE, linewidths=0.85)
                    (lineb2,) = ax.plot([], linewidth=2, color="blue")
                    lineb2.set_xdata(rbE[time_index2])
                    lineb2.set_ydata(zbE[time_index2])
                    plot2_success = True
                else:
                    logger.warning(
                        f"Cannot plot equilibrium2 contours: psi_min={psi_min2}, psi_max={psi_max2}, "
                        f"levels={len(cE) if cE is not None else 0}, contours_valid={contours_valid}"
                    )
            except (IndexError, ValueError) as e:
                logger.error(f"Error plotting second equilibrium: {e}")

        # Add warning text if no data was plotted
        if not plot1_success and not plot2_success:
            ax.text(
                0.5,
                0.5,
                "Warning: No valid equilibrium data to plot\nCheck psi_axis, psi_boundary, and psi2D data",
                transform=ax.transAxes,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
                fontsize=9,
            )

    def view_current_plot(self, ax, time_index1, equilibrium2_ids=None):
        data = self.compute_obj.get_equilibria(selection=["time", "ip"])
        data2 = None
        if equilibrium2_ids:
            compute_obj2 = EquilibriumCompute(equilibrium2_ids)
            data2 = compute_obj2.get_equilibria(selection=["time", "ip"])
            timeE = data2["time"]
            ipE = data2["ip"]
        time = data["time"]
        ip = data["ip"]
        (line31,) = ax.plot([], marker="x", color="green")
        (line32,) = ax.plot([], marker="x", color="blue")
        line33 = ax.axvline(color="red", linestyle="--")
        ax.set_title("$I_p$")
        ax.set_xlabel("t [s]")
        ax.set_ylabel("MA")
        ylims = ax.get_ylim()
        line33.set_xdata([time[time_index1]])
        ax.set_ylim(ylims)
        line31.set_xdata(time)
        line31.set_ydata(ip / 1e6)
        xlims = np.array([min(time), max(time)])
        ip_valid = ip[np.isfinite(ip)]
        ylims = np.array([ip_valid.min(), ip_valid.max()]) / 1e6 if ip_valid.size > 0 else np.array([-1.0, 1.0])
        if data2 is not None:
            line32.set_xdata(timeE)
            line32.set_ydata(ipE / 1e6)
            ipE_valid = ipE[np.isfinite(ipE)]
            xlims[0] = np.minimum(xlims[0], np.min(timeE))
            ylims[0] = np.minimum(ylims[0], np.min(ipE_valid / 1e6)) if ipE_valid.size > 0 else ylims[0]
            xlims[1] = np.maximum(xlims[1], np.max(timeE))
            ylims[1] = np.maximum(ylims[1], np.max(ipE_valid / 1e6)) if ipE_valid.size > 0 else ylims[1]
        dy = ylims[1] - ylims[0]
        if dy > 0:
            ylims[0] = ylims[0] - 0.01 * dy
            ylims[1] = ylims[1] + 0.01 * dy
        elif ylims[0] != 0:
            ylims[0] = ylims[0] * 1.01
            ylims[1] = ylims[1] * 0.99
        else:
            xlims[0] = -1.0
            xlims[1] = +1.0
        dx = xlims[1] - xlims[0]
        if dx > 0:
            xlims[0] = xlims[0] - 0.01 * dx
            xlims[1] = xlims[1] + 0.01 * dx
        elif xlims[0] != 0:
            xlims[0] = xlims[0] * 1.01
            xlims[1] = xlims[1] * 0.99
        else:
            xlims[0] = -1.0
            xlims[1] = +1.0
        line33.set_xdata([time[time_index1]])
        ax.set_xlim(xlims)
        ax.set_ylim(ylims)

    def view_constraints(self, ax, time_index1, equilibrium2_ids=None):
        data = self.compute_obj.get_equilibria(selection=["time", "pf_constraints"])
        data2 = None
        if equilibrium2_ids:
            compute_obj2 = EquilibriumCompute(equilibrium2_ids)
            data2 = compute_obj2.get_equilibria(selection=["time", "pf_constraints"])
            timeE = data2["time"]
            constraintsE = data2["constraints"]
        time = data["time"]
        constraints = data["constraints"]

        # Debug logging
        logger.debug(f"Constraints data available: {constraints is not None}")
        if constraints:
            logger.debug(f"Constraints keys: {constraints.keys() if hasattr(constraints, 'keys') else 'N/A'}")

        (line41,) = ax.plot([], marker="x", color="darkgreen", label="target")
        (line42,) = ax.plot([], marker="x", color="darkblue", label="fitted")
        (line43,) = ax.plot([], marker="x", color="darkorange", label="target")
        (line44,) = ax.plot([], marker="x", color="maroon", label="fitted")
        ax.set_xlabel("index")

        if data2:
            result = self.compute_obj.get_constraints_info(
                "pf-currents", constraints, constraintsE, time, time_index1, timeE
            )
        else:
            result = self.compute_obj.get_constraints_info("pf-currents", constraints, None, time, time_index1, None)

        if not result:
            logger.warning("No pf-currents constraint data available")
            ax.text(
                0.5,
                0.5,
                "No pf-currents constraint data available\nCheck equilibrium reconstruction constraints",
                transform=ax.transAxes,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
                fontsize=9,
            )
            ax.set_title("pf-currents")
            return

        if result:
            y1in, y2in, y3in, y4in, titlelabel, ylabel, scaleFactor = result
            y1 = None
            y2 = None
            y3 = None
            y4 = None
            if y1in is not None:
                y1 = np.copy(y1in)
            if y2in is not None:
                y2 = np.copy(y2in)
            if y3in is not None:
                y3 = np.copy(y3in)
            if y4in is not None:
                y4 = np.copy(y4in)
            x_wrk = np.array([])
            y_wrk = np.array([])
            dataAvail = [False, False, False, False]
            dataAvail[0] = np.all(y1) is not None and np.any(y1 != imas.ids_defs.EMPTY_FLOAT)
            dataAvail[1] = np.all(y2) is not None and np.any(y2 != imas.ids_defs.EMPTY_FLOAT)
            dataAvail[2] = y3 is not None and np.any(y3 != imas.ids_defs.EMPTY_FLOAT)
            dataAvail[3] = y4 is not None and np.any(y4 != imas.ids_defs.EMPTY_FLOAT)
            if dataAvail[0]:
                x1 = range(len(y1))
                x_wrk = np.concatenate((x_wrk, x1))
                filtered = y1[y1 != imas.ids_defs.EMPTY_FLOAT]
                y1 /= scaleFactor
                if len(filtered) > 0:
                    y_wrk = np.concatenate((y_wrk, filtered / scaleFactor))
            if dataAvail[1]:
                x2 = range(len(y2))
                x_wrk = np.concatenate((x_wrk, x2))
                filtered = y2[y2 != imas.ids_defs.EMPTY_FLOAT]
                y2 /= scaleFactor
                if len(filtered) > 0:
                    y_wrk = np.concatenate((y_wrk, filtered / scaleFactor))
            if dataAvail[2]:
                x3 = range(len(y3))
                x_wrk = np.concatenate((x_wrk, x3))
                filtered = y3[y3 != imas.ids_defs.EMPTY_FLOAT]
                y3 /= scaleFactor
                if len(filtered) > 0:
                    y_wrk = np.concatenate((y_wrk, filtered / scaleFactor))
            if dataAvail[3]:
                x4 = range(len(y4))
                x_wrk = np.concatenate((x_wrk, x4))
                filtered = y4[y4 != imas.ids_defs.EMPTY_FLOAT]
                y4 /= scaleFactor
                if len(filtered) > 0:
                    y_wrk = np.concatenate((y_wrk, filtered / scaleFactor))

            minx = 0
            maxx = max(x_wrk)
            if maxx == 0:
                minx = -0.5
                maxx = +0.5
            else:
                dx = maxx - minx
                minx = minx - dx * 0.02
                maxx = maxx + dx * 0.02
            miny = min(y_wrk)
            maxy = max(y_wrk)
            dy = maxy - miny
            if dy == 0:
                dy = y_wrk[0]
            miny = miny - dy * 0.02
            maxy = maxy + dy * 0.02
            if dy == 0 and miny == 0:
                miny = -1
                maxy = +1

            if dataAvail[0]:
                line41.set_xdata(x1)
                line41.set_ydata(y1)
            else:
                line41.set_xdata(np.empty((0)))
                line41.set_ydata(np.empty((0)))
            if dataAvail[1]:
                line42.set_xdata(x2)
                line42.set_ydata(y2)
            else:
                line42.set_xdata(np.empty((0)))
                line42.set_ydata(np.empty((0)))
            if dataAvail[2]:
                line43.set_xdata(x3)
                line43.set_ydata(y3)
            else:
                line43.set_xdata(np.empty((0)))
                line43.set_ydata(np.empty((0)))
            if dataAvail[3]:
                line44.set_xdata(x4)
                line44.set_ydata(y4)
            else:
                line44.set_xdata(np.empty((0)))
                line44.set_ydata(np.empty((0)))
            if np.any(dataAvail):
                ax.set_ylabel(ylabel)
                ax.set_title(titlelabel)
                ax.set_xlim(minx, maxx)
                ax.set_ylim(miny, maxy)
            else:
                logger.warning(f"No valid {titlelabel} data (all values are fill values or empty)")
                ax.text(
                    0.5,
                    0.5,
                    f"No valid {titlelabel} data\n(all values are fill values or empty)",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
                    fontsize=9,
                )
                ax.set_title(titlelabel)
