import logging

import numpy as np
from rich.align import Align
from rich.console import Console
from rich.table import Table

from idstools.compute.core_sources import CoreSourcesCompute

logger = logging.getLogger(f"module.{__name__}")


class CoreSourcesView:
    def __init__(self, ids):
        self.core_sources_compute = CoreSourcesCompute(ids)
        self.ids = ids

    def view_sources(self, time_slice):
        """
        The `view_sources` function prints information about sources, including their name, electron
        flux, energy flux, and ion flux.
        """
        sources_dict = self.core_sources_compute.get_flux_info_from_sources(time_slice)
        ion_table = Table(show_header=False)
        for _, source_dict in sources_dict.items():
            # electrons
            if source_dict["particles_flux"] is None:
                eparticles_flux = "particles(--)"
            else:
                eparticles_flux = f"particles ({source_dict['particles_flux'] : >.6e})"
            if source_dict["energy_flux"] is None:
                eenergy_flux = "energy(--)"
            else:
                eenergy_flux = f"energy ({source_dict['energy_flux']: >.6e})"
            ion_table.add_row(
                f'{source_dict["name"]}',
                eparticles_flux,
                eenergy_flux,
                "",
                "",
                style="bold magenta",
            )
            # ions
            ion_table.add_section()
            ion_table.add_row(
                Align.right("a"),
                Align.right("z_n"),
                Align.right("z_ion"),
                Align.right("particles"),
                Align.right("energy"),
                style="bold red",
            )

            for _, ion_dict in source_dict["ions"].items():
                if ion_dict["particles_flux"] is None or np.isnan(ion_dict["particles_flux"]):
                    particles_flux = "--"
                else:
                    particles_flux = f"{ion_dict['particles_flux'] : >.6e}"
                if ion_dict["energy_flux"] is None or np.isnan(ion_dict["energy_flux"]):
                    energy_flux = "--"
                else:
                    energy_flux = f"{ion_dict['energy_flux'] : >.6e}"
                ion_table.add_row(
                    Align.right(str(ion_dict["a"])),
                    Align.right(str(ion_dict["z_n"])),
                    Align.right(str(ion_dict["z_ion"])),
                    Align.right(particles_flux),
                    Align.right(energy_flux),
                    style="bold green",
                )
            ion_table.add_section()
        console = Console()
        console.print(ion_table)

    def view_power_profiles(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_power_profiles` plots power profiles for different sources

        Args:
            ax: The parameter `ax` is an instance of the `Axes` class from the `matplotlib.pyplot` module.
                It represents the axes on which the power profiles will be plotted.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            rho_tor_norm = self.core_sources_compute.get_rho_tor_norm(time_slice)
            single_and_total_electrons_profiles = self.core_sources_compute.get_single_and_total_electrons_profiles(
                time_slice
            )
            single_and_total_ion_profiles = self.core_sources_compute.get_single_and_total_ion_profiles(time_slice)
            source_names = self.core_sources_compute.get_source_names(time_slice)
            ax.set_title("Power Profiles [MW/M3]")
            ax.plot(
                rho_tor_norm,
                single_and_total_electrons_profiles["total_electron_power_profile"] * 1.0e-6,
                label=r"Total to electrons",
            )
            ax.plot(
                rho_tor_norm,
                single_and_total_ion_profiles["total_ion_power_profile"] * 1.0e-6,
                "--",
                label=r"Total to ions",
            )
            for isource, name in source_names.items():
                ax.plot(
                    rho_tor_norm,
                    single_and_total_electrons_profiles["single_electron_power_profile"][isource] * 1.0e-6,
                    label=name + " [" + str(isource) + "]" + " to electrons",
                )
                ax.plot(
                    rho_tor_norm,
                    single_and_total_ion_profiles["single_ion_power_profile"][isource] * 1.0e-6,
                    "--",
                    label=name + " [" + str(isource) + "]" + " to ions",
                )
            ax.set_ylabel("Power to bulk $\\mathrm{[MW/m^{3}]}$")
            ax.set_xlabel("Normalized toroidal flux coordinate")
            # set legend
            ax.legend()
            return 0
        else:
            logger.warning("viewPowerProfiles:No active sources available")
        return -1

    def view_particles_profiles(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_particles_profiles` plots particle density profiles for electrons and ions at different
        sources as a function of normalized toroidal flux coordinate.

        Args:
            ax: The parameter `ax` is an instance of the `Axes` class from the `matplotlib.pyplot` module. It
                represents the axes on which the particles profiles will be plotted.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            rho_tor_norm = self.core_sources_compute.get_rho_tor_norm(time_slice)
            single_and_total_electrons_profiles = self.core_sources_compute.get_single_and_total_electrons_profiles(
                time_slice
            )
            single_and_total_ion_profiles = self.core_sources_compute.get_single_and_total_ion_profiles(time_slice)
            source_names = self.core_sources_compute.get_source_names(time_slice)
            ax.set_title("PARTICLES PROFILES [/M3/S]")
            ax.plot(
                rho_tor_norm,
                single_and_total_electrons_profiles["total_electron_particles_profile"] * 1.0e-6,
                label=r"Total to electrons",
            )
            ax.plot(
                rho_tor_norm,
                single_and_total_ion_profiles["total_ion_particles_profile"] * 1.0e-6,
                "--",
                label=r"Total to ions",
            )
            for isource, name in source_names.items():
                ax.plot(
                    rho_tor_norm,
                    single_and_total_electrons_profiles["single_electron_particles_profile"][isource] * 1.0e-6,
                    label=name + " [" + str(isource) + "]" + " electrons",
                )
                ax.plot(
                    rho_tor_norm,
                    single_and_total_ion_profiles["single_ion_particles_profile"][isource] * 1.0e-6,
                    "--",
                    label=name + " [" + str(isource) + "]" + " ions",
                )
            ax.set_ylabel("Density $\\mathrm{[m^{-3}.s^{-1}]}$")
            ax.set_xlabel("Normalized toroidal flux coordinate")
            # set legend
            ax.legend()
            return 0
        else:
            logger.warning("viewParticlesProfiles:No active sources available")
        return -1

    def view_current_profiles(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_current_profiles` plots current profiles.

        Args:
            ax: The parameter `ax` is an instance of the `Axes` class from the `matplotlib.pyplot` module. It
                represents the axes on which the current profiles will be plotted.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            rho_tor_norm = self.core_sources_compute.get_rho_tor_norm(time_slice)
            single_and_total_electrons_and_ions_profiles = (
                self.core_sources_compute.get_single_and_total_electrons_and_ions_profiles(time_slice)
            )
            source_names = self.core_sources_compute.get_source_names(time_slice)
            ax.set_title("CURRENT PROFILES [KA/M2]")
            ax.plot(
                rho_tor_norm,
                single_and_total_electrons_and_ions_profiles["total_current_profile"] * 1.0e-3,
                label=r"Total current",
            )
            for isource, name in source_names.items():
                if len(single_and_total_electrons_and_ions_profiles["single_current_profile"][isource]) > 0:
                    ax.plot(
                        rho_tor_norm,
                        single_and_total_electrons_and_ions_profiles["single_current_profile"][isource] * 1.0e-3,
                        label=name + str(isource),
                    )
            ax.set_ylabel("Current density $\\mathrm{[kA/m^{2}]}$")
            ax.set_xlabel("Normalized toroidal flux coordinate")
            # set legend
            ax.legend()
            return 0
        else:
            logger.warning("viewCurrentProfiles:No active sources available")
        return -1

    def view_power_and_particle_waveforms(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_power_and_particle_waveforms` plots power waveforms for different sources and particles
        over time.
        Args:
            ax: The parameter `ax` is an instance of the `Axes` class from the `matplotlib.pyplot` module. It
                represents the axes on which the waveforms will be plotted.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            ntime = len(self.ids.time)
            if ntime == 1:
                logger.warning("Only one time slice --> Waveforms not displayed")
            else:
                time_array = self.ids.time
                single_and_total_electrons_ions_waveforms = (
                    self.core_sources_compute.get_single_and_total_electrons_ions_waveforms(time_slice)
                )
                single_and_total_electrons_waveforms = (
                    self.core_sources_compute.get_single_and_total_electrons_waveforms(time_slice)
                )
                single_and_total_ions_waveforms = self.core_sources_compute.get_single_and_total_ions_waveforms(
                    time_slice
                )
                source_names = self.core_sources_compute.get_source_names(time_slice)
                ax.set_title("POWER AND PARTICLE WAVEFORMS")

                # --- Marker spacing: ~8 markers per curve ---
                markevery = max(1, ntime // 8)

                # --- Per-source markers cycle ---
                markers = ["o", "s", "D", "^", "v", "P", "X", "*"]

                ax.plot(
                    time_array,
                    single_and_total_electrons_ions_waveforms["total_power_waveform"] * 1.0e-6,
                    label=r"Total electrons+ions",
                    linestyle="-",
                    linewidth=3.5,
                    alpha=0.5,
                    color="black",
                )
                ax.plot(
                    time_array,
                    single_and_total_electrons_waveforms["total_electron_power_waveform"] * 1.0e-6,
                    label=r"Total electrons",
                    linestyle="--",
                    linewidth=3.0,
                    alpha=0.5,
                    color="tab:blue",
                )
                ax.plot(
                    time_array,
                    single_and_total_ions_waveforms["total_ion_power_waveform"] * 1.0e-6,
                    label=r"Total ions",
                    linestyle=":",
                    linewidth=3.0,
                    alpha=0.5,
                    color="tab:red",
                )
                for isource, name in source_names.items():
                    marker = markers[isource % len(markers)]
                    ax.plot(
                        time_array,
                        single_and_total_electrons_ions_waveforms["single_power_waveform"][isource] * 1.0e-6,
                        label=name + " [" + str(isource) + "]" + " electrons+ions",
                        linestyle="-",
                        linewidth=1.8,
                        marker=marker,
                        markersize=5,
                        markevery=markevery,
                    )
                    ax.plot(
                        time_array,
                        single_and_total_electrons_waveforms["single_electron_power_waveform"][isource] * 1.0e-6,
                        label=name + " [" + str(isource) + "]" + " electrons",
                        linestyle="--",
                        linewidth=1.5,
                        marker=marker,
                        markersize=4,
                        markevery=markevery,
                    )
                    ax.plot(
                        time_array,
                        single_and_total_ions_waveforms["single_ion_power_waveform"][isource] * 1.0e-6,
                        label=name + " [" + str(isource) + "]" + " ions",
                        linestyle=":",
                        linewidth=1.5,
                        marker=marker,
                        markersize=4,
                        markevery=markevery,
                    )
                ax.set_ylabel("Power waveforms $\\mathrm{[MW]}$")
                ax.set_xlabel("Time (s)")
                # set legend
                ax.legend()
                return 0
        else:
            logger.warning("viewPowerAndParticleWaveforms:No active sources available")
        return -1

    def view_particles_waveform(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_particles_waveform` plots the waveforms of particles (electrons and ions) over time.

        Args:
            ax: The parameter "ax" is an instance of the matplotlib Axes class. It represents the axes on which
                the waveform plot will be drawn.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            ntime = len(self.ids.time)
            if ntime == 1:
                logger.warning("Only one time slice --> Waveforms not displayed")
            else:
                time_array = self.ids.time
                single_and_total_electrons_ions_waveforms = (
                    self.core_sources_compute.get_single_and_total_electrons_ions_waveforms(time_slice)
                )

                single_and_total_electrons_waveforms = (
                    self.core_sources_compute.get_single_and_total_electrons_waveforms(time_slice)
                )

                single_and_total_ions_waveforms = self.core_sources_compute.get_single_and_total_ions_waveforms(
                    time_slice
                )

                source_names = self.core_sources_compute.get_source_names(time_slice)
                ax.set_title("PARTICLES WAVEFORM")
                ax.plot(
                    time_array,
                    single_and_total_electrons_ions_waveforms["total_particles_waveform"],
                    label=r"Total electrons+ions",
                )
                ax.plot(
                    time_array,
                    single_and_total_electrons_waveforms["total_electron_particles_waveform"],
                    label=r"Total electrons",
                )
                ax.plot(
                    time_array,
                    single_and_total_ions_waveforms["total_ion_particles_waveform"],
                    label=r"Total ions",
                )

                for isource, name in source_names.items():
                    ax.plot(
                        time_array,
                        single_and_total_electrons_ions_waveforms["single_particles_waveform"][isource],
                        label=name + " [" + str(isource) + "]" + " electrons+ions",
                    )
                    ax.plot(
                        time_array,
                        single_and_total_electrons_waveforms["single_electron_particles_waveform"][isource],
                        label=name + " [" + str(isource) + "]" + " electrons",
                    )
                    ax.plot(
                        time_array,
                        single_and_total_ions_waveforms["single_ion_particles_waveform"][isource],
                        label=name + " [" + str(isource) + "]" + " ions",
                    )
                ax.set_ylabel("Particles waveforms $\\mathrm{[s^{-1}]}$")
                ax.set_xlabel("Time (s)")
                # set legend
                ax.legend()
                return 0
        else:
            logger.warning("viewParticlesWaveform:No active sources available")
        return -1

    def view_current_waveform(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_current_waveform` plots the current waveform for different sources and displays it.

        Args:
            ax: The parameter `ax` is an instance of the `Axes` class from the `matplotlib.pyplot` module. It
                represents the axes on which the waveform plot will be drawn.
        """
        if self.core_sources_compute.is_active_source_available(time_slice):
            ntime = len(self.ids.time)
            if ntime == 1:
                logger.warning("Only one time slice --> Waveforms not displayed")
            else:
                time_array = self.ids.time
                single_and_total_current_torque = self.core_sources_compute.get_single_and_total_current_torque(
                    time_slice
                )
                source_names = self.core_sources_compute.get_source_names(time_slice)
                ax.set_title("CURRENT WAVEFORM")
                ax.plot(
                    time_array,
                    single_and_total_current_torque["total_current_waveform"] * 1.0e-3,
                    label=r"Total electrons+ions",
                )

                for isource, name in source_names.items():
                    ax.plot(
                        time_array,
                        single_and_total_current_torque["single_current_waveform"][isource] * 1.0e-3,
                        label=name + " [" + str(isource) + "]" + " electrons+ions",
                    )

                ax.set_ylabel("Current waveforms $\\mathrm{[kA.m]}$")
                ax.set_xlabel("Time (s)")
                # set legend
                ax.legend()
                return 0
        else:
            logger.warning("viewCurrentWaveform:No active sources available")
        return -1

    def view_torque_waveform(self, ax, time_slice, *args, **kwargs):
        """
        The function `view_torque_waveform` plots torque waveforms for different sources over time.

        Args:
            ax: The parameter "ax" is an instance of the matplotlib Axes class. It represents the axes on which
                the torque waveform plot will be drawn.
        """

        if self.core_sources_compute.is_active_source_available(time_slice):
            ntime = len(self.ids.time)
            if ntime == 1:
                logger.warning("Only one time slice --> Waveforms not displayed")
            else:
                time_array = self.ids.time
                single_and_total_current_torque = self.core_sources_compute.get_single_and_total_current_torque(
                    time_slice
                )
                source_names = self.core_sources_compute.get_source_names(time_slice)
                # TORQUE WAVEFORM
                ax.set_title("TORQUE WAVEFORM")
                ax.plot(
                    time_array,
                    single_and_total_current_torque["total_torque_waveform"],
                    label=r"Total electrons+ions",
                )
                for isource, name in source_names.items():
                    ax.plot(
                        time_array,
                        single_and_total_current_torque["single_torque_waveform"][isource],
                        label=name + " [" + str(isource) + "]" + " electrons+ions",
                    )

                ax.set_ylabel("Torque waveforms $\\mathrm{[kg.m^2.s^{-2}]}$")
                ax.set_xlabel("Time (s)")
                # set legend
                ax.legend()
                return 0
        else:
            logger.warning("view_torque_waveform:No active sources available")
        return -1
