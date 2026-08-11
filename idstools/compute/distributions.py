"""
This module provides compute functions and classes for distributions ids data

"""

import logging

from idstools.compute.common import get_compat_attr

logger = logging.getLogger("module")


class DistributionsCompute:
    """This class provides compute functions for distributions ids.

    Attributes:
        ids (object): The distributions IDS (Integrated Data Structure) object containing
            fast particle and energetic ion distribution functions.
        ndistributions (int): Number of distributions in the ids object.
        nrho (int): Number of radial grid points (calculated).
        rho_tor_norm (array): Normalized toroidal rho values (calculated).
        cur_calc (object): Current calculation data (calculated).
        active_distributions (list): List of active distributions (calculated).
        radial_grid_info (object): Radial grid information (calculated).
        is_radial_grid_info_processed (bool): Flag indicating if radial grid info has been processed.
    """

    def __init__(self, ids):
        self.ids = ids

        # calculations
        self.ndistributions = len(self.ids.distribution)

        self.nrho = None
        self.rho_tor_norm = None
        self.cur_calc = None
        self.active_distributions = None
        self.radial_grid_info = None
        self.is_radial_grid_info_processed = False

    def get_radial_grid_info(self, time_slice):
        """
        The function `get_radial_grid_info` retrieves radial grid information for distributions in a
        plasma simulation.

        Args:
            time_slice: The `time_slice` parameter

        Returns:
            The function `get_radial_grid_info` returns the `radial_grid_info` dictionary containing
            information about radial grid data for each distribution. If the `radial_grid_info` dictionary
            is empty, it returns `None`. The function also sets several attributes of the class instance
            based on the computed radial grid information before returning the `radial_grid_info`
            dictionary.
        """
        radial_grid_info = {}
        for idistrib in range(self.ndistributions):
            distributions_data = {}
            distributions_data["is_active"] = 0
            distributions_data["cur_calc"] = 1
            distributions_data["nrho"] = 0
            distributions_data["rho_tor_norm"] = None
            if len(self.ids.distribution[idistrib].global_quantities[time_slice].collisions.ion) > 0:
                distributions_data["is_active"] = 1
                current_tor = get_compat_attr(
                    self.ids.distribution[idistrib].global_quantities[time_slice], "current_tor", "current_phi"
                )

                if current_tor == -9e40:
                    distributions_data["cur_calc"] = 0
                try:
                    distributions_data["rho_tor_norm"] = 0
                    if len(self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor_norm) > 0:
                        distributions_data["nrho"] = len(
                            self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor_norm
                        )
                        distributions_data["rho_tor_norm"] = (
                            self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor_norm
                        )
                    elif len(self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor) > 0:
                        distributions_data["nrho"] = len(
                            self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor
                        )
                        distributions_data["rho_tor_norm"] = (
                            self.ids.distribution[idistrib].profiles_1d[time_slice].grid.rho_tor
                            / self.ids.distribution[idistrib]
                            .profiles_1d[time_slice]
                            .grid.rho_tor[distributions_data["nrho"] - 1]
                        )
                except Exception as e:
                    logger.warning(
                        f"distributions.distribution[{idistrib}].profiles_1d[{time_slice}].grid.rho_tor_norm and"
                        "rho_tor could not be read"
                    )
                    logger.debug(f"{e}")
                    return None
                if distributions_data["nrho"] == 0:
                    logger.warning(
                        f"distributions.distribution[{idistrib}].profiles_1d[{time_slice}].grid.rho_tor_norm"
                        "and rho_tor are empty"
                    )
                    return None

            radial_grid_info[idistrib] = distributions_data
        self.active_distributions = {key: value for key, value in radial_grid_info.items() if value["is_active"] == 1}
        if not radial_grid_info:
            return None
        self.nrho = radial_grid_info[0]["nrho"]
        self.rho_tor_norm = radial_grid_info[0]["rho_tor_norm"]
        self.cur_calc = radial_grid_info[0]["cur_calc"]
        self.radial_grid_info = radial_grid_info
        self.is_radial_grid_info_processed = True
        return radial_grid_info

    def get_profiles(self, time_slice, process_index=0):
        """
        The function `get_profiles` retrieves and organizes various profiles and waveforms related to
        injectors and distributions for a given time index.

        Args:
            time_slice: The `time_slice` parameter

        Returns:
            The `get_profiles` method returns a dictionary containing various profiles related to
            injectors, waveforms, and power density. The dictionary includes information such as injector
            names, current waveforms, power waveforms, current density profiles, and power density profiles
            for both individual injectors and all injectors combined. The method also logs information about
            total power, power to electrons, power to ions, and total current
        """
        if self.nrho is None:
            return None
        time_array = self.ids.time
        ntime = len(time_array)
        if self.is_radial_grid_info_processed is False:
            self.get_radial_grid_info(time_slice)
        profiles = {}
        # INJECTOR NAME
        profiles["single_nf_source_name"] = dict()

        # WAVEFORMS
        profiles["all_injectors_current_waveform"] = [0] * ntime
        profiles["all_injectors_electron_power_waveform"] = [0] * ntime
        profiles["all_injectors_ion_power_waveform"] = [0] * ntime
        profiles["all_injectors_total_power_waveform"] = [0] * ntime
        profiles["single_current_waveform"] = dict()
        profiles["single_electron_power_waveform"] = dict()
        profiles["single_ion_power_waveform"] = dict()
        profiles["single_total_power_waveform"] = dict()

        # PROFILES
        profiles["all_injectors_current_density_profile"] = [0] * self.nrho
        profiles["all_injectors_electron_power_density_profile"] = [0] * self.nrho
        profiles["all_injectors_ion_power_density_profile"] = [0] * self.nrho
        profiles["all_injectors_total_power_density_profile"] = [0] * self.nrho
        profiles["single_current_density_profile"] = dict()
        profiles["single_electron_power_density_profile"] = dict()
        profiles["single_ion_power_density_profile"] = dict()
        profiles["single_total_power_density_profile"] = dict()

        # LOOP OVER ALL SOURCE
        for idistrib in range(self.ndistributions):
            # INJECTOR NAME
            if len(self.ids.distribution[idistrib].process) <= process_index:
                if len(self.ids.distribution[idistrib].process[process_index].type.description) > 0:
                    profiles["single_nf_source_name"][idistrib] = self.ids.distribution[idistrib].process[
                        process_index
                    ].type.description + str(idistrib)
                else:
                    profiles["single_nf_source_name"][idistrib] = f"Beam_f{idistrib}"
            else:
                profiles["single_nf_source_name"][idistrib] = f"Beam_{idistrib}"
            if self.radial_grid_info[idistrib]["is_active"]:
                # WAVEFORMS
                profiles["single_current_waveform"][idistrib] = [0] * ntime
                profiles["single_electron_power_waveform"][idistrib] = [0] * ntime
                profiles["single_ion_power_waveform"][idistrib] = [0] * ntime
                profiles["single_total_power_waveform"][idistrib] = [0] * ntime
                nions = len(self.ids.distribution[idistrib].global_quantities[time_slice].collisions.ion)
                for itime in range(ntime):
                    if self.cur_calc == 1:
                        current_tor = get_compat_attr(
                            self.ids.distribution[idistrib].global_quantities[time_slice], "current_tor", "current_phi"
                        )
                        profiles["single_current_waveform"][idistrib][itime] = current_tor
                    profiles["single_electron_power_waveform"][idistrib][itime] = (
                        self.ids.distribution[idistrib].global_quantities[itime].collisions.electrons.power_thermal
                    )
                    for iion in range(nions):
                        profiles["single_ion_power_waveform"][idistrib][itime] = (
                            profiles["single_ion_power_waveform"][idistrib][itime]
                            + self.ids.distribution[idistrib]
                            .global_quantities[itime]
                            .collisions.ion[iion]
                            .power_thermal
                        )
                    profiles["single_total_power_waveform"][idistrib][itime] = (
                        profiles["single_electron_power_waveform"][idistrib][itime]
                        + profiles["single_ion_power_waveform"][idistrib][itime]
                    )
                    profiles["all_injectors_current_waveform"][itime] = (
                        profiles["all_injectors_current_waveform"][itime]
                        + profiles["single_current_waveform"][idistrib][itime]
                    )
                    profiles["all_injectors_electron_power_waveform"][itime] = (
                        profiles["all_injectors_electron_power_waveform"][itime]
                        + profiles["single_electron_power_waveform"][idistrib][itime]
                    )
                    profiles["all_injectors_ion_power_waveform"][itime] = (
                        profiles["all_injectors_ion_power_waveform"][itime]
                        + profiles["single_ion_power_waveform"][idistrib][itime]
                    )
                    profiles["all_injectors_total_power_waveform"][itime] = (
                        profiles["all_injectors_total_power_waveform"][itime]
                        + profiles["single_electron_power_waveform"][idistrib][itime]
                        + profiles["single_ion_power_waveform"][idistrib][itime]
                    )
                # PROFILES
                profiles["single_current_density_profile"][idistrib] = [0] * self.nrho
                profiles["single_electron_power_density_profile"][idistrib] = [0] * self.nrho
                profiles["single_ion_power_density_profile"][idistrib] = [0] * self.nrho
                profiles["single_total_power_density_profile"][idistrib] = [0] * self.nrho
                if self.cur_calc == 1:
                    current_tor = get_compat_attr(
                        self.ids.distribution[idistrib].profiles_1d[time_slice], "current_tor", "current_phi"
                    )
                    profiles["single_current_density_profile"][idistrib] = current_tor
                profiles["single_electron_power_density_profile"][idistrib] = (
                    self.ids.distribution[idistrib].profiles_1d[time_slice].collisions.electrons.power_thermal
                )
                for iion in range(nions):
                    profiles["single_ion_power_density_profile"][idistrib] = (
                        profiles["single_ion_power_density_profile"][idistrib]
                        + self.ids.distribution[idistrib].profiles_1d[time_slice].collisions.ion[iion].power_thermal
                    )
                profiles["single_total_power_density_profile"][idistrib] = (
                    profiles["single_electron_power_density_profile"][idistrib]
                    + profiles["single_ion_power_density_profile"][idistrib]
                )
                profiles["all_injectors_current_density_profile"] = (
                    profiles["all_injectors_current_density_profile"]
                    + profiles["single_current_density_profile"][idistrib]
                )
                profiles["all_injectors_electron_power_density_profile"] = (
                    profiles["all_injectors_electron_power_density_profile"]
                    + profiles["single_electron_power_density_profile"][idistrib]
                )
                profiles["all_injectors_ion_power_density_profile"] = (
                    profiles["all_injectors_ion_power_density_profile"]
                    + profiles["single_ion_power_density_profile"][idistrib]
                )
                profiles["all_injectors_total_power_density_profile"] = (
                    profiles["all_injectors_total_power_density_profile"]
                    + profiles["single_electron_power_density_profile"][idistrib]
                    + profiles["single_ion_power_density_profile"][idistrib]
                )

        logger.info(
            " Total power  = {:.2f}".format(profiles["all_injectors_total_power_waveform"][time_slice] * 1.0e-6) + " MW"
        )
        logger.info(
            " To electrons = {:.2f}".format(profiles["all_injectors_electron_power_waveform"][time_slice] * 1.0e-6)
            + " MW"
        )
        logger.info(
            " To ions      = {:.2f}".format(profiles["all_injectors_ion_power_waveform"][time_slice] * 1.0e-6) + " MW"
        )

        if self.cur_calc == 1:
            logger.info(
                " Total CD        = {:.2f}".format(profiles["all_injectors_current_waveform"][time_slice] * 1.0e-3)
                + " kA"
            )

        if len(self.active_distributions) != 0:
            for idistrib in range(self.ndistributions):
                if self.radial_grid_info[idistrib]["is_active"]:
                    logger.info(
                        " Distribution #"
                        + str(idistrib + 1)
                        + " - power = {:.2f}".format(
                            profiles["single_total_power_waveform"][idistrib][time_slice] * 1.0e-6
                        )
                        + " MW"
                    )
                    if self.cur_calc == 1:
                        logger.info(
                            " Distribution #"
                            + str(idistrib + 1)
                            + " - CD    = {:.2f}".format(
                                profiles["single_current_waveform"][idistrib][time_slice] * 1.0e-3
                            )
                            + " kA"
                        )
        return profiles

    def get_power_absorbedto_individual_ions(self, time_slice, verbose=False):
        """
        This function calculates the power absorbed by individual ions in a plasma simulation.

        Args:
            time_slice: The `time_slice` parameter in the `get_power_absorbedto_individual_ions` method is
                used to specify the index of the time step for which you want to calculate the power absorbed to
                individual ions.
            verbose: The `verbose` parameter

        Returns:
            The function `get_power_absorbedto_individual_ions` returns a dictionary `power_absorbed`
            containing information about the power absorbed to individual ions. The dictionary includes keys
            such as "all_injectors_total_power_waveform_per_ion", "element", and "compo_detail" with
            corresponding values calculated based on the input parameters and data within the function.
        """
        if self.is_radial_grid_info_processed is False:
            self.get_radial_grid_info(time_slice)
        import idstools.init_mendeleiev as mend

        table_mendeleiev = mend.create_table_mendeleiev()
        power_absorbed = {}

        nions = len(self.ids.distribution[0].global_quantities[time_slice].collisions.ion)
        # Power absorbed to individual ions
        power_absorbed["all_injectors_total_power_waveform_per_ion"] = [0] * nions
        power_absorbed["element"] = [0] * nions
        power_absorbed["compo_detail"] = 0
        for distrib_index in range(self.ndistributions):
            nions = len(self.ids.distribution[distrib_index].global_quantities[time_slice].collisions.ion)
            if self.radial_grid_info[distrib_index]["is_active"]:
                for ion_index in range(nions):
                    power_absorbed["all_injectors_total_power_waveform_per_ion"][ion_index] = (
                        power_absorbed["all_injectors_total_power_waveform_per_ion"][ion_index]
                        + self.ids.distribution[distrib_index]
                        .global_quantities[time_slice]
                        .collisions.ion[ion_index]
                        .power_thermal
                    )
                    if (
                        len(
                            self.ids.distribution[distrib_index]
                            .global_quantities[time_slice]
                            .collisions.ion[ion_index]
                            .element
                        )
                        > 0
                    ):
                        power_absorbed["compo_detail"] = 1
                        a = int(
                            self.ids.distribution[distrib_index]
                            .global_quantities[time_slice]
                            .collisions.ion[ion_index]
                            .element[0]
                            .a
                        )
                        z = int(
                            self.ids.distribution[distrib_index]
                            .global_quantities[time_slice]
                            .collisions.ion[ion_index]
                            .element[0]
                            .z_n
                        )
                        power_absorbed["element"][ion_index] = table_mendeleiev[z][a].element
                        logger.info(
                            "      - "
                            + z["element"][ion_index]
                            + " = {:.2f}".format(z["all_injectors_total_power_waveform_per_ion"][ion_index] * 1.0e-3)
                            + " kW"
                        )

        return power_absorbed
