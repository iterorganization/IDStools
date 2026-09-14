import itertools
import logging

import numpy as np
from scipy import constants, interpolate

from idstools.compute.common import get_closest_of_given_value_from_array
from idstools.compute.equilibrium import EquilibriumCompute
from idstools.compute.waves import WavesCompute

logger = logging.getLogger("module")


class EcStrayCompute:
    def __init__(self, equilibrium_ids: object, core_profiles_ids: object, waves_ids: object):
        self.equilibrium_ids = equilibrium_ids
        self.core_profiles_ids = core_profiles_ids
        self.waves_ids = waves_ids

        self.equilibrium_compute = EquilibriumCompute(equilibrium_ids)
        # self.coreProfilesCompute = coreProfilesIds
        self.waves_compute = WavesCompute(waves_ids)

    def get_resonance_layer(self, coherent_wave_index, time_slice, n_harm=None, equilibrium_time_slice=None):
        """This function calculates and returns a dictionary (Resonance Layer) containing r and z values
        corresponding to the resonance points based on the provided nHarm values, b_resonance, and b_total arrays.

        Args:
            time_slice (int): time index, default is 0
            n_harm (list, optional):  integer values that represent the order or index of harmonics
                in a series. Defaults to [1, 2, 3, 4].

        Returns:
            dict: returns dictionary of  resonance layer for specific harmonics

        Examples:
            .. code-block:: python

                import imas
                # add necessary imports
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3", "r")
                connection.open()
                equilibriumIds = connection.get('equilibrium')
                coreProfilesIds = connection.get('waves')
                wavesIds = connection.get('core_profiles')

                ecstrayCompute = EcStrayCompute(equilibriumIds, coreProfilesIds, wavesIds)

                resonance_layer = ecstrayCompute.get_resonance_layer()

                {0: {'r': [5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375,
                5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375, 5.4375],
                'z': [-6.0, -5.90625, -5.8125, -5.71875, -5.625, -5.53125, -5.4375, -5.34375, -5.25, -5.15625,
                5.71875, 5.8125, 5.90625, 6.0]}, 1: {'r': [], 'z': []}, 2: {'r': [], 'z': []}, 3: {'r': [], 'z': []}}

        """
        if n_harm is None:
            n_harm = [1, 2, 3, 4]
        if equilibrium_time_slice is None:
            equilibrium_time_slice = time_slice

        b_resonance = self.waves_compute.get_b_resonance(coherent_wave_index, time_slice, harmonic_frequencies=n_harm)
        profile2d_index, b_total = self.equilibrium_compute.get_b_total(equilibrium_time_slice)
        if profile2d_index != -99:
            r = self.equilibrium_compute.ids.time_slice[equilibrium_time_slice].profiles_2d[profile2d_index].grid.dim1
            z = self.equilibrium_compute.ids.time_slice[equilibrium_time_slice].profiles_2d[profile2d_index].grid.dim2

        [nr, nz] = np.shape(b_total)
        b_err = 10 / nr

        resonance_layer = {}
        for index_harm in range(len(n_harm)):
            resonance_layer[index_harm] = {"r": [], "z": []}
            for iz in range(nz):
                [ir, rloc] = get_closest_of_given_value_from_array(b_total[:, iz], b_resonance[index_harm])
                if np.abs(b_total[ir, iz] - b_resonance[index_harm]) < b_err:
                    resonance_layer[index_harm]["r"].append(r[ir])
                    resonance_layer[index_harm]["z"].append(z[iz])

        return {"profile2d_index": profile2d_index, "resonance_layer": resonance_layer}

    def get_cutoff_layer(self, coherent_wave_index, time_slice):
        """The cutoff layer is a region in a plasma where certain frequencies or modes of wave propagation
        are prevented from propagating or transmitting due to the plasma's properties.

        Args:
            time_slice (int, optional): time index. Defaults to 0.

        Returns:
            dict: cut off layer in dictionary format

        Notes:

            ω_R = √[(eB/m_e/2)^2 + n_e * e^2/(ε_0 * m_e)] + eB/m_e/2

            electron cyclotron frequency in plasma physics. It is denoted by ω_R and can be calculated
            using the equation

            where:

            - ``ω_R`` is the electron cyclotron frequency
            - ``e`` is the elementary charge
            - ``B`` is the magnetic field strength
            - ``m_e`` is the mass of an electron
            - ``n_e`` is the electron number density
            - ``ε_0`` is the vacuum permittivity

        Examples:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3","r")
                connection.open()
                equilibriumIds = connection.get('equilibrium')
                coreProfilesIds = connection.get('waves')
                wavesIds = connection.get('core_profiles')

                ecStrayCompute = EcStrayCompute(equilibriumIds, coreProfilesIds, wavesIds)

                cut_off_layer = ecStrayCompute.get_cutoff_layer()

                {'r': [5.625, 5.4375, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125,
                5.53125, 5.53125, 5.53125, 5.53125, 5.53125,
                5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.53125, 5.4375],
                'z': [-2.15625, -2.0625, -1.96875, -1.875, -1.78125, -1.6875, -1.59375,
                -1.5, -1.40625, -1.3125, -1.21875,
                1.03125, 1.125, 1.21875, 1.3125, 1.40625, 1.5, 1.59375, 1.6875, 1.78125,
                1.875, 1.96875, 2.0625, 2.15625]}

        """
        # wavecompute = WavesCompute(self.wavesIds)
        omega_ec = self.waves_compute.get_omega_ec(coherent_wave_index, time_slice)

        # Find (R,Z) rectangular grid of B-field
        # eqcomputeobj = EquilibriumCompute(self.equilibriumIds)
        profile2d_index, b_total = self.equilibrium_compute.get_b_total(time_slice)

        # B(R,Z) evaluation
        r = self.equilibrium_ids.time_slice[time_slice].profiles_2d[profile2d_index].grid.dim1
        z = self.equilibrium_ids.time_slice[time_slice].profiles_2d[profile2d_index].grid.dim2

        # Ne(psi) in core_profiles IDS
        # rho1d_cp = self.coreProfilesIds.profiles_1d[timeIndexCoreProfiles].grid.rho_tor_norm
        psi1d_cp = (
            self.core_profiles_ids.profiles_1d[time_slice].grid.psi
            - self.core_profiles_ids.profiles_1d[time_slice].grid.psi[-1]
        ) / (
            self.core_profiles_ids.profiles_1d[time_slice].grid.psi[0]
            - self.core_profiles_ids.profiles_1d[time_slice].grid.psi[-1]
        )
        ne_cp = self.core_profiles_ids.profiles_1d[time_slice].electrons.density

        # Ne(psi) interpolated over equilibrium IDS
        # rho1d_eq = self.equilibriumIds.time_slice[timeIndexEquilibrium].profiles_1d.rho_tor_norm
        psi1d_eq = (
            self.equilibrium_ids.time_slice[time_slice].profiles_1d.psi
            - self.equilibrium_ids.time_slice[time_slice].profiles_1d.psi[-1]
        ) / (
            self.equilibrium_ids.time_slice[time_slice].profiles_1d.psi[0]
            - self.equilibrium_ids.time_slice[time_slice].profiles_1d.psi[-1]
        )
        ne_eq = np.zeros(len(psi1d_eq))
        ne_interp = interpolate.interp1d(psi1d_cp, ne_cp, kind="linear")
        for i in range(len(psi1d_eq)):
            ne_eq[i] = float(ne_interp(psi1d_eq[i]))

        # Ne(R,Z) deduced for each point over B(R,Z) in equilibrium IDS
        psi1d_eq = self.equilibrium_ids.time_slice[time_slice].profiles_1d.psi
        psi2d_eq = self.equilibrium_ids.time_slice[time_slice].profiles_2d[profile2d_index].psi
        ne_from_psi = interpolate.interp1d(psi1d_eq, ne_eq, kind="linear")
        ne2d_eq = np.zeros(np.shape(psi2d_eq))
        omega_r = np.zeros(np.shape(psi2d_eq))
        for ir, iz in itertools.product(range(len(r)), range(len(z))):
            try:  # Inside LCFS
                ne2d_eq[ir, iz] = ne_from_psi(psi2d_eq[ir, iz])
                # omega_R = sqrt[(eB/m_e/2)**2 + n_e *e**2/(epsilon_0*m_e)] + eB/m_e/2
                omega_r[ir, iz] = np.sqrt(
                    (constants.e * b_total[ir, iz] / (2 * constants.m_e)) ** 2
                    + ne2d_eq[ir, iz] * constants.e**2 / (constants.epsilon_0 * constants.m_e)
                ) + constants.e * b_total[ir, iz] / (2 * constants.m_e)
            except Exception as e:  # Not defined outside LCFS
                logger.debug(f"{e}")
                ne2d_eq[ir, iz] = -1  # np.nan
                omega_r[ir, iz] = -1  # np.nan

        # Find (R,Z) where omega_R = omega_EC (within the tolerance omega_err)
        [nr, nz] = np.shape(omega_r)
        omega_err = 100 / nr

        cutoff_layer = {"r": [], "z": []}
        for iz in range(nz):
            [ir, rloc] = get_closest_of_given_value_from_array(omega_r[:, iz], omega_ec)
            if np.abs((omega_r[ir, iz] - omega_ec) / omega_r[ir, iz]) < omega_err:
                cutoff_layer["r"].append(r[ir])
                cutoff_layer["z"].append(z[iz])

        return cutoff_layer
