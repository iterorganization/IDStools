"""
This module provides compute functions and classes for core_sources ids data

`refer data dictionary <https://imas-data-dictionary.readthedocs.io/en/latest/>`_.

"""

import functools
import logging
from typing import Dict, Union

import numpy as np

from idstools.compute.common import get_compat_attr

logger = logging.getLogger("module")


class CoreSourcesCompute:
    """This class provides compute functions for core sources ids.

    Attributes:
        ids (object): The core sources IDS (Integrated Data Structure) object containing
            source/sink data for particles and energy in the core plasma including heating,
            current drive, and particle injection sources.
    """

    def __init__(self, ids):
        self.ids = ids

    def get_flux_info_from_sources(self, time_slice):
        """
        The function retrieves information about sources, including their name,
        particle flux, energy flux, and ion properties, and returns a dictionary containing this information.

        Returns:
            The function returns a dictionary containing
            information about the sources. The dictionary has the following
            structure:

            .. code-block:: python

                {
                    0: {
                        "energy_flux": 22081836.173650958,
                        "ions": {
                            0: {
                                "a": 2.0,
                                "energy_flux": None,
                                "particles_flux": 4.947616643196025e21,
                                "z_ion": -9e40,
                                "z_n": 1.0,
                            },
                            "name": "total",
                            "particles_flux": None,
                        },
                    }
                }
        """
        sources_dict = {}
        for source_index, source in enumerate(self.ids.source):
            source_dict = {
                "name": source.identifier.name,
                "particles_flux": None,
                "energy_flux": None,
                "ions": {},
            }
            if len(source.profiles_1d) != 0:
                if len(source.profiles_1d[time_slice].electrons.particles) != 0:
                    grid_volume = (
                        np.asarray([np.nan] * len(source.profiles_1d[time_slice].electrons.particles))
                        if len(source.profiles_1d[time_slice].grid.volume) == 0
                        else source.profiles_1d[time_slice].grid.volume
                    )
                    source_dict["particles_flux"] = np.trapz(
                        source.profiles_1d[time_slice].electrons.particles,
                        grid_volume,
                    )
                if len(source.profiles_1d[time_slice].electrons.energy) != 0:
                    grid_volume = (
                        np.asarray([np.nan] * len(source.profiles_1d[time_slice].electrons.energy))
                        if len(source.profiles_1d[time_slice].grid.volume) == 0
                        else source.profiles_1d[time_slice].grid.volume
                    )
                    source_dict["energy_flux"] = np.trapz(
                        source.profiles_1d[time_slice].electrons.energy,
                        grid_volume,
                    )
                ions_dict = {}
                for ion_index, ion in enumerate(source.profiles_1d[time_slice].ion):
                    if len(ion.element) > 0:
                        ion_dict = {
                            "a": ion.element[0].a,
                            "z_n": ion.element[0].z_n,
                            "z_ion": ion.z_ion,
                        }
                    else:
                        ion_dict = {"a": "--", "z_n": "--", "z_ion": "--"}
                    if len(ion.particles) != 0:
                        ion_dict["particles_flux"] = np.trapz(ion.particles, source.profiles_1d[time_slice].grid.volume)
                    else:
                        ion_dict["particles_flux"] = None
                    if len(ion.energy) != 0:
                        ion_dict["energy_flux"] = np.trapz(ion.energy, source.profiles_1d[time_slice].grid.volume)
                    else:
                        ion_dict["energy_flux"] = None
                    ions_dict[ion_index] = ion_dict
                source_dict["ions"] = ions_dict
            sources_dict[source_index] = source_dict
        return sources_dict

    @functools.lru_cache(maxsize=128)
    def get_rho_tor_norm(self, time_slice) -> Union[np.ndarray, None]:
        """
        The function `get_rho_tor_norm` returns the value of `grid.rho_tor_norm` if it is not empty,
        otherwise it returns None.

        Returns:
            the value of the variable `rho_tor_norm`.
        """
        if len(self.ids.source) == 0:
            return None
        rho_tor_norm = None
        try:
            if len(self.ids.source[0].profiles_1d[time_slice].grid.rho_tor_norm) > 0:
                rho_tor_norm = self.ids.source[0].profiles_1d[time_slice].grid.rho_tor_norm
            elif len(self.ids.source[0].profiles_1d[time_slice].grid.rho_tor) > 0:
                nrho = len(self.ids.source[0].profiles_1d[time_slice].grid.rho_tor)
                rho_tor_norm = (
                    self.ids.source[0].profiles_1d[time_slice].grid.rho_tor
                    / self.ids.source[0].profiles_1d[time_slice].grid.rho_tor[nrho - 1]
                )
        except Exception as e:
            logger.critical(
                f"core_sources.source[isource].profiles_1d[{time_slice}].grid.rho_tor_norm and"
                "rho_tor could not be read"
            )
            logger.debug(f"{e}")
            return None
        if rho_tor_norm is not None and len(rho_tor_norm) == 0:
            logger.critical(
                f"core_sources.source[isource].profiles_1d[{time_slice}].grid.rho_tor_norm and rho_tor are empty"
            )
            return None
        return rho_tor_norm

    @functools.lru_cache(maxsize=128)
    def get_valid_and_active_sources(self, time_slice) -> Dict[int, Dict[str, bool]]:
        """
        The function `get_valid_and_active_sources` returns a dictionary of valid and active sources, where each source
        is represented by a dictionary with the keys "valid" and "active".

        Returns:
            a dictionary of dictionaries. The outer dictionary has integer keys representing the index of each source,
            and the inner dictionaries have string keys ("valid" and "active") representing the validity and
            activity status of each source.
        """
        sources = {}
        for source_index, source_info in enumerate(self.ids.source):
            source = {}
            if len(source_info.global_quantities) > 0:
                source["valid"] = True
                source["active"] = True if source_info.global_quantities[time_slice].power.has_value else False
                # https://jira.iter.org/browse/IMAS-5686
                # (
                #     True
                #     if source_info.global_quantities[time_slice].power.has_value
                #     and abs(source_info.global_quantities[time_slice].power) > 0
                #     else False
                # )
            else:
                source["valid"] = False
                source["active"] = False
                logger.critical(f"core_sources.source[{source_index}] has no global_quantities, will be discarded.")
            sources[source_index] = source
        return sources

    @functools.lru_cache(maxsize=128)
    def is_active_source_available(self, time_slice) -> bool:
        """
        The function checks if there is an active source available among the valid and active sources.

        Returns:
            a boolean value. It is checking if there are any active sources in the list of valid and active sources
            and returning True if there is at least one active source, and False otherwise.
        """
        sources = self.get_valid_and_active_sources(time_slice)
        return any(source["active"] for _, source in sources.items())

    def get_source_names(self, time_slice) -> Dict:
        """
        This function retrieves the names of valid and active sources and returns them in uppercase.

        Returns:
            A dictionary containing the index of valid and active sources as keys and the uppercase name
        of the source as values.
        """
        sources = self.get_valid_and_active_sources(time_slice)
        single_source_name = {}
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_source_name[source_index] = self.ids.source[source_index].identifier.name.upper()
        return single_source_name

    @functools.lru_cache(maxsize=128)
    def get_single_and_total_electrons_and_ions_profiles(self, time_slice) -> Dict[str, np.ndarray]:
        """
        The function returns the total current profile and the individual
        current profiles for each valid and active source.
        SINGLE AND TOTAL PROFILES (ELECTRONS+IONS)

        Returns:
            a dictionary with two keys: "total_current_profile" and "single_current_profile". The value associated
            with the "total_current_profile" key is a numpy array representing the total current profile.
            The value associated with the "single_current_profile" key is a dictionary where the keys
            are the indices of the sources and the
            values are numpy arrays representing the current profiles for each individual source.
        """
        # SINGLE AND TOTAL PROFILES (ELECTRONS+IONS)
        # total_power_profile                = [0]*nrho  # profile
        # total_particles_profile            = [0]*nrho  # profile
        # single_power_profile               = dict()    # profile
        # single_particles_profile           = dict()    # profile
        rho_tor_norm = self.get_rho_tor_norm(time_slice)
        nrho = 0
        if rho_tor_norm is not None:
            nrho = len(rho_tor_norm)
        total_current_profile = np.zeros(nrho)
        single_current_profile = {}
        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():  # range(nsources):
            if source["valid"] and source["active"]:
                if len(self.ids.source[source_index].profiles_1d[time_slice].j_parallel) > 0:
                    total_current_profile = (
                        total_current_profile + self.ids.source[source_index].profiles_1d[time_slice].j_parallel
                    )
                    single_current_profile[source_index] = (
                        self.ids.source[source_index].profiles_1d[time_slice].j_parallel
                    )
                else:
                    single_current_profile[source_index] = np.zeros(nrho)
        return {
            "total_current_profile": total_current_profile,
            "single_current_profile": single_current_profile,
        }

    @functools.lru_cache(maxsize=128)
    def get_single_and_total_electrons_profiles(self, time_slice) -> Dict[str, np.ndarray]:
        """
        The function calculates and returns profiles of total and single electron power and particles
        based on valid and active sources.

        Returns:
            a dictionary with the following keys and corresponding values:
            "total_electron_power_profile": Profile of total electron power
            "total_electron_particles_profile": Profile of total electron particles
            "single_electron_power_profile": Dictionary with profiles of single electron power for each source
            "single_electron_particles_profile": Dictionary containing profiles of single electron
            particles for each data source

        """
        rho_tor_norm = self.get_rho_tor_norm(time_slice)
        nrho = 0
        if rho_tor_norm is not None:
            nrho = len(rho_tor_norm)
        total_electron_power_profile = np.zeros(nrho)
        total_electron_particles_profile = np.zeros(nrho)
        single_electron_power_profile = {}
        single_electron_particles_profile = {}

        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                electrons_energy = self.ids.source[source_index].profiles_1d[time_slice].electrons.energy
                if len(electrons_energy) < 1:
                    electrons_energy = np.zeros(nrho)
                electrons_particles = self.ids.source[source_index].profiles_1d[time_slice].electrons.particles
                if len(electrons_particles) < 1:
                    electrons_particles = np.zeros(nrho)

                total_electron_power_profile = total_electron_power_profile + electrons_energy
                total_electron_particles_profile = total_electron_particles_profile + electrons_particles

                single_electron_power_profile[source_index] = electrons_energy
                single_electron_particles_profile[source_index] = electrons_particles

        return {
            "total_electron_power_profile": total_electron_power_profile,
            "total_electron_particles_profile": total_electron_particles_profile,
            "single_electron_power_profile": single_electron_power_profile,
            "single_electron_particles_profile": single_electron_particles_profile,
        }

    def get_single_and_total_ion_profiles(self, time_slice) -> Dict[str, np.ndarray]:
        """
        The function calculates the total and individual power and particle profiles
        for ions in a plasma simulation.

        Returns:
            a dictionary with the following keys and values:total_ion_power_profile, total_ion_particles_profile,
            single_ion_power_profile, single_ion_particles_profile
        """
        # SINGLE AND TOTAL PROFILES (IONS)
        # total_ion_power_profile = [0] * nrho  # profile
        # total_ion_particles_profile = [0] * nrho  # profile
        # single_ion_power_profile = dict()  # profile
        # single_ion_particles_profile = dict()  # profile
        rho_tor_norm = self.get_rho_tor_norm(time_slice)
        nrho = 0
        if rho_tor_norm is not None:
            nrho = len(rho_tor_norm)
        total_ion_power_profile = np.zeros(nrho)
        total_ion_particles_profile = np.zeros(nrho)
        single_ion_power_profile = {}
        single_ion_particles_profile = {}

        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_ion_power_profile[source_index] = np.zeros(nrho)
                single_ion_particles_profile[source_index] = np.zeros(nrho)
                single_ions_filled = False
                for ion in self.ids.source[source_index].profiles_1d[time_slice].ion:
                    if len(ion.energy) > 1:
                        single_ions_filled = True
                        if len(ion.energy) < 1:
                            ion.energy = [0] * nrho
                        if len(ion.particles) < 1:
                            ion.particles = [0] * nrho

                        single_ion_power_profile[source_index] = single_ion_power_profile[source_index] + ion.energy
                        single_ion_particles_profile[source_index] = (
                            single_ion_particles_profile[source_index] + ion.particles
                        )

                        total_ion_power_profile = total_ion_power_profile + ion.energy
                        total_ion_particles_profile = total_ion_particles_profile + ion.particles
                if single_ions_filled is False:
                    if self.ids.source[source_index].profiles_1d[0].total_ion_energy.has_value:
                        total_ion_power_profile = (
                            total_ion_power_profile + self.ids.source[source_index].profiles_1d[0].total_ion_energy
                        )
        return {
            "total_ion_power_profile": total_ion_power_profile,
            "total_ion_particles_profile": total_ion_particles_profile,
            "single_ion_power_profile": single_ion_power_profile,
            "single_ion_particles_profile": single_ion_particles_profile,
        }

    def get_single_and_total_electrons_ions_waveforms(self, time_slice):
        """
        This function calculates single and total waveforms for electrons and ions based on power and
        particle quantities.

        Returns:
            The function `get_single_and_total_electrons_ions_waveforms` returns a dictionary containing
            four key-value pairs:
            1. "total_power_waveform": an array representing the total power waveform
            2. "total_particles_waveform": an array representing the total particles waveform
            3. "single_power_waveform": a dictionary where each key is a source index and the corresponding
            value is an array
            4. "single_particles_waveform": particles waveform
        """
        # SINGLE AND TOTAL WAVEFORMS (ELECTRONS+IONS)
        # total_power_waveform = [0] * ntime  # waveform
        # total_particles_waveform = [0] * ntime  # waveform
        # single_power_waveform = dict()  # waveform
        # single_particles_waveform = dict()  # waveform
        time_length = len(self.ids.time)
        total_ion_power_waveform = np.zeros(time_length)
        total_ion_particles_waveform = np.zeros(time_length)
        single_power_waveform = {}
        single_particles_waveform = {}
        dict_single_and_total_electrons_waveforms = self.get_single_and_total_electrons_waveforms(time_slice)
        total_electron_power_waveform = dict_single_and_total_electrons_waveforms["total_electron_power_waveform"]
        total_electron_particles_waveform = dict_single_and_total_electrons_waveforms[
            "total_electron_particles_waveform"
        ]
        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_power_waveform[source_index] = []
                single_particles_waveform[source_index] = []
                for time_index in range(time_length):
                    electrons_power = self.ids.source[source_index].global_quantities[time_index].electrons.power
                    electrons_particles = (
                        self.ids.source[source_index].global_quantities[time_index].electrons.particles
                    )
                    total_ion_particles = (
                        self.ids.source[source_index].global_quantities[time_index].total_ion_particles
                    )
                    total_ion_power = self.ids.source[source_index].global_quantities[time_index].total_ion_power

                    if electrons_power < 0:
                        electrons_power = 0.0
                    if electrons_particles < 0:
                        electrons_particles = 0.0
                    if total_ion_particles < 0:
                        total_ion_particles = 0.0
                    if total_ion_power < 0:
                        total_ion_power = 0.0

                    total_ion_power_waveform[time_index] += total_ion_power
                    total_ion_particles_waveform[time_index] += total_ion_particles
                    single_power_waveform[source_index].append(electrons_power + total_ion_power)
                    single_particles_waveform[source_index].append(electrons_particles + total_ion_particles)
                single_power_waveform[source_index] = np.array(single_power_waveform[source_index])
                single_particles_waveform[source_index] = np.array(single_particles_waveform[source_index])
        total_power_waveform = total_electron_power_waveform + total_ion_power_waveform
        total_particles_waveform = total_electron_particles_waveform + total_ion_particles_waveform
        return {
            "total_power_waveform": total_power_waveform,
            "total_particles_waveform": total_particles_waveform,
            "single_power_waveform": single_power_waveform,
            "single_particles_waveform": single_particles_waveform,
        }

    def get_single_and_total_electrons_waveforms(self, time_slice):
        """
        The function calculates and returns waveforms for total electron
        power, total electron particles, single electron power, and single electron particles.

        Returns:
            a dictionary with the following keys and values:
            "total_electron_power_waveform": total_electron_power_waveform,
            "total_electron_particles_waveform": total_electron_particles_waveform,
            "single_electron_power_waveform": single_electron_power_waveform,
            "single_electron_particles_waveform": single_electron_particles_waveform,
        """
        # SINGLE AND TOTAL WAVEFORMS (ELECTRONS)
        # total_electron_power_waveform = [0] * ntime  # waveform
        # total_electron_particles_waveform = [0] * ntime  # waveform
        # single_electron_power_waveform = dict()  # waveform
        # single_electron_particles_waveform = dict()  # waveform
        time_length = len(self.ids.time)
        total_electron_power_waveform = np.zeros(time_length)
        total_electron_particles_waveform = np.zeros(time_length)
        single_electron_power_waveform = {}
        single_electron_particles_waveform = {}
        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_electron_power_waveform[source_index] = []
                single_electron_particles_waveform[source_index] = []
                for time_index in range(time_length):
                    electrons_power = self.ids.source[source_index].global_quantities[time_index].electrons.power
                    if electrons_power < 0:
                        electrons_power = 0.0
                    electrons_particles = (
                        self.ids.source[source_index].global_quantities[time_index].electrons.particles
                    )
                    if electrons_particles < 0:
                        electrons_particles = 0.0

                    total_electron_power_waveform[time_index] = (
                        total_electron_power_waveform[time_index] + electrons_power
                    )
                    total_electron_particles_waveform[time_index] = (
                        total_electron_particles_waveform[time_index] + electrons_particles
                    )
                    single_electron_power_waveform[source_index].append(electrons_power)
                    single_electron_particles_waveform[source_index].append(electrons_particles)
                single_electron_power_waveform[source_index] = np.array(single_electron_power_waveform[source_index])
                single_electron_particles_waveform[source_index] = np.array(
                    single_electron_particles_waveform[source_index]
                )

        return {
            "total_electron_power_waveform": total_electron_power_waveform,
            "total_electron_particles_waveform": total_electron_particles_waveform,
            "single_electron_power_waveform": single_electron_power_waveform,
            "single_electron_particles_waveform": single_electron_particles_waveform,
        }

    def get_single_and_total_ions_waveforms(self, time_slice):
        """
        The function calculates and returns the waveforms for single ion power,
        single ion particles, total ion power, and total ion particles.

        Returns:
            a dictionary with four key-value pairs. The keys are
            "single_ion_power_waveform", "single_ion_particles_waveform",
            "total_ion_power_waveform", and "total_ion_particles_waveform". The corresponding values are the
            waveforms for single ion power, single ion particles, total ion power, and total ion particles,
            respectively.
        """
        # SINGLE AND TOTAL WAVEFORMS (IONS)
        # total_ion_power_waveform = [0] * ntime  # waveform
        # total_ion_particles_waveform = [0] * ntime  # waveform
        # single_ion_power_waveform = dict()  # waveform
        # single_ion_particles_waveform = dict()  # waveform
        time_length = len(self.ids.time)
        total_ion_power_waveform = np.zeros(time_length)  # waveform
        total_ion_particles_waveform = np.zeros(time_length)  # waveform
        single_ion_power_waveform = {}  # waveform
        single_ion_particles_waveform = {}  # waveform
        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_ion_power_waveform[source_index] = []
                single_ion_particles_waveform[source_index] = []
                for time_index in range(time_length):
                    total_ion_power = self.ids.source[source_index].global_quantities[time_index].total_ion_power
                    if total_ion_power < 0:
                        total_ion_power = 0.0
                    total_ion_particles = (
                        self.ids.source[source_index].global_quantities[time_index].total_ion_particles
                    )
                    if total_ion_particles < 0:
                        total_ion_particles = 0.0
                    single_ion_power_waveform[source_index].append(total_ion_power)
                    single_ion_particles_waveform[source_index].append(total_ion_particles)
                    total_ion_power_waveform[time_index] = total_ion_power_waveform[time_index] + total_ion_power
                    total_ion_particles_waveform[time_index] = (
                        total_ion_particles_waveform[time_index] + total_ion_particles
                    )

                single_ion_power_waveform[source_index] = np.array(single_ion_power_waveform[source_index])
                single_ion_particles_waveform[source_index] = np.array(single_ion_particles_waveform[source_index])
        return {
            "single_ion_power_waveform": single_ion_power_waveform,
            "single_ion_particles_waveform": single_ion_particles_waveform,
            "total_ion_power_waveform": total_ion_power_waveform,
            "total_ion_particles_waveform": total_ion_particles_waveform,
        }

    def get_single_and_total_current_torque(self, time_slice):
        """
        The function `get_single_and_total_current_torque` calculates the total and individual current and torque
        waveforms for a given set of sources.

        Returns:
            a dictionary with the following keys and values:
            "total_current_waveform": total_current_waveform,
            "total_torque_waveform": total_torque_waveform,
            "single_current_waveform": single_current_waveform,
            "single_torque_waveform": single_torque_waveform,
        """
        # SINGLE AND TOTAL CURRENT AND TORQUE
        # total_current_waveform = [0] * ntime  # waveform
        # total_torque_waveform = [0] * ntime  # waveform
        # single_current_waveform = dict()  # waveform
        # single_torque_waveform = dict()  # waveform

        time_length = len(self.ids.time)

        total_current_waveform = np.zeros(time_length)  # waveform
        total_torque_waveform = np.zeros(time_length)  # waveform
        single_current_waveform = {}  # waveform
        single_torque_waveform = {}  # waveform

        sources = self.get_valid_and_active_sources(time_slice)
        for source_index, source in sources.items():
            if source["valid"] and source["active"]:
                single_current_waveform[source_index] = []
                single_torque_waveform[source_index] = []
                for time_index in range(time_length):
                    current_parallel = self.ids.source[source_index].global_quantities[time_index].current_parallel
                    if current_parallel < -1.0e40:
                        current_parallel = 0.0
                    torque_tor = get_compat_attr(
                        self.ids.source[source_index].global_quantities[time_index], "torque_tor", "torque_phi"
                    )

                    if torque_tor < 0:
                        torque_tor = 0.0

                    total_current_waveform[time_index] = total_current_waveform[time_index] + current_parallel
                    total_torque_waveform[time_index] = total_torque_waveform[time_index] + torque_tor
                    single_current_waveform[source_index].append(current_parallel)
                    single_torque_waveform[source_index].append(torque_tor)
                single_current_waveform[source_index] = np.array(single_current_waveform[source_index])
                single_torque_waveform[source_index] = np.array(single_torque_waveform[source_index])

        return {
            "total_current_waveform": total_current_waveform,
            "total_torque_waveform": total_torque_waveform,
            "single_current_waveform": single_current_waveform,
            "single_torque_waveform": single_torque_waveform,
        }
