import logging

import numpy as np
import scipy.constants.codata as codata
from rich.align import Align
from rich.console import Console
from rich.table import Table

from idstools.compute.core_transport import CoreTransportCompute
from idstools.compute.equilibrium import EquilibriumCompute

logger = logging.getLogger(f"module.{__name__}")

QE = codata.physical_constants["elementary charge"][0]


class CoreTransportView:
    def __init__(self, ids):
        self.core_transport_compute = CoreTransportCompute(ids)
        self.ids = ids

    def view_fluxes(self, time_slice):
        """
        The `viewFluxes` function prints out flux information for electrons and ions.
        """
        console = Console()
        fluxes_dict = self.core_transport_compute.get_fluxes(time_slice)
        ion_table = Table(show_header=False)
        for _, flux_dict in fluxes_dict.items():
            if flux_dict["particles_flux"] is None or np.isnan(flux_dict["particles_flux"]):
                eparticles_flux = "--"
            else:
                eparticles_flux = f"{flux_dict['particles_flux'] : >.6e}"
            if flux_dict["energy_flux"] is None or np.isnan(flux_dict["energy_flux"]):
                eenergy_flux = "--"

            else:
                eenergy_flux = f"{flux_dict['energy_flux']: >.6e}"
            name = flux_dict["flux_multiplier"] if flux_dict["flux_multiplier"].has_value else "--"
            name = f"{flux_dict['name']}  ( {name} )"
            ion_table.add_row(
                name,
                "",
                "",
                "",
                "electrons",
                style="bold magenta",
            )
            ion_table.add_section()
            ion_table.add_row(
                Align.right("label"),
                Align.right("a"),
                Align.right("z_n"),
                Align.right("z_ion"),
                Align.right(f"particles flux ({eparticles_flux})"),
                Align.right(f"energy flux ({eenergy_flux})"),
                style="bold yellow",
            )
            ion_table.add_section()
            for _, ion_dict in flux_dict["ions"].items():
                if ion_dict["particles_flux"] is None or np.isnan(ion_dict["particles_flux"]):
                    particles_flux = "--"
                else:
                    particles_flux = f"{ion_dict['particles_flux'] : >.6e}"
                if ion_dict["energy_flux"] is None or np.isnan(ion_dict["energy_flux"]):
                    energy_flux = "--"
                else:
                    energy_flux = f"{ion_dict['energy_flux'] : >.6e}"
                ion_table.add_row(
                    Align.right(ion_dict["name"]),
                    Align.right(str(ion_dict["a"])),
                    Align.right(str(ion_dict["z_n"])),
                    Align.right(str(ion_dict["z_ion"])),
                    Align.right(particles_flux),
                    Align.right(energy_flux),
                    style="bold green",
                )

            ion_table.add_section()

        console.print(ion_table)

    def view_ions_particle_fluxes(
        self,
        axes,
        ids_core_transport,
        ids_core_profiles,
        ids_equilibrium,
        time_slice,
        model_index,
        logscale=False,
    ):
        tm = ids_core_transport.model[model_index]
        r = tm.profiles_1d[time_slice].grid_d.rho_tor_norm
        vp_per__s = self._get_vp_per_s(tm.profiles_1d[time_slice].grid_d, ids_equilibrium, time_slice, model_index)

        e_compute = EquilibriumCompute(ids_equilibrium)
        gm3 = e_compute.getgm3(r, time_slice)
        gm7 = e_compute.getgm7(r, time_slice)

        counter = 0
        for t_i, c_i in zip(
            tm.profiles_1d[-1].ion,
            ids_core_profiles.profiles_1d[time_slice].ion,
        ):
            self._validate_ions_data(t_i, c_i, r, model_index)

            gamma_i = vp_per__s * (
                -t_i.particles.d * np.gradient(c_i.density, r) * gm3 + c_i.density * t_i.particles.v * gm7
            )
            ax = axes[counter]
            counter = counter + 1
            ax.plot(r, gamma_i, label="Direct evaluation")
            ax.plot(r, t_i.particles.flux, label="Transport code")
            if logscale:
                ax.set_yscale("log")
            ax.set_title(f"Particle fluxes for {t_i.element[0].z_n}/{t_i.element[0].a}")
            ax.set_xlabel("rho_tor_norm")
            ax.set_ylabel("Particle flux density")
            ax.legend()

    def view_ions_energy_fluxes(
        self,
        axes,
        ids_core_transport,
        ids_core_profiles,
        ids_equilibrium,
        time_slice,
        model_index,
        logscale=False,
    ):
        tm = ids_core_transport.model[model_index]
        r = tm.profiles_1d[time_slice].grid_d.rho_tor_norm
        vp_per__s = self._get_vp_per_s(tm.profiles_1d[time_slice].grid_d, ids_equilibrium, time_slice, model_index)

        e_compute = EquilibriumCompute(ids_equilibrium)
        gm3 = e_compute.getgm3(r, time_slice)
        gm7 = e_compute.getgm7(r, time_slice)

        counter = 0
        for t_i, c_i in zip(
            tm.profiles_1d[-1].ion,
            ids_core_profiles.profiles_1d[time_slice].ion,
        ):
            self._validate_ions_data(t_i, c_i, r, model_index)
            gamma_i = vp_per__s * (
                -t_i.particles.d * np.gradient(c_i.density, r) * gm3 + c_i.density * t_i.particles.v * gm7
            )

            ax = axes[counter]
            counter = counter + 1
            q_i_conductive = (
                vp_per__s
                * (-t_i.energy.d * np.gradient(c_i.temperature, r) * gm3 + c_i.temperature * t_i.energy.v * gm7)
                * c_i.density
                * QE
            )
            q_i_convective = gamma_i * c_i.temperature * QE
            ax.plot(r, q_i_conductive, label="Direct evaluation (conductive)")
            (base_line,) = ax.plot(r, q_i_convective * 1.5, label="Direct evaluation (convective)")
            ax.fill_between(
                r,
                q_i_convective * 0.0,
                q_i_convective * 2.5,
                facecolor=base_line.get_color(),
                alpha=0.2,
            )
            (base_line,) = ax.plot(r, q_i_conductive + q_i_convective * 1.5, label="Direct evaluation")
            ax.fill_between(
                r,
                q_i_conductive + q_i_convective * 0.0,
                q_i_conductive + q_i_convective * 2.5,
                facecolor=base_line.get_color(),
                alpha=0.2,
            )
            ax.plot(r, t_i.energy.flux, label="Transport code")
            if logscale:
                ax.set_yscale("log")
            ax.set_title(f"Energy fluxes for {t_i.element[0].z_n}/{t_i.element[0].a}")
            ax.set_xlabel("rho_tor_norm")
            ax.set_ylabel("Energy flux density")
            ax.legend()

    def view_energy_fluxes_for_electrons(
        self,
        ax,
        ids_core_transport,
        ids_core_profiles,
        ids_equilibrium,
        time_slice,
        model_index,
        logscale=False,
    ):
        tm = ids_core_transport.model[model_index]
        r = tm.profiles_1d[time_slice].grid_d.rho_tor_norm
        vp_per__s = self._get_vp_per_s(tm.profiles_1d[time_slice].grid_d, ids_equilibrium, time_slice, model_index)

        t_e = tm.profiles_1d[time_slice].electrons
        c_e = ids_core_profiles.profiles_1d[time_slice].electrons
        self._validate_electrons(t_e, c_e, r, model_index)
        e_compute = EquilibriumCompute(ids_equilibrium)
        gm3 = e_compute.getgm3(r, time_slice=time_slice)
        gm7 = e_compute.getgm7(r, time_slice=time_slice)

        q_e_conductive = (
            vp_per__s
            * (-t_e.energy.d * np.gradient(c_e.temperature, r) * gm3 + c_e.temperature * t_e.energy.v * gm7)
            * c_e.density
            * QE
        )
        gamma_e = np.array([t.particles.flux * t.z_ion for t in tm.profiles_1d[-1].ion]).sum(axis=0)
        q_e_convective = gamma_e * c_e.temperature * QE

        ax.plot(r, q_e_conductive, label="Direct evaluation (conductive)")
        (base_line,) = ax.plot(r, q_e_convective * 1.5, label="Direct evaluation (convective)")
        ax.fill_between(
            r,
            q_e_convective * 0.0,
            q_e_convective * 2.5,
            facecolor=base_line.get_color(),
            alpha=0.2,
        )
        (base_line,) = ax.plot(r, q_e_conductive + q_e_convective * 1.5, label="Direct evaluation")
        ax.fill_between(
            r,
            q_e_conductive + q_e_convective * 0.0,
            q_e_conductive + q_e_convective * 2.5,
            facecolor=base_line.get_color(),
            alpha=0.2,
        )
        ax.plot(r, t_e.energy.flux, label="Transport code")
        if logscale:
            ax.set_yscale("log")
        ax.set_title("Energy fluxes for electrons")
        ax.set_xlabel("rho_tor_norm")
        ax.set_ylabel("Energy flux density")
        ax.legend()

    def view_particle_fluxes_for_electrons(
        self,
        ax,
        ids_core_transport,
        ids_core_profiles,
        time_slice,
        model_index,
        logscale=False,
    ):
        tm = ids_core_transport.model[model_index]
        r = tm.profiles_1d[time_slice].grid_d.rho_tor_norm

        t_e = tm.profiles_1d[time_slice].electrons
        c_e = ids_core_profiles.profiles_1d[time_slice].electrons
        self._validate_electrons(t_e, c_e, r, model_index)
        gamma_e = np.array([t.particles.flux * t.z_ion for t in tm.profiles_1d[-1].ion]).sum(axis=0)

        ax.plot(r, gamma_e, label="Ambipolar Transport code fluxes")
        ax.plot(r, t_e.particles.flux, label="Transport code")
        if logscale:
            ax.set_yscale("log")
        ax.set_title("Particle fluxes for electrons")
        ax.set_xlabel("rho_tor_norm")
        ax.set_ylabel("Particle flux density")
        ax.legend()

    @staticmethod
    def _get_vp_per_s(grid_d, ids_equilibrium, time_slice, model_index):
        """dV/drho_tor_norm / area on grid_d.

        grid_d.volume and grid_d.area are optional in the DD. If they are empty,
        they are taken from equilibrium.time_slice[].profiles_1d and interpolated on grid_d.rho_tor_norm.
        """
        r = np.asarray(grid_d.rho_tor_norm)
        v = np.asarray(grid_d.volume)
        s = np.asarray(grid_d.area)
        if len(v) != len(r) or len(s) != len(r):
            eq = ids_equilibrium.time_slice[time_slice].profiles_1d
            if len(eq.rho_tor_norm) > 0 and len(eq.volume) == len(eq.rho_tor_norm) == len(eq.area):
                logger.warning(
                    f"core_transport.model[{model_index}].profiles_1d.grid_d.volume/area are empty, "
                    "taken from equilibrium"
                )
                v = np.interp(r, eq.rho_tor_norm, eq.volume)
                s = np.interp(r, eq.rho_tor_norm, eq.area)
            else:
                logger.critical(
                    f"core_transport.model[{model_index}].profiles_1d.grid_d.volume/area and "
                    "equilibrium volume/area are empty, direct evaluation is not possible"
                )
                return np.full(len(r), np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.gradient(v, r) / s

    def _validate_electrons(self, t_e, c_e, r, model_index):
        if len(r) != len(c_e.density):
            logger.critical("core_profiles.profiles_1d[-1].electrons.density could not be read")
            c_e.density = c_e.density[: len(r)]
        if len(r) != len(c_e.temperature):
            logger.critical("core_profiles.profiles_1d[-1].electrons.temperature could not be read")
            c_e.temperature = c_e.temperature[: len(r)]
        if len(t_e.particles.flux) < 1:
            logger.critical(
                f"core_transport.model[{model_index}].profiles_1d[-1].electrons.particles.flux could not be read"
            )
            t_e.particles.flux = np.asarray([np.nan] * r)
        if len(t_e.energy.d) < 1:
            logger.critical(f"core_transport.model[{model_index}].profiles_1d[-1].electrons.energy.d could not be read")
            t_e.energy.d = np.asarray([np.nan] * r)
        if len(t_e.energy.v) < 1:
            logger.critical(f"core_transport.model[{model_index}].profiles_1d[-1].electrons.energy.v could not be read")
            t_e.energy.v = np.asarray([np.nan] * r)
        if len(t_e.energy.flux) < 1:
            logger.critical(
                f"core_transport.model[{model_index}].profiles_1d[-1].electrons.energy.flux could not be read"
            )
            t_e.energy.flux = np.asarray([np.nan] * r)

    def _validate_ions_data(self, t_i, c_i, r, model_index):
        if len(c_i.density) < 1:
            logger.critical("core_profiles.profiles_1d[-1].ion.density could not be read")
            c_i.density = np.asarray([np.nan] * r)

        if len(r) != len(c_i.density):
            logger.critical(
                "core_profiles.profiles_1d[-1].ion.density length is not the same as rho_tor_norm length,"
                "correcting the length"
            )
            c_i.density = c_i.density[: len(r)]
        if len(c_i.temperature) < 1:
            logger.critical("core_profiles.profiles_1d[-1].ion.temperature could not be read")
            c_i.temperature = np.asarray([np.nan] * r)
        if len(r) != len(c_i.temperature):
            logger.critical(
                "core_profiles.profiles_1d[-1].ion.temperature length is not the same as rho_tor_norm length,"
                "correcting the length"
            )
            c_i.temperature = c_i.temperature[: len(r)]

        if len(t_i.particles.d) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.particles.d could not be read")
            t_i.particles.d = np.asarray([np.nan] * r)
        if len(t_i.particles.v) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.particles.v could not be read")
            t_i.particles.v = np.asarray([np.nan] * r)
        if len(t_i.particles.flux) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.particles.flux could not be read")
            t_i.particles.flux = np.asarray([np.nan] * r)
        if len(t_i.energy.d) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.energy.d could not be read")
            t_i.energy.d = np.asarray([np.nan] * r)
        if len(t_i.energy.v) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.energy.v could not be read")
            t_i.energy.v = np.asarray([np.nan] * r)
        if len(t_i.energy.flux) < 1:
            logger.critical(f"core_transport.model[{model_index}].ion.energy.flux could not be read")
            t_i.energy.flux = np.asarray([np.nan] * r)
