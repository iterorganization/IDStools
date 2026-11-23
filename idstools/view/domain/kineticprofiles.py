import logging

from idstools.domain.kineticprofiles import KineticProfilesCompute

logger = logging.getLogger("module")


class KineticProfilesView:
    single_style = "o"
    multi_style = "-"

    def __init__(self, connection, time_slice, edge_required, dd_update):
        self.k_profiles = KineticProfilesCompute()
        self.k_profiles.analyze(connection, time_slice, edge_required, dd_update)
        if self.k_profiles.is_core_profiles_present:
            self.plotstyle = (
                KineticProfilesView.multi_style
                if len(self.k_profiles.waveform["time"]) > 1
                else KineticProfilesView.single_style
            )
        else:
            self.plotstyle = KineticProfilesView.single_style

    @staticmethod
    def view_time_line(ax, time):
        ymin = ax.get_ylim()[0]
        ymax = ax.get_ylim()[1]
        ax.plot(
            [time, time],
            [ymin, ymax],
            color="gray",
            linestyle="--",
            label=r"$t_{slice}$",
        )
        ax.set_ylim(ymin, ymax)

    def view_central_temperature_waveforms(self, ax):
        """
        This function plots central temperature waveforms with optional ion temperature

        Args:
            ax: a  matplotlib Axes object.
        """
        ax.plot(
            self.k_profiles.waveform["time"],
            self.k_profiles.waveform["te"]["central"],
            self.plotstyle,
            color="r",
            label=r"$T_e(0)$",
        )
        if self.k_profiles.ti_flag != 0:
            ax.plot(
                self.k_profiles.waveform["time"],
                self.k_profiles.waveform["ti"]["central"],
                self.plotstyle,
                color="b",
                label=r"$T_i(0)$",
            )
        if (
            self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1]
            > self.k_profiles.common_time_array[0]
        ):
            ax.set_xlim(
                self.k_profiles.common_time_array[0],
                self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1],
            )

        KineticProfilesView.view_time_line(ax, self.k_profiles.common_time_value)
        ax.set_xlabel("$Time\\/[\\mathrm{s}]$")
        ax.set_ylabel("$T\\/[\\mathrm{keV}]$")
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_title("Profiles displayed for t = " + "%.1f" % self.k_profiles.common_time_value + " s")

    def view_central_density_waveforms(self, ax, logscale=False):
        """
        This function plots various density waveforms over time

        Args:
            ax: a Matplotlib axis object.
        """
        ax.plot(
            self.k_profiles.waveform["time"],
            self.k_profiles.waveform["ne"]["central"],
            self.plotstyle,
            color="r",
            label=r"$n_e(0)$",
        )
        if max(self.k_profiles.nspec_over_ne) > 0:
            ax.plot(
                self.k_profiles.waveform["time"],
                self.k_profiles.waveform["ni"]["central"],
                self.plotstyle,
                color="b",
                label=r"$n_i(0)$",
            )
        if self.k_profiles.species:
            for ispecies in range(self.k_profiles.nspecies_core):
                if (self.k_profiles.is_composition_available == 1) & (
                    self.k_profiles.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT
                ):
                    ax.plot(
                        self.k_profiles.waveform["time"],
                        self.k_profiles.waveform["n_species"][self.k_profiles.species[ispecies]]["density"]["central"],
                        self.plotstyle,
                        label=r"$n_{" + self.k_profiles.species[ispecies] + "}(0)$",
                    )

        KineticProfilesView.view_time_line(ax, self.k_profiles.common_time_value)
        ax.set_xlabel("$Time\\/[\\mathrm{s}]$")
        ax.set_ylabel("$n\\/[\\mathrm{m^{-3}}]$")

        if (
            self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1]
            > self.k_profiles.common_time_array[0]
        ):
            ax.set_xlim(
                self.k_profiles.common_time_array[0],
                self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1],
            )
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        if logscale:
            ax.set_yscale("log")

    def view_central_zeff_waveform(self, ax):
        """
        This function plots the central Z-effective waveform over time.

        Args:
            ax: a Matplotlib axis object.
        """
        ax.plot(
            self.k_profiles.waveform["time"],
            self.k_profiles.waveform["zeff"]["central"],
            self.plotstyle,
            color="b",
            label=r"$Z_{eff}(0)$",
        )
        self.view_time_line(ax, self.k_profiles.common_time_value)
        ax.set_xlabel(r"$Time\/[\mathrm{s}]$")
        ax.set_ylabel("$Z_{eff}$")
        if (
            self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1]
            > self.k_profiles.common_time_array[0]
        ):
            ax.set_xlim(
                self.k_profiles.common_time_array[0],
                self.k_profiles.common_time_array[self.k_profiles.common_time_length - 1],
            )
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    def view_temperature_profiles(self, ax):
        """
        This function plots temperature profiles for electron and ion temperatures at the core and edge regions
        based on the provided data.

        Args:
            ax: a matplotlib Axes object
        """
        if self.k_profiles.is_core_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm"],
                self.k_profiles.profiles["te"],
                color="r",
                label=r"$T_e$",
            )
            if self.k_profiles.ti_flag != 0:
                ax.plot(
                    self.k_profiles.profiles["rhonorm"],
                    self.k_profiles.profiles["ti"],
                    color="b",
                    label=r"$T_i$",
                )
        if self.k_profiles.is_edge_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm_e"],
                self.k_profiles.profiles["te_e"],
                color="r",
                label=r"$T_{e,edge}$",
            )
            ax.plot(
                self.k_profiles.profiles["rhonorm_e"],
                self.k_profiles.profiles["ti_e"],
                color="b",
                label=r"$T_{i,edge}$",
            )
        if not self.k_profiles.r_out_graph:
            ax.set_xlabel(r"$\rho/\rho_0$")
            ax.set_ylabel("$T\\/[\\mathrm{keV}]$")
        else:
            ax.set_xlabel(r"$R_{maj}\/[\mathrm{m}]$")
            ax.set_ylabel("$T\\/[\\mathrm{keV}]$")
        ax.set_xlim(self.k_profiles.xbeg, self.k_profiles.xend)
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.set_title("t = " + "%.1f" % self.k_profiles.common_time_value + " s")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    def view_density_profiles(self, ax, logscale=False):
        """
        This function plots density profiles for different species in a plasma based on provided kinetic profiles.

        Args:
            ax: a Matplotlib axis object
        """
        if self.k_profiles.is_core_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm"],
                self.k_profiles.profiles["ne"],
                color="r",
                label=r"$n_e$",
            )
            if "ni" in self.k_profiles.profiles.keys():
                if max(self.k_profiles.nspec_over_ne) > 0:
                    ax.plot(
                        self.k_profiles.profiles["rhonorm"],
                        self.k_profiles.profiles["ni"],
                        color="b",
                        label=r"$n_i$",
                    )
        if self.k_profiles.is_edge_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm_e"],
                self.k_profiles.profiles["ne_e"],
                color="r",
                label=r"$n_{e,edge}$",
            )
            ax.plot(
                self.k_profiles.profiles["rhonorm_e"],
                self.k_profiles.profiles["ni_e"],
                color="b",
                label=r"$n_{i,edge}$",
            )
        if self.k_profiles.species:
            for ispecies in range(self.k_profiles.nspecies_core):
                color = None  # edge curve uses the same color as the core curve
                if self.k_profiles.is_composition_available and self.k_profiles.is_core_profiles_present:
                    if self.k_profiles.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT:
                        (line,) = ax.plot(
                            self.k_profiles.profiles["rhonorm"],
                            self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["density"],
                            label=r"$n_" + self.k_profiles.species[ispecies] + "$",
                        )
                        color = line.get_color()
                if self.k_profiles.is_edge_profiles_present and self.k_profiles.species_map[ispecies] != -99:
                    if (
                        self.k_profiles.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT
                        or self.k_profiles.is_core_profiles_present == 0
                    ):
                        ax.plot(
                            self.k_profiles.profiles["rhonorm_e"],
                            self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["density_e"],
                            color=color,
                            label=r"$n_{" + self.k_profiles.species[ispecies] + ",edge}$",
                        )
        if not self.k_profiles.r_out_graph:
            ax.set_xlabel(r"$\rho/\rho_0$")
            ax.set_ylabel("$n\\/[\\mathrm{m^{-3}}]$")
        else:
            ax.set_xlabel(r"$R_{maj}\/[\mathrm{m}]$")
            ax.set_ylabel("$n\\/[\\mathrm{m^{-3}}]$")
        if logscale:
            ax.set_yscale("log")
        ax.set_xlim(self.k_profiles.xbeg, self.k_profiles.xend)
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.set_title("t = " + "%.1f" % self.k_profiles.common_time_value + " s")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    def view_zeff_profile(self, ax):
        """
        This function plots Zeff profiles at the core and edge regions

        Args:
            ax: a Matplotlib axis object
        """
        if self.k_profiles.is_core_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm"],
                self.k_profiles.profiles["zeff"],
                color="b",
                label=r"$Z_{eff}$",
            )
        if self.k_profiles.is_edge_profiles_present:
            ax.plot(
                self.k_profiles.profiles["rhonorm_e"],
                self.k_profiles.profiles["zeff_e"],
                color="b",
                label=r"$Z_{eff,edge}$",
            )
        if not self.k_profiles.r_out_graph:
            ax.set_xlabel(r"$\rho/\rho_0$")
            ax.set_ylabel("$Z_{eff}$")
        else:
            ax.set_xlabel(r"$R_{maj}\/[\mathrm{m}]$")
            ax.set_ylabel("$Z_{eff}$")
        ax.set_xlim(self.k_profiles.xbeg, self.k_profiles.xend)
        # ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
        ax.set_title("t = " + "%.1f" % self.k_profiles.common_time_value + " s")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    def view_vphi_profile(self, ax, logscale=False):
        """
        This Python function plots the toroidal rotation velocity profiles for different species in a plasma
        simulation.

        Args:
            ax: a matplotlib axis object.
        """
        if self.k_profiles.species:
            if (
                self.k_profiles.is_composition_available
                and (self.k_profiles.vphi_flag != 0 or self.k_profiles.vphi_e_flag != 0)
                and (max(self.k_profiles.nspec_over_ne) > 0 or not self.k_profiles.is_core_profiles_present)
            ):
                for ispecies in range(self.k_profiles.nspecies_core):
                    if self.k_profiles.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT:
                        if "vphi" in self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]].keys():
                            color = None  # edge curve uses the same color as the core curve
                            if self.k_profiles.vphi_flag != 0:
                                (line,) = ax.plot(
                                    self.k_profiles.profiles["rhonorm"],
                                    self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["vphi"],
                                    label=r"$vphi_" + self.k_profiles.species[ispecies] + "$",
                                )
                                color = line.get_color()
                            if (
                                self.k_profiles.is_edge_profiles_present
                                and self.k_profiles.species_map[ispecies] != -99
                                and self.k_profiles.vphi_e_flag != 0
                            ):
                                ax.plot(
                                    self.k_profiles.profiles["rhonorm_e"],
                                    self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["vphi_e"],
                                    color=color,
                                    label=r"$vphi_{" + self.k_profiles.species[ispecies] + ",edge}$",
                                )
                if not self.k_profiles.r_out_graph:
                    ax.set_xlabel(r"$\rho/\rho_0$")
                    ax.set_ylabel(r"$|v_{tor}|\/[\mathrm{m.s^{-1}}]$")
                else:
                    ax.set_xlabel(r"$R_{maj}\/[\mathrm{m}]$")
                    ax.set_ylabel(r"$|v_{tor}|\/[\mathrm{m.s^{-1}}]$")
                ax.set_xlim(self.k_profiles.xbeg, self.k_profiles.xend)
                if logscale is False:
                    if self.k_profiles.max_vphi > self.k_profiles.min_vphi:
                        ax.set_ylim(self.k_profiles.min_vphi, self.k_profiles.max_vphi * 1.1)

                ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                ax.set_title("t = " + "%.1f" % self.k_profiles.common_time_value + " s")
                ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                if logscale:
                    ax.set_yscale("log")
        else:
            ax.remove()

    def view_vpol_profile(self, ax, logscale=False):
        """
        This function plots the vpol profiles for different species based on certain conditions and customizes
        the legend and axis labels accordingly.

        Args:
            ax: a matplotlib Axes object.
        """
        if self.k_profiles.species:
            if (
                self.k_profiles.is_composition_available
                and (self.k_profiles.vpol_flag != 0 or self.k_profiles.vpol_e_flag != 0)
                and (max(self.k_profiles.nspec_over_ne) > 0 or not self.k_profiles.is_core_profiles_present)
            ):
                for ispecies in range(self.k_profiles.nspecies_core):
                    if self.k_profiles.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT:
                        if "vpol" in self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]].keys():
                            color = None  # edge curve uses the same color as the core curve
                            if self.k_profiles.vpol_flag != 0:
                                (line,) = ax.plot(
                                    self.k_profiles.profiles["rhonorm"],
                                    self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["vpol"],
                                    label=r"$vpol_" + self.k_profiles.species[ispecies] + "$",
                                )
                                color = line.get_color()
                            if (
                                self.k_profiles.is_edge_profiles_present
                                and self.k_profiles.species_map[ispecies] != -99
                                and self.k_profiles.vpol_e_flag != 0
                            ):
                                ax.plot(
                                    self.k_profiles.profiles["rhonorm_e"],
                                    self.k_profiles.profiles["n_species"][self.k_profiles.species[ispecies]]["vpol_e"],
                                    color=color,
                                    label=r"$vpol_{" + self.k_profiles.species[ispecies] + ",edge}$",
                                )
                if not self.k_profiles.r_out_graph:
                    ax.set_xlabel(r"$\rho/\rho_0$")
                    ax.set_ylabel(r"$|v_{pol}|\/[\mathrm{m.s^{-1}}]$")
                else:
                    ax.set_xlabel(r"$R_{maj}\/[\mathrm{m}]$")
                    ax.set_ylabel(r"$|v_{pol}|\/[\mathrm{m.s^{-1}}]$")
                ax.set_xlim(self.k_profiles.xbeg, self.k_profiles.xend)
                if logscale is False:
                    if self.k_profiles.max_vpol > self.k_profiles.min_vpol:
                        ax.set_ylim(self.k_profiles.min_vpol, self.k_profiles.max_vpol * 1.1)

                ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                ax.set_title("t = " + "%.1f" % self.k_profiles.common_time_value + " s")
                ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
                if logscale:
                    ax.set_yscale("log")
        else:
            ax.remove()
