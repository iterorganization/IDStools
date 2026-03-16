import logging

import numpy as np

try:
    import imaspy as imas
except ImportError:
    import imas

from idstools.compute.common import get_nearest_time
from idstools.compute.core_profiles import CoreProfilesCompute
from idstools.compute.edge_profiles import EdgeProfilesCompute
from idstools.compute.equilibrium import EquilibriumCompute
from idstools.utils.idshelper import get_available_ids_and_occurrences

logger = logging.getLogger("module")


class KineticProfilesCompute:
    IMPURITY_LIMIT = 0.001

    def __init__(self):
        self.connection = None
        self.available_ids = None
        self.edge_required = None

        self.core_profiles = None
        self.edge_profiles = None
        self.equilibrium = None

        self.is_core_profiles_present = True
        self.is_edge_profiles_present = False
        self.is_equilibrium_present = False

        self.time_array_edge_profiles = None
        self.time_index_edge_profiles = None
        self.time_value_edge_profiles = None

        self.time_array_length_core_profiles = None
        self.time_array_core_profiles = None
        self.time_index_core_profiles = None
        self.time_value_core_profiles = None

        self.time_array_equilibrium = None
        self.time_index_equilibrium = None
        self.time_value_equilibrium = None

        self.common_time_length = None
        self.common_time_array = None

        self.r_out_graph = False
        self.initialised = None

        self.is_composition_available = True
        self.gset = None
        self.nrho = None
        self.mrho = None
        self.erho = None
        self.nspecies_core = None
        self.nspecies_edge = None
        self.ti_flag = None
        self.ti_e_flag = None
        self.species_map = None

        self.xbeg = None
        self.xend = None
        self.rho_tor_norm = None

        self.a = None
        self.z = None
        self.n = None
        self.species_map = None
        self.volume = None
        self.zeff = None
        self.electron_density = None
        self.electron_temperature = None
        self.ti_flag = None
        self.ti_e_flag = None
        self.ion_temperature = None
        self.ion_density = None

        self.vphi_flag = None
        self.vphi_e_flag = None
        self.ion_vphi = None

        self.vpol_flag = None
        self.vpol_e_flag = None
        self.ion_vpol = None

        self.species = None
        self.nspec_over_ne = None

        self.profiles = None

        self.max_vphi = None
        self.min_vphi = None
        self.max_vpol = None
        self.min_vpol = None

        self.waveform = None

    def analyze(self, connection, time_value, edge_required, dd_update=False):
        self.connection = connection
        self.edge_required = edge_required
        self.available_ids = get_available_ids_and_occurrences(connection)
        self.initialised = self.check_idsses(dd_update)
        self.fill_idses(time_value)

        self.edge_profiles_compute = EdgeProfilesCompute(self.edge_profiles)
        self.core_profiles_compute = CoreProfilesCompute(self.core_profiles)
        self.equlibrium_compute = EquilibriumCompute(self.equilibrium)

        self.gset = self.getgset()
        (
            self.nrho,
            self.mrho,
            self.erho,
        ) = self.get_rho_tor_norm()
        self.nspecies_core, self.nspecies_edge = self.get_species()

        rho_or_r_outboard_profile = self.get_rho_or_r_outboard_profile()
        self.xbeg = rho_or_r_outboard_profile["xbeg"]
        self.xend = rho_or_r_outboard_profile["xend"]
        self.rho_tor_norm = rho_or_r_outboard_profile["rho_tor_norm"]

        self.nspecies_core, self.nspecies_core_edge = self.get_species()
        self.a = self.get_species_a_number()  # Species A number (not mandatory)
        self.z = self.get_species_z_number()  # Species Z number (not mandatory)
        self.n = self.get_species_atoms_n()  # Number of atoms per species (not mandatory)
        self.species_map = self.get_species_map()
        self.volume = self.get_volume_profile()  # Volume profile (not mandatory)
        self.zeff = self.get_zeff_profile()  # Zeff profile (not mandatory)
        self.electron_density = self.getne_profile()  # Ne profile (not mandatory)
        self.electron_temperature = self.gette_profile()  # Te profile (not mandatory)
        self.ti_flag, self.ti_e_flag = self.getti_flag()  # Ti profile (not mandatory)
        self.ion_temperature = self.get_ion_temperature()  # ion temerature
        self.ion_density = self.get_ion_density()  # Ni profile (not mandatory)
        vphi_profile = self.get_v_phi_profile()  # Vphi profile (not mandatory)
        self.vphi_flag = vphi_profile["vphi_flag"]
        self.vphi_e_flag = vphi_profile["vphi_e_flag"]
        self.ion_vphi = vphi_profile["ion_vphi"]
        vpol_profile = self.get_vpol_profile()  # Vpol profile (not mandatory)
        self.vpol_flag = vpol_profile["vpol_flag"]
        self.vpol_e_flag = vpol_profile["vpol_e_flag"]
        self.ion_vpol = vpol_profile["ion_vpol"]
        self.species = self.get_species_list()
        self.nspec_over_ne = self.get_n_spec_nver_ne()

        self.profiles = self.get_profiles()  # Create the dictionary defining the list of profiles

        velocity_profiles = self.get_min_max_velocity_profiles()  # Min and max of velocity profiles
        self.max_vphi = velocity_profiles["max_vphi"]
        self.min_vphi = velocity_profiles["min_vphi"]
        self.max_vpol = velocity_profiles["max_vpol"]
        self.min_vpol = velocity_profiles["min_vpol"]

        self.waveform = self.get_waveform()  # Create the dictionary defining the list of waveforms (central values)

    def get_ids(self, ids_name="", dd_update=False):
        """
        This function retrieves a specific IDS object based on the provided name and checks if it is
        present in the data-entry.

        Args:
            ids_name: The `ids_name` parameter is used to specify the name of the IDS (Intelligent Data
                Structure) that you want to retrieve. It is a string parameter that should correspond to the
                specific IDS structure you are interested in accessing.

        Returns:
            The function `get_ids` returns a tuple containing two values - `ids_object` and `ids_present`.
        """
        ids_present = False
        ids_object = None

        if ids_name:
            logger.info(f"--> retrieving ids {ids_name}")

            for idsname, occ in self.available_ids:
                if idsname == ids_name:
                    try:
                        if dd_update:
                            ids_object = imas.convert_ids(
                                self.connection.get(ids_name, occurrence=occ, autoconvert=False),
                                self.connection.factory.version,
                            )
                        else:
                            ids_object = self.connection.get(ids_name, occurrence=occ, lazy=True, autoconvert=False)

                        if ids_object.time is not None:
                            if len(ids_object.time) > 0:
                                ids_present = True
                        else:
                            logger.critical(f"No {ids_name}/{occ} IDS in the data-entry.")
                            ids_present = False
                            continue
                        break

                    except Exception as e:
                        logger.critical(f"The {ids_name} IDS is absent from the input data-entry. {e}")
                        ids_present = False
        return ids_object, ids_present

    def check_idsses(self, dd_update=False):
        """
        The function `check_idsses` checks for the presence of core profiles, edge profiles, and
        equilibrium data and logs appropriate messages based on the presence of the data.

        Returns:
            The function `check_idsses` is returning a boolean value. It returns `True` if either
            `is_core_profiles_present` or `is_edge_profiles_present` is True, indicating that data
            is present to plot. If both `is_core_profiles_present` and `is_edge_profiles_present`
            are False, it logs a critical message and returns `None`.
        """
        self.core_profiles, self.is_core_profiles_present = self.get_ids("core_profiles", dd_update)

        if self.edge_required:
            self.edge_profiles, self.is_edge_profiles_present = self.get_ids("edge_profiles", dd_update)
            if self.is_core_profiles_present:
                logger.info("Found adjoining edge_profiles. Will attempt to add to plots.")
            else:
                logger.info("Found edge_profiles IDS in data-entry. Will only plot edge data.")
        self.equilibrium, self.is_equilibrium_present = self.get_ids("equilibrium", dd_update)

        if not self.is_core_profiles_present and not self.is_edge_profiles_present:
            logger.critical("No data found to plot. --> Abort.")
            logger.critical("----> Aborted.")
            return None

        return True

    def fill_idses(self, time_slice):
        """
        This function fills in various profiles and data for a given time slice in a plasma physics
        simulation.

        Args:
            time_slice: The `fill_idses` method you provided seems to be handling the filling of various
                profiles and data based on a given time slice. The `time_slice` parameter is used to specify a
                part``icular time at which the data should be retrieved and processed.
        """
        # Search for adequate time slice for display
        if self.is_core_profiles_present:
            self.time_array_length_core_profiles = len(self.core_profiles.time)
            self.time_array_core_profiles = self.core_profiles.time
            self.time_index_core_profiles, self.time_value_core_profiles = get_nearest_time(
                self.time_array_core_profiles, time_slice
            )
            self.common_time_length = len(self.core_profiles.time)
            self.common_time_array = self.core_profiles.time
        else:
            self.common_time_length = len(self.edge_profiles.time)
            self.common_time_array = self.edge_profiles.time

        self.common_time_index, self.common_time_value = get_nearest_time(self.common_time_array, time_slice)
        # Read equilibrium data for this time slice if present
        if self.is_equilibrium_present:
            self.time_array_length_equilibrium = len(self.equilibrium.time)
            self.time_array_equilibrium = self.equilibrium.time
            self.time_index_equilibrium, self.time_value_equilibrium = get_nearest_time(
                self.time_array_equilibrium, time_slice
            )
        # Add 1D-profiles edge data if present

        if self.is_edge_profiles_present:
            self.time_array_length_edge_profiles = len(self.edge_profiles.time)
            self.time_array_edge_profiles = self.edge_profiles.time
            self.time_index_edge_profiles, self.time_value_edge_profiles = get_nearest_time(
                self.time_array_edge_profiles, time_slice
            )
            # Read edge_profile data for this time slice
            try:
                _ = self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                # teme = timeValueEdgeProfiles
            except Exception as e:
                logger.debug(f"{e}")
                logger.warning("No profiles_1d information found in edge_profiles IDS.")
                if self.is_equilibrium_present and len(self.equilibrium.time) > 0:
                    # tqme = timeValueEquilibrium
                    if (
                        len(self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.r_outboard) > 0
                        or not self.is_core_profiles_present
                    ):
                        try:
                            _ = self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                        except Exception as e:
                            logger.debug(f"{e}")
                            self.is_edge_profiles_present = False
                            logger.warning("No grid_ggd information found in edge_profiles IDS.")
                        try:
                            _ = self.edge_profiles.ggd[self.time_index_edge_profiles]
                        except Exception as e:
                            logger.debug(f"{e}")
                            self.is_edge_profiles_present = False
                            logger.warning("No ggd information found in edge_profiles IDS.")
                        if self.is_edge_profiles_present:
                            self.r_out_graph = True
                            logger.info("Attempting to use R_outboard coordinate instead.")
                    else:
                        if self.is_core_profiles_present:
                            self.is_edge_profiles_present = False
                else:
                    if self.is_core_profiles_present:
                        self.is_edge_profiles_present = False
                    else:
                        try:
                            _ = self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                        except Exception as e:
                            logger.debug(f"{e}")
                            self.is_edge_profiles_present = False
                            logger.warning("No grid_ggd information found in edge_profiles IDS.")
                        try:
                            _ = self.edge_profiles.ggd[self.time_index_edge_profiles]
                        except Exception as e:
                            logger.debug(f"{e}")
                            self.is_edge_profiles_present = False
                            logger.warning("No ggd information found in edge_profiles IDS.")
                        if self.is_edge_profiles_present:
                            self.r_out_graph = True
                            logger.info("Attempting to use R coordinate instead.")

    def getgset(self):
        """
        This function retrieves the outer midplane array index for edge profiles, with some additional
        checks and warnings.

        Returns:
            The function `getgset` is returning the variable `gset`.
        """
        if self.r_out_graph:
            gset = self.edge_profiles_compute.get_outer_midplane_array_index(self.time_index_edge_profiles)
            if gset is None:
                logger.warning("Abandoning edge plots !")
                self.is_edge_profiles_present = False
                self.r_out_graph = False
            try:
                if self.edge_profiles.midplane.index != 1 and self.r_out_graph and self.is_core_profiles_present:
                    logger.warning("Edge and core profile midplane coordinates are not aligned!")
            except Exception as e:
                logger.debug(f"{e}")
                logger.warning("Edge_profiles midplane location not specified! Coordinates may be misaligned.")
            return gset
        return None

    def get_rho_or_r_outboard_profile(self):
        """
        This function retrieves the rho_tor_norm profile for the outboard region based on core and edge
        profiles data.

        Returns:
            The function `get_rho_or_r_outboard_profile` returns a dictionary with keys `"xbeg"`,
            `"xend"`, and `"rho_tor_norm"`. The values associated with these keys are the variables `xbeg`,
            `xend`, and `rho_tor_norm` respectively.
        """
        xbeg = 99.0
        xend = 0
        rho_tor_norm = [0] * (self.nrho + self.erho)
        if not self.r_out_graph and self.is_core_profiles_present:
            if len(self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor_norm) > 0:
                for i in range(self.nrho):
                    rho_tor_norm[i] = self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor_norm[i]
            elif len(self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor) > 0:
                for i in range(self.nrho):
                    rho_tor_norm[i] = (
                        self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor[i]
                        / self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor[self.nrho - 1]
                    )
            xbeg = 0
            xend = 1
        elif self.is_core_profiles_present:
            for i in range(self.nrho):
                rho_tor_norm[i] = self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.r_outboard[
                    self.mrho + i
                ]
            xbeg = min(xbeg, rho_tor_norm[self.nrho - 1], rho_tor_norm[0])
            xend = max(xend, rho_tor_norm[self.nrho - 1], rho_tor_norm[0])

        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                if len(self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor_norm) > 0:
                    for i in range(self.erho):
                        rho_tor_norm[self.nrho + i] = self.edge_profiles.profiles_1d[
                            self.time_index_edge_profiles
                        ].rho_tor_norm[i]
                elif len(self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor) > 0:
                    for i in range(self.erho):
                        rho_tor_norm[self.nrho + i] = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles].grid.rho_tor[i]
                            / self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor[self.nrho - 1]
                        )
                xbeg = min(xbeg, rho_tor_norm[self.nrho + self.erho - 1], rho_tor_norm[0])
                xend = max(
                    xend,
                    rho_tor_norm[self.nrho + self.erho - 1],
                    rho_tor_norm[self.nrho],
                )
            else:
                if (
                    self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].dimension
                    == imas.ids_defs.EMPTY_INT
                ):
                    logger.debug("Dimensionality of Outer Midplane GGD subset is not defined !")
                    logger.debug("Assuming the grid subset is made of edges (dimensionality 2).")
                if self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].dimension == 1:
                    for i in range(self.erho):
                        ielem = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .grid_subset[self.gset]
                            .element[i]
                            .object[0]
                            .index
                        )
                        i1 = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[0]
                            .object[ielem - 1]
                            .nodes[0]
                        )
                        rho_tor_norm[self.nrho + i] = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[0]
                            .object[i1 - 1]
                            .geometry[0]
                        )
                        xbeg = min(xbeg, rho_tor_norm[0])
                        xend = max(xend, rho_tor_norm[self.nrho + i])
                elif (
                    self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].dimension == 2
                    or self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].dimension
                    == imas.ids_defs.EMPTY_INT
                ) and self.is_edge_profiles_present:
                    for i in range(self.erho):
                        ielem = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .grid_subset[self.gset]
                            .element[i]
                            .object[0]
                            .index
                        )
                        i1 = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[1]
                            .object[ielem - 1]
                            .nodes[0]
                        )
                        i2 = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[1]
                            .object[ielem - 1]
                            .nodes[1]
                        )
                        rho_tor_norm[self.nrho + i] = (
                            self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[0]
                            .object[i1 - 1]
                            .geometry[0]
                            + self.edge_profiles.grid_ggd[self.time_index_edge_profiles]
                            .space[0]
                            .objects_per_dimension[0]
                            .object[i2 - 1]
                            .geometry[0]
                        ) / 2
                        xbeg = min(xbeg, rho_tor_norm[0])
                        xend = max(xend, rho_tor_norm[self.nrho + i])
                else:
                    logger.warning(
                        f"Unexpected dimensionality of Outer Midplane GGD subset :"
                        f"{self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].dimension}"
                    )
                    logger.warning("Abandoning edge plots !")
                    self.is_edge_profiles_present = False
        return {"xbeg": xbeg, "xend": xend, "rho_tor_norm": rho_tor_norm}

    def get_species(self):
        """
        The function `get_species` determines the number of species present in core and edge profiles
        data, handling exceptions and logging warnings if necessary.

        Returns:
            The `get_species` method returns a tuple containing the number of species in the core profiles
            (`nspecies_core`) and the number of species in the edge profiles (`nspecies_edge`).
        """
        nspecies_core = 0
        if self.is_core_profiles_present:
            try:
                nspecies_core = len(self.core_profiles.profiles_1d[self.time_index_core_profiles].ion)
            except Exception as e:
                logger.debug(f"{e}")
                logger.critical(
                    f"core_profiles.profiles_1d[self.{self.time_index_core_profiles}].ion could not be read."
                )
                return None

        nspecies_edge = nspecies_core
        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                nspecies_edge = len(self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion)
            else:
                nspecies_edge = len(self.edge_profiles.ggd[self.time_index_edge_profiles].ion)
        if nspecies_core != nspecies_edge and self.is_core_profiles_present and self.is_edge_profiles_present:
            logger.warning("Warning: list of species in core and edge profiles data do not match!")
        if not self.is_core_profiles_present:
            nspecies_core = nspecies_edge

        return nspecies_core, nspecies_edge

    def get_species_a_number(self):
        """
        This function retrieves the 'a' attribute values for different species from core or edge
        profiles data and handles exceptions accordingly.

        Returns:
            The function `get_species_a_number` returns a list `a` containing integer values extracted
            from the attribute `a` of different elements in the core or edge profiles based on certain
            conditions. The values are read from either
            `core_profiles` or `edge_profiles`
        """
        a = [0] * self.nspecies_core
        if self.is_core_profiles_present:
            try:
                for ispecies in range(self.nspecies_core):
                    a[ispecies] = int(
                        self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].element[0].a
                    )
            except Exception as e:
                logger.debug(f"{e}")
                logger.warning("core_profiles.profiles_1d[:].ion[0].element[0].a could not be read.")
                self.is_composition_available = False  # plot_compo
        else:
            if not self.r_out_graph:
                try:
                    for ispecies in range(self.nspecies_core_edge):
                        a[ispecies] = int(
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[ispecies].element[0].a
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.profiles_1d[:].ion[0].element[0].a could not be read.")
                    self.is_composition_available = False
            else:
                try:
                    for ispecies in range(self.nspecies_core_edge):
                        a[ispecies] = int(
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[ispecies].element[0].a
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.ggd[:].ion[0].element[0].a could not be read.")
                    self.is_composition_available = False
        return a

    def get_species_z_number(self):
        """
        This function retrieves the Z number (atomic number) for each species in the core or edge
        profiles data.

        Returns:
            The `get_species_z_number` method returns a list `z` containing the atomic numbers of
            different species. The method first initializes the list `z` with zeros, then based on the
            availability of core profiles or edge profiles, it reads the atomic numbers of species from the
            corresponding profiles and populates the `z` list.
        """
        z = [0] * self.nspecies_core
        if self.is_core_profiles_present:
            try:
                for ispecies in range(self.nspecies_core):
                    z[ispecies] = int(
                        self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].element[0].z_n
                    )
            except Exception as e:
                logger.debug(f"{e}")
                logger.warning("core_profiles.profiles_1d[:].ion[0].element[0].z_n could not be read.")
                self.is_composition_available = False
        else:
            if not self.r_out_graph:
                try:
                    for ispecies in range(self.nspecies_edge):
                        z[ispecies] = int(
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[ispecies].element[0].z_n
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.profiles_1d[:].ion[0].element[0].z_n could not be read.")
                    self.is_composition_available = False
            else:
                try:
                    for ispecies in range(self.nspecies_edge):
                        z[ispecies] = int(
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[ispecies].element[0].z_n
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.ggd[:].ion[0].element[0].z_n could not be read.")
                    self.is_composition_available = False
        return z

    def get_species_atoms_n(self):
        """
        This function retrieves the number of atoms for each species from core or edge profiles, with a
        fallback value of 1 if the data cannot be read.

        Returns:
            The `get_species_atoms_n` method returns a list `n` containing the number of atoms for each
            species in the core or edge profiles. The method first initializes the list with 1 for each
            species, then attempts to read the number of atoms for each species from the core or edge
            profiles data.
        """
        n = [1] * self.nspecies_core
        if self.is_core_profiles_present:
            try:
                for ispecies in range(self.nspecies_core):
                    n[ispecies] = (
                        self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].element[0].atoms_n
                    )
            except Exception as e:
                logger.debug(f"{e}")
                logger.warning("core_profiles.profiles_1d[:].ion[0].element[0].atoms_n could not be read.")
                logger.warning("Value of 1 assumed.")
        else:
            if not self.r_out_graph:
                try:
                    for ispecies in range(self.nspecies_edge):
                        n[ispecies] = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                            .ion[ispecies]
                            .element[0]
                            .atoms_n
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.profiles_1d[:].ion[0].element[0].atoms_n could not be read.")
                    logger.warning("Value of 1 assumed.")
            else:
                try:
                    for ispecies in range(self.nspecies_edge):
                        n[ispecies] = (
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[ispecies].element[0].atoms_n
                        )
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("edge_profiles.ggd[:].ion[0].element[0].atoms_n could not be read.")
                    logger.warning("Value of 1 assumed.")
        return n

    def get_species_map(self):
        """
        The function `get_species_map` creates a mapping of species between core and edge profiles based
        on certain conditions.

        Returns:
            The `species_map` is being returned.
        """
        if self.is_edge_profiles_present:
            species_map = [-99] * self.nspecies_core
            for ispecies in range(self.nspecies_core):
                for jspecies in range(self.nspecies_edge):
                    if self.r_out_graph == 0:
                        if (
                            self.a[ispecies]
                            == int(
                                self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[jspecies].element[0].a
                            )
                            and self.z[ispecies]
                            == int(
                                self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                .ion[jspecies]
                                .element[0]
                                .z_n
                            )
                            and self.n[ispecies]
                            == self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                            .ion[jspecies]
                            .element[0]
                            .atoms_n
                        ):
                            species_map[ispecies] = jspecies
                    else:
                        if (
                            self.a[ispecies]
                            == int(self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].element[0].a)
                            and self.z[ispecies]
                            == int(self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].element[0].z_n)
                            and self.n[ispecies]
                            == self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].element[0].atoms_n
                        ):
                            species_map[ispecies] = jspecies
                if species_map[ispecies] == -99 and self.is_core_profiles_present == 1:
                    logger.warning(
                        "Core_profiles species "
                        + self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].label
                        + " has no partner in edge_profiles!"
                    )
            self.species_map = species_map
            return species_map
        return None

    def get_rho_tor_norm(self):
        """
        This function calculates and returns the values of nrho, mrho, and erho based on certain
        conditions and data availability.

        Returns:
            The function `get_rho_tor_norm` returns three values: `nrho`, `mrho`, and `erho`.
        """
        nrho = 0
        mrho = 0
        if not self.r_out_graph and self.is_core_profiles_present:
            nrho = self.core_profiles_compute.getnrho(self.time_index_core_profiles)
            if nrho is None or nrho == 0:
                logger.error("core_profiles.profiles_1d[:].grid.rho_tor_norm and rho_tor are empty.")
                logger.error("----> Aborted.")
                exit()
        else:
            if self.is_core_profiles_present:
                if len(self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.rho_tor_norm) == len(
                    self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.rho_tor_norm
                ):
                    nrho = len(self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.rho_tor_norm)
                else:
                    mrho = self.equlibrium_compute.getmrho()
                    nrho = len(self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.rho_tor_norm) - mrho

        erho = 0
        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                erho = self.core_profiles_compute.getnrho()
                if nrho is None or nrho == 0:
                    logger.warning("edge_profiles.profiles_1d[:].grid.rho_tor_norm and rho_tor are empty.")
            else:
                erho = len(self.edge_profiles.grid_ggd[self.time_index_edge_profiles].grid_subset[self.gset].element)
        return nrho, mrho, erho

    def get_volume_profile(self):
        """
        The function `get_volume_profile` retrieves volume data from core and edge profiles, handling
        different scenarios based on the availability of data.

        Returns:
            The `get_volume_profile` method returns a list `volume` containing volume values for the core
            and edge profiles. The volume values are obtained from different sources based on the conditions
            and availability of data. The method populates the `volume` list with volume values for the core
            profiles, edge profiles, or equilibrium data, depending on the conditions and data availability.
        """
        volume = [0] * (self.nrho + self.erho)
        if self.is_core_profiles_present:
            if len(self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.volume) == self.nrho:
                for i in range(self.nrho):
                    volume[i] = self.core_profiles.profiles_1d[self.time_index_core_profiles].grid.volume[i]
            else:
                try:
                    for i in range(self.nrho):
                        volume[i] = self.equilibrium.time_slice[self.time_index_equilibrium].profiles_1d.volume[i]
                    if len(volume) == len(
                        self.core_profiles.profiles_1d[self.time_index_core_profiles].electrons.density
                    ):
                        logger.warning("   core_profiles.profiles_1d[:].grid.volume could not be read.")
                        logger.warning("   ----> equilibrium.time_slice[:].profiles_1d.volume used instead.")
                        logger.warning("   (possible because the resolution is the same, but maybe not correct)")
                except Exception as e:
                    logger.debug(f"{e}")
                    logger.warning("core_profiles.profiles_1d[:].grid.volume could not be read.")
                    self.is_composition_available = False
        if self.is_edge_profiles_present and not self.r_out_graph:
            for i in range(self.erho):
                volume[self.nrho + i] = self.edge_profiles.profiles_1d[self.time_index_edge_profiles].grid.volume[i]
        return volume

    def get_zeff_profile(self):
        """
        The function `get_zeff_profile` retrieves Zeff profiles from core and edge plasma profiles,
        handling potential data mismatches.

        Returns:
            The function `get_zeff_profile` returns a list `zeff` containing Z-effective values for both
            core and edge profiles. The list is constructed by first initializing it with zeros, then
            populating it with Z-effective values from core and edge profiles if they are present. The
            Z-effective values are read from the respective profile objects and stored in the `zeff` list
            based on the indices
        """
        zeff = [0] * (self.nrho + self.erho)
        if self.is_core_profiles_present:
            _zeff = self.core_profiles.profiles_1d[self.time_index_core_profiles].zeff.value
            if len(_zeff) != self.nrho:
                logger.warning("core_profiles.profiles_1d[:].zeff could not be read.")
                logger.warning(f"Size mismatch: rho_tor_norm = {self.nrho}, " f"zeff = {len(_zeff)}")
                _zeff = np.asarray([np.nan] * self.nrho)
            for i in range(self.nrho):
                zeff[i] = _zeff[i]
        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                _zeff = self.edge_profiles.profiles_1d[self.time_index_edge_profiles].zeff.value
                if len(_zeff) < 1:
                    logger.warning("edge_profiles.profiles_1d[:].zeff could not be read.")
                    _zeff = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    zeff[self.nrho + i] = _zeff[i]
            else:
                _gset = self.edge_profiles.ggd[self.time_index_edge_profiles].zeff[self.gset].values
                if len(_gset) < 1:
                    logger.warning("edge_profiles.ggd[:].zeff could not be read.")
                    _gset = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    zeff[self.nrho + i] = _gset[i]
        return zeff

    def getne_profile(self):
        """
        This function retrieves electron density profiles from core and edge plasma profiles data.

        Returns:
            The function `getne_profile` returns a list of electron density values. The electron density
            values are collected from different sources based on the conditions specified in the function.
            The returned list contains electron density values for both core and edge profiles, with NaN
            values filled in case of missing data.
        """
        electron_density = [0] * (self.nrho + self.erho)
        if self.is_core_profiles_present:
            _density = self.core_profiles.profiles_1d[self.time_index_core_profiles].electrons.density.value
            if len(_density) != self.nrho:
                logger.warning("core_profiles.profiles_1d[:].electrons.density could not be read.")
                logger.warning(f"Size mismatch: rho_tor_norm = {self.nrho}, electrons.density =" f"{len(_density)}")
                _density = np.asarray([np.nan] * self.nrho)
            for i in range(self.nrho):
                electron_density[i] = _density[i]
        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                _density = self.core_profiles.profiles_1d[self.time_index_edge_profiles].electrons.density.value
                if len(_density) < 1:
                    logger.warning("edge_profiles.profiles_1d[:].electrons.density could not be read.")
                    _density = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    electron_density[self.nrho + i] = _density[i]
            else:
                _gset = self.edge_profiles.ggd[self.time_index_edge_profiles].electrons.density[self.gset].values
                if len() < 1:
                    logger.warning("edge_profiles.ggd[:].electrons.density could not be read.")
                    _gset = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    electron_density[self.nrho + i] = _gset[i]
        return electron_density

    def gette_profile(self):
        """
        This function retrieves electron temperature profiles from core and edge plasma profiles,
        converting the values to Kelvin.

        Returns:
            The function `gette_profile` returns a list `electron_temperature` containing electron
            temperatures. The electron temperatures are extracted from core and edge profiles data,
            converted to keV, and stored in the list based on the specified
            conditions. The list is then returned as the output of the function.
        """
        electron_temperature = [0] * (self.nrho + self.erho)
        if self.is_core_profiles_present:
            _temperature = self.core_profiles.profiles_1d[self.time_index_core_profiles].electrons.temperature.value
            if len(_temperature) != self.nrho:
                logger.warning("core_profiles.profiles_1d[:].electrons.temperature could not be read.")
                logger.warning(
                    f"Size mismatch: rho_tor_norm = {self.nrho}, electrons.temperature = " f"{len(_temperature)}"
                )
                _temperature = np.asarray([np.nan] * self.nrho)
            for i in range(self.nrho):
                electron_temperature[i] = _temperature[i] * 1.0e-3
        if self.is_edge_profiles_present:
            if not self.r_out_graph:
                _temperature = self.edge_profiles.profiles_1d[self.time_index_edge_profiles].electrons.temperature
                if len(_temperature) < 1:
                    logger.warning("edge_profiles.profiles_1d[:].electrons.temperature could not be read.")
                    _temperature = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    electron_temperature[self.nrho + i] = _temperature[i] * 1.0e-3
            else:
                _gset = self.edge_profiles.ggd[self.time_index_edge_profiles].electrons.temperature[self.gset].values
                if len() < 1:
                    logger.warning("edge_profiles.ggd[:].electrons.temperature could not be read.")
                    _gset = np.asarray([np.nan] * self.erho)
                for i in range(self.erho):
                    electron_temperature[self.nrho + i] = _gset[i] * 1.0e-3
        return electron_temperature

    def getti_flag(self):
        """
        The function `getti_flag` checks and sets flags based on the availability and consistency of
        temperature data in core and edge profiles.

        Returns:
            The `getti_flag` method returns the values of `ti_flag` and `ti_e_flag` after performing
            certain checks and operations within the method.
        """
        ti_flag = 0
        if self.is_core_profiles_present:
            t_i_average = self.core_profiles.profiles_1d[self.time_index_core_profiles].t_i_average.value
            if len(t_i_average) != self.nrho:
                logger.warning("core_profiles.profiles_1d[:].t_i_average could not be read.")
                logger.warning(f"Size mismatch: rho_tor_norm = {self.nrho}, t_i_average = " f"{len(t_i_average)}")
                t_i_average = np.asarray([np.nan] * self.nrho)
            else:
                ti_flag = 1
        ti_e_flag = 0
        if self.is_edge_profiles_present:

            if not self.r_out_graph:
                t_i_average = self.edge_profiles.profiles_1d[self.time_index_edge_profiles].t_i_average.value
                if len() < 1:
                    logger.warning("edge_profiles.profiles_1d[:].t_i_average could not be read.")
                    t_i_average = np.asarray([np.nan] * self.erho)
                else:
                    ti_e_flag = 1
            else:
                t_i_average = self.edge_profiles.ggd[self.time_index_edge_profiles].t_i_average[self.gset].values
                if len() < 1:
                    logger.warning("edge_profiles.ggd[:].t_i_average could not be read.")
                    t_i_average = np.asarray([np.nan] * self.erho)
                else:
                    ti_e_flag = 1

        if ti_flag == 0:
            for ispecies in range(self.nspecies_core):
                if self.is_core_profiles_present:
                    temp = self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].temperature.value
                    if len(temp) != self.nrho:
                        logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].temperature could not be read.")
                        logger.warning(
                            f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].temperature = " f"{len(temp)}"
                        )
                        temp = np.asarray([np.nan] * self.nrho)
                    else:
                        ti_flag = 2
                if self.is_edge_profiles_present and ti_e_flag == 0:
                    jspecies = self.species_map[ispecies]
                    if jspecies != -99:
                        if not self.r_out_graph:
                            temperature = (
                                self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                .ion[jspecies]
                                .temperature.value
                            )
                            if len(temperature) < 1:
                                if ti_e_flag != 1:
                                    logger.warning(
                                        f"edge_profiles.profiles_1d[:].ion[{jspecies}].temperature could not be read."
                                    )
                                    temperature = np.asarray([np.nan] * self.erho)
                            else:
                                ti_e_flag = 2
                        else:
                            temperature = (
                                self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].temperature.value
                            )
                            if len(temperature) < 1:
                                if ti_e_flag != 1:
                                    logger.warning("edge_profiles.ggd[:].ion[:].temperature could not be read.")
                                    temperature[self.gset].values = np.asarray([np.nan] * self.erho)
                            else:
                                ti_e_flag = 2

        logger.info(f"Ti_flag : {ti_flag}, Ti_e_flag : {ti_e_flag}")
        self.ti_flag = ti_flag
        self.ti_e_flag = ti_e_flag
        return ti_flag, ti_e_flag

    def get_ion_temperature(self):
        """
        This function retrieves ion temperatures from core and edge profiles and returns them in a list.

        Returns:
            The function `get_ion_temperature` returns a list of ion temperatures. The list is populated
            based on certain conditions and calculations involving the input parameters and attributes of
            the object.
        """
        ion_temperature = [0] * (self.nrho + self.erho)
        if self.ti_flag == 1:
            for i in range(self.nrho):
                ion_temperature[i] = (
                    self.core_profiles.profiles_1d[self.time_index_core_profiles].t_i_average[i] * 1.0e-3
                )
        elif self.ti_flag == 2:
            for i in range(self.nrho):
                ion_temperature[i] = (
                    self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[0].temperature[i] * 1.0e-3
                )
        if self.is_edge_profiles_present:
            if self.ti_e_flag == 1:
                if not self.r_out_graph:
                    for i in range(self.erho):
                        ion_temperature[self.nrho + i] = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles].t_i_average[i] * 1.0e-3
                        )
                else:
                    for i in range(self.erho):
                        ion_temperature[self.nrho + i] = (
                            self.edge_profiles.ggd[self.time_index_edge_profiles].t_i_average[self.gset].values[i]
                            * 1.0e-3
                        )
            elif self.ti_e_flag == 2:
                if not self.r_out_graph:
                    for i in range(self.erho):
                        ion_temperature[self.nrho + i] = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[0].temperature[i] * 1.0e-3
                        )
                else:
                    for i in range(self.erho):
                        ion_temperature[self.nrho + i] = (
                            self.edge_profiles.ggd[self.time_index_edge_profiles]
                            .ion[0]
                            .temperature[self.gset]
                            .values[i]
                            * 1.0e-3
                        )
        return ion_temperature

    def get_ion_density(self):
        """
        This function retrieves ion density data from core and edge profiles, handling different cases
        and logging warnings for any issues encountered.

        Returns:
            The `get_ion_density` method returns a dictionary `ion_density` containing ion density values
            for each species at different radial positions.
        """
        ion_density = {}
        for ispecies in range(self.nspecies_core):
            ion_density[ispecies] = [0] * (self.nrho + self.erho)
            if self.is_core_profiles_present:
                density = self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].density
                if len(density) != self.nrho:
                    logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].density could not be read.")
                    logger.warning(
                        f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].density = " f"{len(density)}"
                    )
                    density = np.asarray([np.nan] * self.nrho)
                for i in range(self.nrho):
                    ion_density[ispecies][i] = density[i]
            if self.is_edge_profiles_present:
                jspecies = self.species_map[ispecies]
                if jspecies != -99:
                    if not self.r_out_graph:
                        multiple_states_flag = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                            .ion[jspecies]
                            .multiple_states_flag
                        )

                        if multiple_states_flag == 0:
                            _density = (
                                self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                .ion[jspecies]
                                .density.value
                            )
                            if len(_density) < 1:
                                logger.warning(
                                    f"edge_profiles.profiles_1d[:].ion[{jspecies}].density could not be read."
                                )
                                _density = np.asarray([np.nan] * self.erho)
                            for i in range(self.erho):
                                ion_density[ispecies][self.nrho + i] = _density[i]
                        else:
                            for istate in range(
                                len(self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                _density = (
                                    self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .state[istate]
                                    .density.value
                                )
                                if len(_density) < 1:
                                    logger.warning(
                                        f"edge_profiles.profiles_1d[:].ion[{jspecies}].state[{istate}].density "
                                        f"could not be read."
                                    )
                                    _density = np.asarray([0] * self.erho)
                                for i in range(self.erho):
                                    ion_density[ispecies][self.nrho + i] = (
                                        ion_density[ispecies][self.nrho + i] + _density[i]
                                    )
                    else:
                        if (
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].multiple_states_flag
                            == 0
                        ):
                            _density = (
                                self.edge_profiles.ggd[self.time_index_edge_profiles]
                                .ion[jspecies]
                                .density[self.gset]
                                .values
                            )
                            if len() < 1:
                                logger.warning(f"edge_profiles.ggd[:].ion[{jspecies}.density could not be read.")
                                _density = np.asarray([np.nan] * self.erho)
                            for i in range(self.erho):
                                ion_density[ispecies][self.nrho + i] = _density[i]
                        else:
                            for istate in range(
                                len(self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                _density = (
                                    self.edge_profiles.ggd[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .state[istate]
                                    .density.value
                                )
                                if len(_density) < 1:
                                    logger.warning(
                                        f"edge_profiles.ggd[:].ion[{jspecies}].state[{istate}].density "
                                        f"could not be read."
                                    )
                                    _density = np.asarray([0] * self.erho)
                                for i in range(self.erho):
                                    ion_density[ispecies][self.nrho + i] = (
                                        ion_density[ispecies][self.nrho + i] + _density.values[i]
                                    )
        return ion_density

    def get_v_phi_profile(self):
        """
        This function retrieves toroidal velocity profiles for ions from core and edge plasma profiles.

        Returns:
            The function `get_v_phi_profile` returns a dictionary with three keys:
            1. "vphi_flag": Indicates the status of the toroidal velocity for the core profiles. It can have
            values 0, 1, or 2.
            2. "vphi_e_flag": Indicates the status of the toroidal velocity for the edge profiles. It can
            have values 0, 1
        """
        vphi_flag = 0
        vphi_e_flag = 0
        ion_vphi = {}
        for ispecies in range(self.nspecies_core):
            ion_vphi[ispecies] = [0] * (self.nrho + self.erho)
            if self.is_core_profiles_present:
                vphioid = self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].velocity.toroidal
                if len(vphioid) != self.nrho:
                    logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].velocity.toroidal could not be read.")
                    logger.warning(
                        f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].velocity.toroidal = "
                        f"{len(vphioid)}"
                    )
                    vphioid = np.asarray([np.nan] * self.nrho)
                else:
                    vphi_flag = 1
                    for i in range(self.nrho):
                        ion_vphi[ispecies][i] = abs(vphioid[i])
                if hasattr(self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies], "velocity_tor"):
                    vphi = self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].velocity_tor
                    if len(vphi) != self.nrho:
                        logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].velocity_tor could not be read.")
                        logger.warning(
                            f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].velocity_tor = " f"{len(vphi)}"
                        )
                        vphi = np.asarray([np.nan] * self.nrho)
                    else:
                        if vphi_flag == 0:
                            vphi_flag = 2
                            for i in range(self.nrho):
                                ion_vphi[ispecies][i] = abs(vphi[i])
            if self.is_edge_profiles_present:
                jspecies = self.species_map[ispecies]
                if jspecies != -99:
                    if not self.r_out_graph:
                        multiple_states_flag = (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                            .ion[jspecies]
                            .multiple_states_flag
                        )
                        if multiple_states_flag == 0:
                            try:
                                vphi = (
                                    self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .velocity.toroidal
                                )
                                if len(vphi) == self.erho:
                                    for i in range(self.erho):
                                        ion_vphi[ispecies][self.nrho + i] = abs(vphi[i])
                                    vphi_e_flag = 1
                            except Exception as e:
                                logger.debug(f"{e}")
                                logger.warning(
                                    f"edge_profiles.profiles_1d[:].ion[{jspecies}].velocity.toroidal could not be read."
                                )
                            if vphi_e_flag != 1:
                                try:
                                    vphi = (
                                        self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                        .ion[jspecies]
                                        .velocity_tor
                                    )
                                    if len(vphi) == self.erho:
                                        for i in range(self.erho):
                                            ion_vphi[ispecies][self.nrho + i] = abs(vphi[i])
                                        vphi_e_flag = 2
                                except Exception as e:
                                    logger.debug(f"{e}")
                                    logger.warning(
                                        f"edge_profiles.profiles_1d[:].ion[{jspecies}].velocity_tor could not be read."
                                    )
                        else:
                            for istate in range(
                                len(self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                try:
                                    vphi = (
                                        self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                        .ion[jspecies]
                                        .state[istate]
                                        .velocity.toroidal
                                    )
                                    if len(vphi) == self.erho:
                                        for i in range(self.erho):
                                            if self.ion_density[ispecies][self.nrho + i] > 0.0:
                                                ion_vphi[ispecies][self.nrho + i] = (
                                                    ion_vphi[ispecies][self.nrho + i]
                                                    + abs(vphi[i])
                                                    * self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                                    .ion[jspecies]
                                                    .state[istate]
                                                    .density[i]
                                                    / self.ion_density[ispecies][self.nrho + i]
                                                )
                                        vphi_e_flag = 1
                                except Exception as e:
                                    logger.debug(f"{e}")
                                    logger.warning(
                                        f"edge_profiles.profiles_1d[:].ion[{jspecies}].state[{istate}]."
                                        f"velocity.toroidal could not be read."
                                    )
                                if vphi_e_flag != 1:
                                    try:
                                        vphi = (
                                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                            .ion[jspecies]
                                            .state[istate]
                                            .velocity_tor
                                        )
                                        if len(vphi) == self.erho:
                                            for i in range(self.erho):
                                                if self.ion_density[ispecies][self.nrho + i] > 0.0:
                                                    ion_vphi[ispecies][self.nrho + i] = (
                                                        ion_vphi[ispecies][self.nrho + i]
                                                        + abs(vphi[i])
                                                        * self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                                        .ion[jspecies]
                                                        .state[istate]
                                                        .density[i]
                                                        / self.ion_density[ispecies][self.nrho + i]
                                                    )
                                            vphi_e_flag = 2
                                    except Exception as e:
                                        logger.debug(f"{e}")
                                        logger.warning(
                                            f"edge_profiles.profiles_1d[:].ion[{jspecies}].state[{istate}]."
                                            f"velocity_tor could not be read."
                                        )

                    else:
                        if (
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].multiple_states_flag
                            == 0
                        ):
                            try:
                                toroidal = (
                                    self.edge_profiles.ggd[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .velocity[self.gset]
                                    .toroidal
                                )
                                if len(toroidal) == self.erho:
                                    for i in range(self.erho):
                                        ion_vphi[ispecies][self.nrho + i] = abs(toroidal[i])
                                    vphi_e_flag = 1
                            except Exception as e:
                                logger.debug(f"{e}")
                                logger.warning(
                                    f"edge_profiles.ggd[:].ion[{jspecies}].velocity.toroidal could not be read."
                                )
                        else:
                            for istate in range(
                                len(self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                try:
                                    toroidal = (
                                        self.edge_profiles.ggd[self.time_index_edge_profiles]
                                        .ion[jspecies]
                                        .state[istate]
                                        .velocity[self.gset]
                                        .toroidal
                                    )
                                    if len(toroidal) == self.erho:
                                        for i in range(self.erho):
                                            if self.ion_density[ispecies][self.nrho + i] > 0:
                                                ion_vphi[ispecies][self.nrho + i] = (
                                                    ion_vphi[ispecies][self.nrho + i]
                                                    + abs(toroidal[i])
                                                    * self.edge_profiles.ggd[self.time_index_edge_profiles]
                                                    .ion[jspecies]
                                                    .state[istate]
                                                    .density[self.gset]
                                                    .values[i]
                                                    / self.ion_density[ispecies][self.nrho + i]
                                                )
                                        vphi_e_flag = 1
                                except Exception as e:
                                    logger.debug(f"{e}")
                                    logger.warning(
                                        f"edge_profiles.ggd[:].ion[{jspecies}].state[{istate}]."
                                        f"velocity.toroidal could not be read."
                                    )

        logger.debug(f"Vphi_flag : {vphi_flag}, Vphi_e_flag : {vphi_e_flag}")
        return {
            "vphi_flag": vphi_flag,
            "vphi_e_flag": vphi_e_flag,
            "ion_vphi": ion_vphi,
        }

    def get_vpol_profile(self):
        """
        The `get_vpol_profile` function retrieves poloidal velocity profiles for ions from core and edge
        plasma profiles.

        Returns:
            The `get_vpol_profile` method returns a dictionary with three keys:
            1. "vpol_flag": an integer indicating the status of the poloidal velocity calculation for the
            ions in the core and edge profiles.
            2. "vpol_e_flag": an integer indicating the status of the poloidal velocity calculation for the
            edge profiles.
            3. "ion_vpol": a dictionary containing the calculated pol
        """
        vpol_flag = 0
        vpol_e_flag = 0
        ion_vpol = {}
        for ispecies in range(self.nspecies_core):
            ion_vpol[ispecies] = [0] * (self.nrho + self.erho)
            if self.is_core_profiles_present:
                vpoloidal = (
                    self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].velocity.poloidal
                )
                if len(vpoloidal) != self.nrho:
                    logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].velocity.poloidal could not be read.")
                    logger.warning(
                        f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].velocity.poloidal ="
                        f"{len(vpoloidal)}"
                    )
                    vpoloidal = np.asarray([np.nan] * self.nrho)
                else:
                    vpol_flag = 1
                    for i in range(self.nrho):
                        ion_vpol[ispecies][i] = abs(vpoloidal[i])
                if hasattr(self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies], "velocity_pol"):
                    vpol = self.core_profiles.profiles_1d[self.time_index_core_profiles].ion[ispecies].velocity_pol
                    if len(vpol) != self.nrho:
                        logger.warning(f"core_profiles.profiles_1d[:].ion[{ispecies}].velocity_pol could not be read.")
                        logger.warning(
                            f"Size mismatch: rho_tor_norm = {self.nrho}, ion[{ispecies}].velocity_pol = " f"{len(vpol)}"
                        )
                        vpol = np.asarray([np.NaN] * self.nrho)
                    else:
                        if vpol_flag == 0:
                            vpol_flag = 2
                            for i in range(self.nrho):
                                ion_vpol[ispecies][i] = abs(vpol[i])
            if self.is_edge_profiles_present:
                jspecies = self.species_map[ispecies]
                if jspecies != -99:
                    if not self.r_out_graph:
                        if (
                            self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                            .ion[jspecies]
                            .multiple_states_flag
                            == 0
                        ):
                            try:
                                poloidal = (
                                    self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .velocity.poloidal
                                )
                                if len(poloidal) == self.erho:
                                    for i in range(self.erho):
                                        ion_vpol[ispecies][self.nrho + i] = abs(poloidal[i])
                                    vpol_e_flag = 1
                            except Exception as e:
                                logger.debug(f"{e}")
                                logger.warning(
                                    f"edge_profiles.profiles_1d[:].ion[{jspecies}].velocity.poloidal could not be read."
                                )
                        else:
                            for istate in range(
                                len(self.edge_profiles.profiles_1d[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                try:
                                    poloidal = (
                                        self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                        .ion[jspecies]
                                        .state[istate]
                                        .velocity.poloidal
                                    )
                                    if len(poloidal) == self.erho:
                                        for i in range(self.erho):
                                            if self.ion_density[ispecies][self.nrho + i] > 0:
                                                ion_vpol[ispecies][self.nrho + i] = (
                                                    ion_vpol[ispecies][self.nrho + i]
                                                    + abs(poloidal[i])
                                                    * self.edge_profiles.profiles_1d[self.time_index_edge_profiles]
                                                    .ion[jspecies]
                                                    .state[istate]
                                                    .density[i]
                                                    / self.ion_density[ispecies][self.nrho + i]
                                                )
                                        vpol_e_flag = 1
                                except Exception as e:
                                    logger.debug(f"{e}")
                                    logger.warning(
                                        f"edge_profiles.profiles_1d[:].ion[{jspecies}].state[{istate}]."
                                        f"velocity.poloidal could not be read."
                                    )
                    else:
                        if (
                            self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].multiple_states_flag
                            == 0
                        ):
                            try:
                                poloidal = (
                                    self.edge_profiles.ggd[self.time_index_edge_profiles]
                                    .ion[jspecies]
                                    .velocity[self.gset]
                                    .poloidal
                                )
                                if len(poloidal) == self.erho:
                                    for i in range(self.erho):
                                        ion_vpol[ispecies][self.nrho + i] = abs(poloidal[i])
                                    vpol_e_flag = 1
                            except Exception as e:
                                logger.debug(f"{e}")
                                logger.warning(
                                    "edge_profiles.ggd[:].ion[{jspecies}].velocity.poloidal could not be read."
                                )
                        else:
                            for istate in range(
                                len(self.edge_profiles.ggd[self.time_index_edge_profiles].ion[jspecies].state)
                            ):
                                try:
                                    poloidal = (
                                        self.edge_profiles.ggd[self.time_index_edge_profiles]
                                        .ion[jspecies]
                                        .state[istate]
                                        .velocity[self.gset]
                                        .poloidal
                                    )
                                    if len(poloidal) == self.erho:
                                        for i in range(self.erho):
                                            if self.ion_density[ispecies][self.nrho + i] > 0:
                                                ion_vpol[ispecies][self.nrho + i] = (
                                                    ion_vpol[ispecies][self.nrho + i]
                                                    + abs(poloidal[i])
                                                    * self.edge_profiles.ggd[self.time_index_edge_profiles]
                                                    .ion[jspecies]
                                                    .state[istate]
                                                    .density[self.gset]
                                                    .values[i]
                                                    / self.ion_density[ispecies][self.nrho + i]
                                                )
                                        vpol_e_flag = 1
                                except Exception as e:
                                    logger.debug(f"{e}")
                                    logger.warning(
                                        f"edge_profiles.ggd[:].ion[{jspecies}].state[{istate}]."
                                        f"velocity.poloidal could not be read."
                                    )

        logger.debug(f"Vpol_flag : {vpol_flag}, Vpol_e_flag : {vpol_e_flag}")
        return {
            "vpol_flag": vpol_flag,
            "vpol_e_flag": vpol_e_flag,
            "ion_vpol": ion_vpol,
        }

    def get_species_list(self):
        """
        This function retrieves a list of species based on certain conditions and data sources.

        Returns:
            A list of species based on the conditions specified in the code snippet. If the number of core
            species is greater than 0, the function will return a list of species either from the Mendeleiev
            table or from core profiles or edge profiles based on certain conditions. If the number of core
            species is not greater than 0, the function will return None.
        """
        import idstools.init_mendeleiev as mend

        # Mendeleiev table
        table_mendeleiev = mend.create_table_mendeleiev()
        if any(value == imas.ids_defs.EMPTY_INT for value in self.z):
            logger.error(f"core_profiles.profiles_1d[].ion[].element[].z_n" f" values are not available {self.z}")
            return None
        if self.nspecies_core > 0:
            # Plasma composition
            species = []
            for ispecies in range(self.nspecies_core):
                if self.n[ispecies] == 1:
                    species.append(table_mendeleiev[self.z[ispecies]][self.a[ispecies]].element)
                else:
                    if self.is_core_profiles_present:
                        _coreprofiles_profile_1d_ion = self.core_profiles.profiles_1d[
                            self.time_index_core_profiles
                        ].ion[ispecies]
                        if "label" in dir(_coreprofiles_profile_1d_ion):
                            species.append(_coreprofiles_profile_1d_ion.label.value)
                        elif "name" in dir(_coreprofiles_profile_1d_ion):
                            species.append(_coreprofiles_profile_1d_ion.name.value)
                    else:
                        if not self.r_out_graph:
                            _edgeprofiles_profile_1d_ion = self.edge_profiles.profiles_1d[
                                self.time_index_edge_profiles
                            ].ion[ispecies]
                            if "label" in dir(_edgeprofiles_profile_1d_ion):
                                species.append(_edgeprofiles_profile_1d_ion.label.value)
                            elif "name" in dir(_edgeprofiles_profile_1d_ion):
                                species.append(_edgeprofiles_profile_1d_ion.name.value)
                        else:
                            _edgeprofiles_ggd_ion = self.edge_profiles.ggd[self.time_index_edge_profiles].ion[ispecies]
                            if "label" in dir(_edgeprofiles_ggd_ion):
                                species.append(_edgeprofiles_ggd_ion.label.value)
                            elif "name" in dir(_edgeprofiles_ggd_ion):
                                species.append(_edgeprofiles_ggd_ion.name.value)

            return species
        return None

    def get_n_spec_nver_ne(self):
        """
        This function calculates and displays plasma composition with species concentrations based on
        core profiles and mapping to edge species.

        Returns:
            The function `get_n_spec_nver_ne` returns the list `nspec_over_ne`, which contains the
            calculated values for the ratio of species density to electron density for each species in the
            core profiles. If the conditions specified in the function are not met, the function returns a
            list of zeros with the same length as the number of species in the core profiles.
        """
        if (self.nspecies_core > 0) and self.is_composition_available:
            if self.is_edge_profiles_present and self.is_core_profiles_present:
                logger.debug("Species_mapping :")
                for ispecies in range(self.nspecies_core):
                    if self.species_map[ispecies] != -99:
                        logger.debug(
                            f"Core species {ispecies} is {self.species[ispecies]} and maps to edge species "
                            f"{self.species_map[ispecies]}"
                        )
                    else:
                        logger.debug(
                            f"Core species {ispecies} is {self.species[ispecies]} and does not map to edge species"
                        )

            # Species concentrations
            ntot = 0
            imax = -99
            species_density = [0] * self.nspecies_core
            max_density = -999.0
            nspec_over_ntot = [0] * self.nspecies_core
            nspec_over_ne = [0] * self.nspecies_core
            nspec_over_nmaj = [0] * self.nspecies_core
            if self.is_core_profiles_present:
                for ispecies in range(self.nspecies_core):
                    species_density[ispecies] = sum(
                        self.volume[0 : self.nrho - 1]
                        * self.core_profiles.profiles_1d[self.time_index_core_profiles]
                        .ion[ispecies]
                        .density[0 : self.nrho - 1]
                    )
                    ntot = ntot + species_density[ispecies]
                    if species_density[ispecies] > max_density:
                        max_density = species_density[ispecies]
                        imax = ispecies

                ne = sum(
                    self.volume[0 : self.nrho - 1]
                    * self.core_profiles.profiles_1d[self.time_index_core_profiles].electrons.density[0 : self.nrho - 1]
                )

                nspec_over_ntot = species_density / ntot
                nspec_over_ne = species_density / ne
                if imax != -99:
                    nspec_over_nmaj = species_density / species_density[imax]
                else:
                    nspec_over_nmaj = 0

            # When a species appears twice: combine
            if self.species:
                for ispecies in range(self.nspecies_core):
                    for jspecies in range(self.nspecies_core):
                        if (self.species[jspecies] == self.species[ispecies]) & (jspecies != ispecies):
                            nspec_over_ntot[ispecies] = nspec_over_ntot[ispecies] + nspec_over_ntot[jspecies]
                            nspec_over_ntot[jspecies] = 0
                            nspec_over_ne[ispecies] = nspec_over_ne[ispecies] + nspec_over_ne[jspecies]
                            nspec_over_ne[jspecies] = 0
                            nspec_over_nmaj[ispecies] = nspec_over_nmaj[ispecies] + nspec_over_nmaj[jspecies]
                            nspec_over_nmaj[jspecies] = 0

                # Nice display of plasma composition with species concentrations
                disp_species = "   species:      "
                disp_a = "   a:            "
                disp_z = "   z:            "
                disp_nspec_over_ntot = "   n_over_ntot:  "
                disp_nspec_over_ne = "   n_over_ne:    "
                disp_nspec_over_nmaj = "   n_over_n_maj: "
                for ispecies in range(self.nspecies_core):
                    if nspec_over_ne[ispecies] > 0.0:
                        tabsize = 8
                        disp_species = (
                            disp_species + self.species[ispecies] + " " * (tabsize - len(self.species[ispecies]))
                        )
                        disp_a = (
                            disp_a
                            + format("%.1f" % self.a[ispecies])
                            + " " * (tabsize - len(format("%.1f" % self.a[ispecies])))
                        )
                        disp_z = (
                            disp_z
                            + format("%.1f" % self.z[ispecies])
                            + " " * (tabsize - len(format("%.1f" % self.z[ispecies])))
                        )
                        disp_nspec_over_ntot = (
                            disp_nspec_over_ntot
                            + format("%.3f" % nspec_over_ntot[ispecies])
                            + " " * (tabsize - len(format("%.3f" % nspec_over_ntot[ispecies])))
                        )
                        disp_nspec_over_ne = (
                            disp_nspec_over_ne
                            + format("%.3f" % nspec_over_ne[ispecies])
                            + " " * (tabsize - len(format("%.3f" % nspec_over_ne[ispecies])))
                        )
                        disp_nspec_over_nmaj = (
                            disp_nspec_over_nmaj
                            + format("%.3f" % nspec_over_nmaj[ispecies])
                            + " " * (tabsize - len(format("%.3f" % nspec_over_nmaj[ispecies])))
                        )

                if self.is_core_profiles_present == 1:
                    print(
                        "   ------------",
                    )
                    print(disp_species)
                    print(disp_a)
                    print(disp_z)
                    print(disp_nspec_over_ntot)
                    print(disp_nspec_over_ne)
                    print(disp_nspec_over_nmaj)
                    print("   ------------")

        else:
            nspec_over_ne = [0] * self.nspecies_core
        return nspec_over_ne

    def get_profiles(self):
        """
        The function `get_profiles` retrieves and organizes various plasma profiles and species
        densities based on certain criteria.

        Returns:
            The function `get_profiles` returns a dictionary `profiles` containing various profiles
            related to core and edge plasma parameters. The dictionary includes keys such as "rhonorm",
            "te", "ti", "ne", "zeff" for core profiles, and "rhonorm_e", "te_e", "ti_e", "ne_e", "zeff_e"
            for edge profiles.
        """
        # Criteria for significant impurity (in X[imp]/ne concentration)

        profiles = {}
        if self.is_core_profiles_present:
            profiles["rhonorm"] = [0] * self.nrho
            profiles["te"] = [0] * self.nrho
            if self.ti_flag != 0:
                profiles["ti"] = [0] * self.nrho
            profiles["ne"] = [0] * self.nrho
            profiles["zeff"] = [0] * self.nrho
            for i in range(self.nrho):
                profiles["rhonorm"][i] = self.rho_tor_norm[i]
                profiles["te"][i] = self.electron_temperature[i]
                if self.ti_flag != 0:
                    profiles["ti"][i] = self.ion_temperature[i]
                profiles["ne"][i] = self.electron_density[i]
                profiles["zeff"][i] = self.zeff[i]
        if self.is_edge_profiles_present:
            profiles["rhonorm_e"] = [0] * self.erho
            profiles["te_e"] = [0] * self.erho
            if self.ti_e_flag != 0:
                profiles["ti_e"] = [0] * self.erho
            profiles["ne_e"] = [0] * self.erho
            profiles["zeff_e"] = [0] * self.erho
            for i in range(self.erho):
                profiles["rhonorm_e"][i] = self.rho_tor_norm[self.nrho + i]
                profiles["te_e"][i] = self.electron_temperature[self.nrho + i]
                if self.ti_e_flag != 0:
                    profiles["ti_e"][i] = self.ion_temperature[self.nrho + i]
                profiles["ne_e"][i] = self.electron_density[self.nrho + i]
                profiles["zeff_e"][i] = self.zeff[self.nrho + i]

        profiles["n_species"] = {}
        if self.species:
            for ispecies in range(self.nspecies_core):
                profiles["n_species"][self.species[ispecies]] = {}
            if self.is_core_profiles_present:
                profiles["ni"] = [0] * self.nrho
                for ispecies in range(self.nspecies_core):
                    if self.is_composition_available is True:
                        if self.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT:
                            profiles["n_species"][self.species[ispecies]]["density"] = [0] * self.nrho
                            if self.vpol_flag != 0:
                                profiles["n_species"][self.species[ispecies]]["vpol"] = [0] * self.nrho
                            if self.vphi_flag != 0:
                                profiles["n_species"][self.species[ispecies]]["vphi"] = [0] * self.nrho
                            for i in range(self.nrho):
                                profiles["n_species"][self.species[ispecies]]["density"][i] = self.ion_density[
                                    ispecies
                                ][i]
                                if self.vpol_flag != 0:
                                    profiles["n_species"][self.species[ispecies]]["vpol"][i] = self.ion_vpol[ispecies][
                                        i
                                    ]
                                if self.vphi_flag != 0:
                                    profiles["n_species"][self.species[ispecies]]["vphi"][i] = self.ion_vphi[ispecies][
                                        i
                                    ]
                for i in range(self.nrho):
                    profiles["ni"][i] = profiles["ni"][i] + self.ion_density[ispecies][i]
            if self.is_edge_profiles_present:
                profiles["ni_e"] = [0] * self.erho
                for ispecies in range(self.nspecies_core):
                    if self.species_map[ispecies] != -99:
                        profiles["n_species"][self.species[ispecies]]["density_e"] = [0] * self.erho
                        if self.vpol_e_flag != 0:
                            profiles["n_species"][self.species[ispecies]]["vpol_e"] = [0] * self.erho
                        if self.vphi_e_flag != 0:
                            profiles["n_species"][self.species[ispecies]]["vphi_e"] = [0] * self.erho
                        for i in range(self.erho):
                            profiles["n_species"][self.species[ispecies]]["density_e"][i] = self.ion_density[ispecies][
                                self.nrho + i
                            ]
                            if self.vpol_e_flag != 0:
                                profiles["n_species"][self.species[ispecies]]["vpol_e"][i] = self.ion_vpol[ispecies][
                                    self.nrho + i
                                ]
                            if self.vphi_e_flag != 0:
                                profiles["n_species"][self.species[ispecies]]["vphi_e"][i] = self.ion_vphi[ispecies][
                                    self.nrho + i
                                ]
                    if self.species_map[ispecies] != -99:
                        for i in range(self.erho):
                            profiles["ni_e"][i] = profiles["ni_e"][i] + self.ion_density[ispecies][self.nrho + i]
        return profiles

    def get_min_max_velocity_profiles(self):
        """
        This function calculates the minimum and maximum velocity profiles for different species in a
        plasma system.

        Returns:
            The `get_min_max_velocity_profiles` method returns a dictionary containing the maximum and
            minimum velocity profiles for `vphi` and `vpol`. The keys in the dictionary are "max_vphi",
            "min_vphi", "max_vpol", and "min_vpol", each corresponding to the maximum and minimum values for
            the `vphi` and `vpol` profiles, respectively.
        """
        # vphi_flag = vphi_profile["vphi_flag"]
        # vphi_e_flag = vphi_profile["vphi_e_flag"]
        # ion_vphi = vphi_profile["ion_vphi"]

        # vpol_flag = vpol_profile["vpol_flag"]
        # vpol_e_flag = vpol_profile["vpol_e_flag"]
        # ion_vpol = vpol_profile["ion_vpol"]
        # Min and max of velocity profiles
        max_vphi = -9e99
        min_vphi = 9e99
        max_vpol = -9e99
        min_vpol = 9e99
        if self.species:
            for ispecies in range(self.nspecies_core):
                if self.is_composition_available and (
                    self.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT
                    or not self.is_core_profiles_present
                ):
                    if self.vphi_flag != 0:
                        if "vphi" in self.profiles["n_species"][self.species[ispecies]].keys():
                            if max_vphi < max(
                                self.profiles["n_species"][self.species[ispecies]]["vphi"][0 : self.nrho - 1]
                            ):
                                max_vphi = max(
                                    self.profiles["n_species"][self.species[ispecies]]["vphi"][0 : self.nrho - 1]
                                )
                            if min_vphi > min(
                                self.profiles["n_species"][self.species[ispecies]]["vphi"][0 : self.nrho - 1]
                            ):
                                min_vphi = min(
                                    self.profiles["n_species"][self.species[ispecies]]["vphi"][0 : self.nrho - 1]
                                )
                    if self.is_edge_profiles_present and self.species_map[ispecies] != -99 and self.vphi_e_flag != 0:
                        if "vphi_e" in self.profiles["n_species"][self.species[ispecies]].keys():
                            if max_vphi < max(
                                self.profiles["n_species"][self.species[ispecies]]["vphi_e"][0 : self.erho - 1]
                            ):
                                max_vphi = max(
                                    self.profiles["n_species"][self.pecies[ispecies]]["vphi_e"][0 : self.erho - 1]
                                )
                            if min_vphi > min(
                                self.profiles["n_species"][self.species[ispecies]]["vphi_e"][0 : self.erho - 1]
                            ):
                                min_vphi = min(
                                    self.profiles["n_species"][self.species[ispecies]]["vphi_e"][0 : self.erho - 1]
                                )
                    if self.vpol_flag != 0:
                        if "vpol" in self.profiles["n_species"][self.species[ispecies]].keys():
                            if max_vpol < max(
                                self.profiles["n_species"][self.species[ispecies]]["vpol"][0 : self.nrho - 1]
                            ):
                                max_vpol = max(
                                    self.profiles["n_species"][self.species[ispecies]]["vpol"][0 : self.nrho - 1]
                                )
                            if min_vpol > min(
                                self.profiles["n_species"][self.species[ispecies]]["vpol"][0 : self.nrho - 1]
                            ):
                                min_vpol = min(
                                    self.profiles["n_species"][self.species[ispecies]]["vpol"][0 : self.nrho - 1]
                                )
                    if self.is_edge_profiles_present and self.species_map[ispecies] != -99 and self.vpol_e_flag != 0:
                        if "vpol_e" in self.profiles["n_species"][self.species[ispecies]].keys():
                            if max_vpol < max(
                                self.profiles["n_species"][self.species[ispecies]]["vpol_e"][0 : self.erho - 1]
                            ):
                                max_vpol = max(
                                    self.profiles["n_species"][self.pecies[ispecies]]["vpol_e"][0 : self.erho - 1]
                                )
                            if min_vpol > min(
                                self.profiles["n_species"][self.species[ispecies]]["vpol_e"][0 : self.erho - 1]
                            ):
                                min_vpol = min(
                                    self.profiles["n_species"][self.species[ispecies]]["vpol_e"][0 : self.erho - 1]
                                )

            if self.vphi_flag != 0 or self.vphi_e_flag != 0:
                logger.debug(f"max_vphi : {max_vphi}")
                logger.debug(f"min_vphi : {min_vphi}")
            if self.vpol_flag != 0 or self.vpol_e_flag != 0:
                logger.debug(f"max_vpol : {max_vpol}")
                logger.debug(f"min_vpol : {min_vpol}")

        return {
            "max_vphi": max_vphi,
            "min_vphi": min_vphi,
            "max_vpol": max_vpol,
            "min_vpol": min_vpol,
        }

    def create_wave_form(self, ndim):
        """
        The function `create_wave_form` returns a dictionary with three keys, each containing a list of
        zeros with a length specified by the `ndim` parameter.

        Args:
            ndim: The `ndim` parameter in the `create_wave_form` function represents the number of
                dimensions for which you want to create the wave form. This parameter is used to determine the
                length of the lists in the dictionary that is returned by the function.

        Returns:
            A dictionary is being returned with three keys: "central", "edge", and "rho95", each
            containing a list of zeros with a length specified by the input parameter ndim.
        """
        return {"central": [0] * ndim, "edge": [0] * ndim, "rho95": [0] * ndim}

    def get_waveform(self):
        """
        The function `get_waveform` retrieves various plasma waveforms from a data source and organizes
        them into a dictionary structure.

        Returns:
            The function `get_waveform` returns a dictionary containing various waveforms related to
            plasma parameters such as electron temperature, ion temperature, electron density, impurity
            density, impurity velocity components (poloidal and toroidal), and effective charge. The
            dictionary also includes information about the time array and the total ion density.
        """
        vphi_flag = self.vphi_flag

        vpol_flag = self.vpol_flag
        # Create the dictionary defining the list of waveforms (central values) that can be displayed
        if self.is_core_profiles_present:
            waveform = {}
            waveform["time"] = self.common_time_array
            for ikey in ["te", "ti", "ne", "zeff"]:
                waveform[ikey] = self.create_wave_form(0)
            electrons_temperature = np.array([])
            for i, _ in enumerate(self.time_array_core_profiles):
                electrons_temperature = np.append(
                    electrons_temperature, self.core_profiles.profiles_1d[i].electrons.temperature[0]
                )

            waveform["te"]["central"] = electrons_temperature * 1e-3
            # self.connection.partial_get("core_profiles", "profiles_1d(:)/electrons/temperature(0)") * 1e-3

            if self.ti_flag == 1:
                t_i_average = np.array([])
                for i, _ in enumerate(self.time_array_core_profiles):
                    t_i_average = np.append(t_i_average, self.core_profiles.profiles_1d[i].t_i_average[0])
                waveform["ti"]["central"] = t_i_average * 1e-3
                # (
                #     self.connection.partial_get("core_profiles", "profiles_1d(:)/t_i_average(0)") * 1e-3
                # )
            else:
                try:
                    ion_temperature = np.array([])
                    for i, _ in enumerate(self.time_array_core_profiles):
                        ion_temperature = np.append(
                            ion_temperature, self.core_profiles.profiles_1d[i].ion[0].temperature[0]
                        )

                    waveform["ti"]["central"] = ion_temperature * 1e-3
                    # (
                    #     self.connection.partial_get("core_profiles", "profiles_1d(:)/ion(0)/temperature(0)") * 1e-3
                    # )
                except Exception as e:
                    logger.debug(f"{e}")
                    waveform["ti"]["central"] = [np.NaN] * len(self.time_array_core_profiles)

            electrons_density = np.array([])
            for i, _ in enumerate(self.time_array_core_profiles):
                electrons_density = np.append(electrons_density, self.core_profiles.profiles_1d[i].electrons.density[0])

            waveform["ne"]["central"] = electrons_density
            # self.connection.partial_get(
            #     "core_profiles", "profiles_1d(:)/electrons/density(0)"
            # )
            zeff = np.array([])
            for i, _ in enumerate(self.time_array_core_profiles):
                zeff = np.append(zeff, self.core_profiles.profiles_1d[i].zeff[0])

            waveform["zeff"]["central"] = zeff
            # self.connection.partial_get("core_profiles", "profiles_1d(:)/zeff(0)")

            waveform["n_species"] = {}
            waveform["ni"] = self.create_wave_form(len(self.time_array_core_profiles))
            if self.species:
                for ispecies in range(self.nspecies_core):
                    if self.is_composition_available and (
                        self.nspec_over_ne[ispecies] > KineticProfilesCompute.IMPURITY_LIMIT
                    ):
                        waveform["n_species"][self.species[ispecies]] = {
                            "density": self.create_wave_form(0),
                            "vpol": self.create_wave_form(0),
                            "vphi": self.create_wave_form(0),
                        }

                        try:
                            ion_density = np.array([])
                            for i, _ in enumerate(self.time_array_core_profiles):
                                ion_density = np.append(
                                    ion_density, self.core_profiles.profiles_1d[i].ion[ispecies].density[0]
                                )

                            waveform["n_species"][self.species[ispecies]]["density"]["central"] = ion_density
                            # (
                            #     self.connection.partial_get(
                            #         "core_profiles",
                            #         f"profiles_1d(:)/ion({ispecies})/density(0)",
                            #     )
                            # )
                            if vpol_flag == 1:
                                velocity_poloidal = np.array([])
                                for i, _ in enumerate(self.time_array_core_profiles):
                                    velocity_poloidal = np.append(
                                        velocity_poloidal,
                                        self.core_profiles.profiles_1d[i].ion[ispecies].velocity.poloidal[0],
                                    )
                                waveform["n_species"][self.species[ispecies]]["vpol"]["central"] = velocity_poloidal
                                # (
                                #     self.connection.partial_get(
                                #         "core_profiles",
                                #         f"profiles_1d(:)/ion({ispecies})/velocity/poloidal(0)",
                                #     )
                                # )
                            elif vpol_flag == 2:
                                velocity_pol = np.array([])
                                for i, _ in enumerate(self.time_array_core_profiles):
                                    velocity_pol = np.append(
                                        velocity_pol, self.core_profiles.profiles_1d[i].ion[ispecies].velocity_pol[0]
                                    )
                                waveform["n_species"][self.species[ispecies]]["vpol"]["central"] = velocity_pol
                                # (
                                #     self.connection.partial_get(
                                #         "core_profiles",
                                #         f"profiles_1d(:)/ion({ispecies})/velocity_pol(0)",
                                #     )
                                # )
                            if vphi_flag == 1:
                                velocity_toroidal = np.array([])
                                for i, _ in enumerate(self.time_array_core_profiles):
                                    velocity_toroidal = np.append(
                                        velocity_toroidal,
                                        self.core_profiles.profiles_1d[i].ion[ispecies].velocity.toroidal[0],
                                    )
                                waveform["n_species"][self.species[ispecies]]["vphi"]["central"] = velocity_toroidal
                                # (
                                #     self.connection.partial_get(
                                #         "core_profiles",
                                #         f"profiles_1d(:)/ion({ispecies})/velocity/toroidal(0)",
                                #     )
                                # )
                            elif vphi_flag == 2:
                                velocity_tor = np.array([])
                                for i, _ in enumerate(self.time_array_core_profiles):
                                    velocity_tor = np.append(
                                        velocity_tor, self.core_profiles.profiles_1d[i].ion[ispecies].velocity_tor[0]
                                    )
                                waveform["n_species"][self.species[ispecies]]["vphi"]["central"] = velocity_tor
                                # (
                                #     self.connection.partial_get(
                                #         "core_profiles",
                                #         f"profiles_1d(:)/ion({ispecies})/velocity_tor(0)",
                                #     )
                                # )
                        except Exception as e:
                            logger.debug(f"{e}")
                            waveform["n_species"][self.species[ispecies]]["density"]["central"] = [
                                np.NaN
                            ] * self.common_time_length
                            waveform["n_species"][self.species[ispecies]]["vpol"]["central"] = [
                                np.NaN
                            ] * self.common_time_length
                            waveform["n_species"][self.species[ispecies]]["vphi"]["central"] = [
                                np.NaN
                            ] * self.common_time_length

                        for itime in range(self.common_time_length):
                            waveform["ni"]["central"][itime] = (
                                waveform["ni"]["central"][itime]
                                + waveform["n_species"][self.species[ispecies]]["density"]["central"][itime]
                            )
            return waveform
        return None
