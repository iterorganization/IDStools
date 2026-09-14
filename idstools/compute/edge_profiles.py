"""
This module provides compute functions and classes for edge_profiles ids data

`refer data dictionary <https://imas-data-dictionary.readthedocs.io/en/latest/>`_.

"""

import functools
import itertools
import logging
from typing import Union

import numpy as np
from scipy import interpolate

import idstools.init_mendeleiev as mend

logger = logging.getLogger("module")


class EdgeProfilesCompute:
    """This class provides compute functions for edge profiles ids.

    Attributes:
        ids (object): The edge profiles IDS (Integrated Data Structure) object containing
            edge and scrape-off layer plasma profile data including density, temperature,
            and potential profiles near the plasma boundary.
    """

    def __init__(self, ids):
        self.ids = ids

    @staticmethod
    def get_plasma_composition_with_species_concentration(ids, time_slice) -> Union[dict, int]:
        """
        Function retrives composition and species concentration in below format
            - Spcies_label
                - a
                - nspec_over_ne
                - nspec_over_nmaj
                - nspec_over_ntot
                - species [mendeleiev_table]
                - states
                    - label
                    - n_ni
                    - states_density [list]
                    - z_average

        Args:
            ids ([ids_object]): filled ids object
            time_slice (int, optional): [slice on which functions should operate on]. Defaults to 0.

        Returns:
            [dict]: [species wise data in dictionary format]

        Example:
            .. code-block:: python

                import imas
                from idstools.compute.edge_profiles import EdgeProfilesCompute

                connection = imas.DBEntry(
                    \"imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3\", \"r\")
                idsObj = connection.get('edge_profiles')
                connection.close()
                result = EdgeProfilesCompute.get_plasma_composition_with_species_concentration(idsObj, 0)

                {'0':
                    {'a': 2.0,
                    'label': 'D',
                    'nspec_over_ne': 0.0,
                    'nspec_over_nmaj': 0.0,
                    'nspec_over_ntot': 0.0,
                    'species': 'D',
                    'states':
                        {'0':
                            {'label': ' D+1',
                            'n_ni': 100.0,
                            'states_density': [1.6577031350573213e+22],
                            'z_average': 1.0}},
                            'z': 1},
                '1':
                    {'a': 4.0,
                    'label': 'He',
                    'nspec_over_ne': 0.007831354424836625,
                    'nspec_over_nmaj': 0.008250985371197173,
                    'nspec_over_ntot': 0.008146485662619047,
                    'species': 'He4',
                    'states':
                        {'0':
                            {'label': ' He+1',
                            'n_ni': 0.9279275264034698,
                            'states_density': [1.2691899775336492e+18,
                            1.3550765319392264e+20],
                            'z_average': 1.0},
                        '1':
                            {'label': ' He+2',
                            'n_ni': 99.07207247359639,
                            'states_density': [1.2691899775336492e+18, 1.3550765319392264e+20],
                            'z_average': 2.0}},
                            'z': 2},
        """
        try:
            ids.ggd[time_slice]

        except Exception as e:
            logger.debug(f"{e}")
            logger.critical(f"edge_profiles IDS:slice not found {e}")
            return 0

        edge_profiles_compute = EdgeProfilesCompute(ids)

        if edge_profiles_compute.get_volume(time_slice) is None:
            return -1

        data = {}
        nspec_over_ntot = edge_profiles_compute.get_nspec_over_ntot(time_slice)
        nspec_over_ne = edge_profiles_compute.get_nspec_over_ne(time_slice)
        nspec_over_nmaj = edge_profiles_compute.get_nspec_over_nmaj(time_slice)
        species = edge_profiles_compute.get_species(time_slice)
        labels = edge_profiles_compute.get_labels(time_slice)
        edge_profiles_compute.combine_species_when_appear_twice(
            time_slice, species, nspec_over_ntot, nspec_over_ne, nspec_over_nmaj
        )
        a = edge_profiles_compute.get_a(time_slice)
        z = edge_profiles_compute.get_z(time_slice)
        states_data = edge_profiles_compute.get_states_data(time_slice)
        for species_index in range(len(species)):
            species_data = {
                "nspec_over_ntot": nspec_over_ntot[species_index],
                "nspec_over_ne": nspec_over_ne[species_index],
                "nspec_over_nmaj": nspec_over_nmaj[species_index],
                "a": a[species_index],
                "z": z[species_index],
                "species": species[species_index],
                "states": states_data[str(species_index)],
                "label": labels[species_index],
            }
            data[str(species_index)] = species_data

        return data

    def get_labels(self, time_slice: int):
        """
        This function returns a list of labels for all species in a given time slice.

        Args:
            time_slice: an optional integer parameter that specifies the time slice on which the function
                should operate. The default value is 0

        Returns:
            a list of labels for all species in a given time slice.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getLabels(time_slice=0)

                ['D', 'He', 'Ne', 'Be', ' D2+']
        """

        nspecies = len(self.ids.ggd[time_slice].ion)
        labels = [self.ids.ggd[time_slice].ion[ispecies].label for ispecies in range(nspecies)]
        logger.debug(f"Species identification :{labels}")
        return labels

    @functools.lru_cache(maxsize=128)
    def get_a(self, time_slice: int, element_index: int = 0) -> list:
        """
        This function returns a list of atomic masses for a given slice and element index.

        Args:
            time_slice (int, optional): The index of the slice in the `ggd` list that contains the ion information.
                Defaults to 0
            element_index (int, optional): Element index, It is used to access the 'a' attribute of the element object.
                Defaults to 0

        Returns:
            a list of atomic masses for each species in the given slice index and element index.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_a(time_slice=0)

                [2.0, 4.0, 20.0, 9.0, 2.0]
        """
        nspecies = len(self.ids.ggd[time_slice].ion)
        a = [0] * nspecies
        for ispecies in range(nspecies):
            a[ispecies] = self.ids.ggd[time_slice].ion[ispecies].element[element_index].a

        logger.debug(f"Mass of atom : {str(a)}")
        return a

    @functools.lru_cache(maxsize=128)
    def get_z(self, time_slice: int, element_index: int = 0) -> list:
        """
        This function returns a list of nuclear charges for each species in a given slice and element
        index.

        Args:
            time_slice (int, optional): time slice on which functions should operate on. Defaults to 0.
            element_index (int, optional): element of the atom or molecule on which functions should operate on.
                Defaults to 0.

        Returns:
            a list of nuclear charges for each species in the given time_slice and element_index.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_z(time_slice=0)

                [1, 2, 10, 4, 1]
        """
        # TODO why always element_index = 0 we are picking up
        nspecies = len(self.ids.ggd[time_slice].ion)
        z = [0] * nspecies
        for ispecies in range(nspecies):
            z[ispecies] = int(self.ids.ggd[time_slice].ion[ispecies].element[element_index].z_n)
        logger.debug(f"Nuclear charge each species : {z}")
        return z

    def get_states(self, time_slice: int):
        """
        This function returns quantities related to the different states of the species (ionisation, energy,
        excitation, ...) for each species

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a list of states (ionisation, energy, excitation, etc.) in  the input data of each species .

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getStates(time_slice=0)

                print(result[0]) # state object from species

                # class 'imas_3_38_1_ual_4_11_4.edge_profiles.ggd_ion_state__structArray'
        """
        nspecies = len(self.ids.ggd[time_slice].ion)
        return [self.ids.ggd[time_slice].ion[i_species].state for i_species in range(nspecies)]

    def get_states_data(self, time_slice: int) -> dict:
        """
        This function returns a dictionary containing data on the states and densities of different species
        in a plasma simulation.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a dictionary containing information about the states of different species in a plasma, including
            their labels, z-averages, densities, and relative densities.


        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getStatesData(time_slice=0)

                {'0':
                {'0':
                {'label': ' D+1',
                'n_ni': 100.0,
                'states_density': [1.6577031350573213e+22],
                'z_average': 1.0}},
                '1':
                {'0': {'label': ' He+1',
                'n_ni': 0.9279275264034698,
                'states_density': [1.2691899775336492e+18, 1.3550765319392264e+20],
                'z_average': 1.0},
                '1':
                {'label': ' He+2',
                'n_ni': 99.07207247359639,
                'states_density': [1.2691899775336492e+18, 1.3550765319392264e+20],
                'z_average': 2.0}},
        """

        states_data = {}

        volume = self.get_volume(time_slice)
        nspecies = len(self.ids.ggd[time_slice].ion)
        species_density, _, _ = self.get_species_density(time_slice)
        for species_index in range(nspecies):
            species_data = {}
            nstates = len(self.ids.ggd[time_slice].ion[species_index].state)
            states_density = [0] * nstates
            for state_index in range(nstates):
                state_data = {"label": self.ids.ggd[time_slice].ion[species_index].state[state_index].label}
                for xd in self.ids.ggd[time_slice].ion[species_index].state[state_index].z_average:
                    if xd.grid_subset_index == 5:
                        state_data["z_average"] = xd.values[0]

                for xd in self.ids.ggd[time_slice].ion[species_index].state[state_index].density:
                    if xd.grid_subset_index == 5:
                        states_density[state_index] = sum(np.array(volume) * np.array(xd.values))
                        break
                state_data["states_density"] = states_density
                state_data["n_ni"] = 100 * states_density[state_index] / species_density[species_index]
                species_data[str(state_index)] = state_data
            states_data[str(species_index)] = species_data
        return states_data

    def get_ne(self, time_slice: int) -> float:
        """
        This function calculates the total number of electrons (ne) based on the volume and electron density
        of a given slice.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            the total number of electrons (ne) in the given slice of the object, calculated by multiplying the
            volume of the slice with its electron density and summing the results.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_ne(time_slice=0)

                1.7465285792413856e+22
        """
        volume = self.get_volume(time_slice)
        electron_density = self.get_density(time_slice)
        logger.info(f"Total no. electrons (ne): {str(sum(volume * electron_density))}")
        return sum(volume * electron_density)

    @functools.lru_cache(maxsize=128)
    def get_volume(self, time_slice) -> Union[list, None]:
        """
        This function calculates the volume of a grid subset using either pre-calculated volume data or by
        manually calculating it from the nodes.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a list of volumes for each element in the grid subset. If the volumes are not available in the cells,
            it calculates the volumes manually from the nodes. If the volumes are still empty, it returns None.
            Finally, it returns the volumes list.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getVolume(time_slice=0)

                [0.00037247887179986,
                0.00036873285033229,
                0.00036505732877168,
                0.00035287806726545,
                0.00034083126399982,
                0.00032428140427918,
                0.00030192063059504,
                0.00027702026849475,
                0.0002505748085483,
                0.00021528820409221]
        """
        IDENTIFIER_CELLS_INDEX = 5  # cells identifier
        cells_grid_subset = None
        for grid_subset in self.ids.grid_ggd[time_slice].grid_subset:
            if grid_subset.identifier.index == IDENTIFIER_CELLS_INDEX:
                cells_grid_subset = grid_subset
        elements = []
        if cells_grid_subset:
            elements = cells_grid_subset.element

        num_vertices = len(elements)
        if num_vertices == 0:
            logger.warning("edge_profiles IDS:No element found in grid subset")
            return None
        volumes = [0] * num_vertices

        for ielement, element in enumerate(elements):
            for obj in element.object:
                # Get mapping information from element like, space, dimension and index
                # which we need to look in space object
                space_index = obj.space - 1
                dimension_index = obj.dimension - 1
                object_index = obj.index - 1

                # Get geometry_content.index to check what is stored in the geometry array
                geometry_content_index = (
                    self.ids.grid_ggd[time_slice]
                    .space[space_index]
                    .objects_per_dimension[dimension_index]
                    .geometry_content.index
                )
                # if geometry_content => face_indices_volume or face_indices_volume_connection it contains the volume
                if geometry_content_index in [31, 32]:
                    # Get the object which is mapped from grid_subset to space
                    obj_dim = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[dimension_index]
                        .object[object_index]
                    )
                    # The third element contains the volume, read the same
                    volumes[ielement] = obj_dim.geometry[2]
        if not np.any(volumes):
            logger.debug(
                "edge_profiles IDS:volume is not available in cells (face_indices_volume).. \
                Calculating manually from nodes "
            )
            # Get volume from nodes if volumes are still empty
            for ielement, element in enumerate(elements):
                for obj in element.object:
                    # Get mapping information from element like, space, dimension and index
                    # which we need to look in space object
                    space_index = obj.space - 1
                    dimension_index = obj.dimension - 1
                    object_index = obj.index - 1

                    # Get all nodes of the cell object
                    nodes = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[dimension_index]
                        .object[object_index]
                        .nodes
                    )
                    # Decrement by 1 to compensate zero based indexing
                    nodes = nodes - 1
                    # Get R and Z values from nodes deom object_per_dimesnion 0
                    r1, z1 = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[0]
                        .object[nodes[0]]
                        .geometry
                    )
                    r2, z2 = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[0]
                        .object[nodes[1]]
                        .geometry
                    )

                    r3, z3 = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[0]
                        .object[nodes[2]]
                        .geometry
                    )
                    r4, z4 = (
                        self.ids.grid_ggd[time_slice]
                        .space[space_index]
                        .objects_per_dimension[0]
                        .object[nodes[3]]
                        .geometry
                    )
                    area = 0.5 * ((r1 * z2 + r2 * z3 + r3 * z4 + r4 * z1) - (r2 * z1 + r3 * z2 + r4 * z3 + r1 * z4))
                    bary_r = (
                        1.0
                        / (6.0 * area)
                        * (
                            (r1 + r2) * (r1 * z2 - r2 * z1)
                            + (r2 + r3) * (r2 * z3 - r3 * z2)
                            + (r3 + r4) * (r3 * z4 - r4 * z3)
                            + (r4 + r1) * (r4 * z1 - r1 * z4)
                        )
                    )

                    volumes[ielement] = 2.0 * np.pi * bary_r * area

        if not np.any(volumes):
            logger.critical("edge_profiles IDS: volumes are empty")
            return None
        logger.info(f"Total volume:{np.sum(volumes)}")
        return volumes

    def get_density(self, time_slice):
        """
        This function retrieves the electron density array for a given slice index and returns it.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            the electron density array for a specific slice index, and also logging the array and the total
            electron density.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getDensity(time_slice=0)

                array([1.83014037e+19, 2.86305333e+19, 4.50302324e+19, 6.99266610e+19,
                1.04025196e+20, 1.56969187e+20, 2.32851365e+20, 3.45402170e+20,
                4.94164863e+20, 7.07373803e+20])
        """
        density_ion = next(
            (xd.values for xd in self.ids.ggd[time_slice].electrons.density if xd.grid_subset_index == 5),
            None,
        )
        logger.debug(f"Electrons density array:{density_ion}")
        logger.info(f"Total Electrons density:{sum(density_ion)}")
        return density_ion

    @functools.lru_cache(maxsize=128)
    def get_species_density(self, time_slice: int) -> tuple:
        """
        This function calculates the density of different species in a given slice and returns a tuple containing
        the species density list, the total density, and the index of the species with the maximum density.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a tuple containing three values: a list of species density, the total density of all species, and the
            index of the species with the maximum density.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getSpeciesDensity(time_slice=0)

                ([1.6577031350573213e+22,
                1.3677684317145648e+20,
                6.227201649981566e+19,
                1.3510799045753078e+19,
                8.356155820974862e+16],
                1.6789674570848447e+22,
                0)
        """
        nspecies = len(self.ids.ggd[time_slice].ion)
        volume = self.get_volume(time_slice)
        ntot = 0
        species_density_list = [0] * nspecies
        max_density = -999.0
        max_density_index = 0
        for ispecies in range(nspecies):
            for xd in self.ids.ggd[time_slice].ion[ispecies].density:
                if xd.grid_subset_index == 5:
                    species_density_list[ispecies] = sum(np.array(volume) * np.array(xd.values))
                    break

            if len(self.ids.ggd[time_slice].ion[ispecies].density) == 0:
                logger.warning(
                    "edge_profiles IDS: species density not found for "
                    + self.ids.ggd[time_slice].ion[ispecies].label
                    + ", Getting density from state."
                )
                density = None
                for counter, state in enumerate(self.ids.ggd[time_slice].ion[ispecies].state):
                    for xd in state.density:
                        if xd.grid_subset_index == 5:
                            if counter == 0:
                                density = np.array([0] * len(xd.values))
                                density = np.add(density, np.array(xd.values))
                            else:
                                density = np.add(density, np.array(xd.values))
                            break
                species_density_list[ispecies] = sum(np.array(volume) * density)
            ntot = ntot + species_density_list[ispecies]
            if species_density_list[ispecies] > max_density:
                max_density = species_density_list[ispecies]
                max_density_index = ispecies
        logger.debug(f"Species density : {species_density_list}")
        logger.debug(f"Sum of Species Density (ntot) : {ntot}")
        logger.debug(f"Index of Maximum Density Species : {max_density_index}")
        return species_density_list, ntot, max_density_index

    def get_nspec_over_ntot(self, time_slice):
        """
        This function calculates the ratio of the number of species to the total number of particles in a plasma.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            The function `get_nspec_over_ntot` is returning the ratio of the list of species densities to the
            total density (`ntot`).

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_nspec_over_ntot(time_slice=0)

                array([9.87334881e-01, 8.14648566e-03, 3.70894720e-03, 8.04708810e-04, 4.97696116e-06])

        """
        species_density_list, ntot, _ = self.get_species_density(time_slice)
        return species_density_list / ntot

    def get_nspec_over_ne(self, time_slice):
        """
        This function calculates the ratio of species density to electron density.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            the ratio of the species density list to the electron density (ne).

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_nspec_over_ne(time_slice=0)

                array([9.49141717e-01, 7.83135442e-03, 3.56547366e-03, 7.73580187e-04, 4.78443692e-06])
        """
        species_density_list, _, _ = self.get_species_density(time_slice)
        ne = self.get_ne(time_slice)
        return species_density_list / ne

    def get_nspec_over_nmaj(self, time_slice) -> list:
        """
        This function returns a list of the ratio of each species density to the maximum species density.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a list of values obtained by dividing each element of the list `species_density_list` by the maximum
            value in that list. This list represents the ratio of the density of each species to the density of
            the most abundant species.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.get_nspec_over_nmaj()

                array([1.00000000e+00, 8.25098537e-03, 3.75652402e-03, 8.15031278e-04,5.04080353e-06])
        """
        (
            species_density_list,
            _,
            max_density_index,
        ) = self.get_species_density(time_slice)
        return species_density_list / species_density_list[max_density_index]

    def get_species(self, time_slice) -> list:
        """
        This function creates a Mendeleiev table and returns a list of species based on the values of a,
        z, and the table.

        Args:
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.

        Returns:
            a list of species based on the values of a, z, and the Mendeleev table.

        Example:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=123276;run=1;database=ITER;version=3", "r")
                idsObj = connection.get('edge_profiles')
                computeObj = EdgeProfilesCompute(idsObj)
                result = computeObj.getSpecies()

                ['D', 'He4', 'Ne', 'Be', 'D']
        """
        table_mendeleiev = mend.create_table_mendeleiev()
        nspecies = len(self.ids.ggd[time_slice].ion)

        a = list(map(int, self.get_a(time_slice)))
        z = list(map(int, self.get_z(time_slice)))
        return [table_mendeleiev[z[ispecies]][a[ispecies]].element for ispecies in range(nspecies)]

    def combine_species_when_appear_twice(self, time_slice, species, nspec_over_ntot, nspec_over_ne, nspec_over_nmaj):
        """
        This is helper function which checks if there are duplicate entries of species and combine the species.
        This is in place change of arrays

        Args:
            species (list): result from get_species()
            nspec_over_ntot (list): result from get_nspec_over_ntot()
            nspec_over_ne (list): result from get_nspec_over_ne()
            nspec_over_nmaj (list): result from get_nspec_over_nmaj()
            time_slice (int, optional): time slice on which function should operate on. Defaults to 0.
        """
        nspecies = len(self.ids.ggd[time_slice].ion)
        for ispecies, jspecies in itertools.product(range(nspecies), range(nspecies)):
            if (species[jspecies] == species[ispecies]) & (jspecies != ispecies):
                nspec_over_ntot[ispecies] = nspec_over_ntot[ispecies] + nspec_over_ntot[jspecies]
                nspec_over_ntot[jspecies] = 0
                nspec_over_ne[ispecies] = nspec_over_ne[ispecies] + nspec_over_ne[jspecies]
                nspec_over_ne[jspecies] = 0
                nspec_over_nmaj[ispecies] = nspec_over_nmaj[ispecies] + nspec_over_nmaj[jspecies]
                nspec_over_nmaj[jspecies] = 0

    def get_core_boundry(self, time_slice):
        """
        This function `get_core_boundry` retrieves coordinates for core boundary elements from grid subsets based on
        specified indices.

        Args:
            time_slice: The `time_slice` parameter

        Returns:
            the coordinates of the elements in the grid subset that corresponds to either the core_boundry
        or core subset, depending on which one is found and has non-zero elements.
        """
        CORE_BOUNDRY_SUBSET_INDEX = 15  # core_boundry
        CORE_SUBSET_INDEX = 22  # Core
        core_boundry_grid_subset = None
        core_grid_subset = None
        for grid_subset in self.ids.grid_ggd[time_slice].grid_subset:
            if grid_subset.identifier.index == CORE_BOUNDRY_SUBSET_INDEX:
                core_boundry_grid_subset = grid_subset
                logger.info(
                    f"Found Grid subset for core_boundry subset name:{grid_subset.identifier.name}, Index: \
                    {grid_subset.identifier.index}"
                )
            if grid_subset.identifier.index == CORE_SUBSET_INDEX:
                core_grid_subset = grid_subset
                logger.info(
                    f"Found Grid subset for core name:{grid_subset.identifier.name}, Index: \
                    {grid_subset.identifier.index}"
                )
        if core_boundry_grid_subset or core_grid_subset:
            if core_boundry_grid_subset is not None and len(core_boundry_grid_subset.element) != 0:
                grid_subset = core_boundry_grid_subset

            elif core_grid_subset is not None and len(core_grid_subset.element) != 0:
                grid_subset = core_grid_subset

        num_sep = len(grid_subset.element)
        sep_coords = np.zeros((num_sep, 2))

        for ielement, element in enumerate(grid_subset.element):
            for obj in element.object:
                index = obj.index - 1  # 1 based indexing
                space = obj.space - 1
                dim = 0  # choosing nodes 1=nodes, 2=edges, 3=faces, 4=cells/volumes
                if len(self.ids.grid_ggd[time_slice].space[space].objects_per_dimension[dim].object) > index:
                    sep_coords[ielement, :] = (
                        self.ids.grid_ggd[time_slice].space[space].objects_per_dimension[dim].object[index].geometry[:2]
                    )
                else:
                    logger.warning(f"Grid object at index {index} not found in space {space} dimension {dim}")
        # hull = ConvexHull(sep_coords[0 : num_sep - 1, :])  # find a closed core_boundry contour
        # core_boundry = np.array([sep_coords[hull.vertices, 0], sep_coords[hull.vertices, 1]]).T
        return sep_coords

    def get_separatrix(self, time_slice):
        """
        This function `get_separatrix` retrieves coordinates for the separatrix from a grid subset based on a given time
        slice.

        Args:
            time_slice: The `time_slice` parameter

        Returns:
            The function `get_separatrix` is returning the coordinates of the separatrix elements found in
            the grid subset for the given time slice. The coordinates are stored in a NumPy array
            `sep_coords`, where each row represents the coordinates of a separatrix element.
        """
        SUBSET_INDEX = 16  # separatrix
        separatix_grid_subset = None
        for grid_subset in self.ids.grid_ggd[time_slice].grid_subset:

            if grid_subset.identifier.index == SUBSET_INDEX:
                separatix_grid_subset = grid_subset
                logger.info(
                    f"Found Grid subset for separatrix name:{grid_subset.identifier.name}, Index: \
                    {grid_subset.identifier.index}"
                )
        if separatix_grid_subset is None:
            logger.warning("edge_profiles IDS:Separatrix not found")
            return None
        num_sep = len(separatix_grid_subset.element)
        # if num_sep == 0:
        #     logger.warning("edge_profiles IDS:No element found in separatrix grid subset")
        #     return None
        sep_coords = np.zeros((num_sep, 2))

        for ielement, element in enumerate(separatix_grid_subset.element):
            for obj in element.object:
                index = obj.index - 1  # 1 based indexing
                space = obj.space - 1
                dim = 0  # choosing nodes 1=nodes, 2=edges, 3=faces, 4=cells/volumes
                sep_coords[ielement, :] = (
                    self.ids.grid_ggd[time_slice].space[space].objects_per_dimension[dim].object[index].geometry[:2]
                )
        # hull = ConvexHull(sep_coords[0 : num_sep - 1, :])  # find a closed separatrix contour
        # separatrix = np.array([sep_coords[hull.vertices, 0], sep_coords[hull.vertices, 1]]).T
        return sep_coords

    def get_rz(self, time_slice):
        """
        The function `get_rz` returns the `r_edge` and `z_edge` coordinates of vertices in a grid.

        Returns:
            two arrays: r_edge and z_edge.
        """
        num_vertices = len(self.ids.grid_ggd[time_slice].space[0].objects_per_dimension[0].object)  # nodes dimension
        vertex_coords = np.zeros((num_vertices, 2))
        for vertex_id in range(num_vertices):
            vertex_coords[vertex_id, :] = (
                self.ids.grid_ggd[time_slice].space[0].objects_per_dimension[0].object[vertex_id].geometry[:2]
            )
        # Note : For  geometry_content=11 node coordinates (first 2 elements), then connection
        # length, and distance in the poloidal plane to the nearest solid surface outside
        # the separatrix
        r_edge = vertex_coords[:, 0]
        z_edge = vertex_coords[:, 1]
        return r_edge, z_edge

    # interpolate on rectangular x,y grid, for example a regular grid of 400 points
    def get_rectangular_grid(self, num_points=400):
        """
        The function `get_rectangular_grid` returns two arrays `x` and `y` that represent a meshgrid of points
        within a specified range.

        Args:
            num_points: The `num_points` parameter is an optional integer argument that specifies the number of points
                to generate in the x and y directions. By default, it is set to 400.

        Returns:
            two arrays, x and y.
        """
        x, y = np.meshgrid(np.linspace(4, 8.5, num_points), np.linspace(-4.5, 4.5, num_points))
        return x, y

    def get_electron_density(self, time_slice, x, y):
        """
        The function `get_electron_density` calculates the electron density at a given position (x, y) by interpolating
        values from a grid.

        Args:
            time_slice: time index
            x: The x-coordinate of the point where you want to calculate the electron density.
            y: The parameter "y" represents the y-coordinate of the point at which you want to calculate the electron
                density.

        Returns:
            the electron density at the given coordinates (x, y).
        """
        r_edge, z_edge = self.get_rz(time_slice)
        temp = None

        for electrons_density in self.ids.ggd[time_slice].electrons.density:
            if electrons_density.grid_subset_index == 1:  # nodes
                temp = electrons_density.values
        if temp is None:
            # TODO if nodes grid_subset is not available is it possible to get coordinated from other subsets?
            logger.warning("edge_profiles : electrons density values not found for nodes grid_subset")
            return None
        ne_edge = interpolate.griddata((r_edge, z_edge), temp, (x, y))
        return ne_edge

    def get_ion_density(self, time_slice, x, y):
        """
        The function `get_ion_density` calculates the ion density at a given position (x, y) by interpolating values
        from a grid.

        Args:
            time_slice: time index
            x: The parameter "x" represents the x-coordinate of the point at which you want to calculate the
                ion density.
            y: The parameter "y" represents the y-coordinate of the point at which you want to calculate the
                ion density.

        Returns:
            the ion density at the given coordinates (x, y).
        """
        r_edge, z_edge = self.get_rz(time_slice)
        temp = None
        for ion_density in self.ids.ggd[time_slice].ion[0].density:
            if ion_density.grid_subset_index == 1:  # nodes
                temp = ion_density.values

        if temp is None:
            logger.warning("edge_profiles : ion density values not found for nodes grid_subset")
            return None
        ni_edge = interpolate.griddata((r_edge, z_edge), temp, (x, y))
        return ni_edge

    def get_neutral_density(self, time_slice, x, y):
        """
        The function `get_neutral_density` calculates the neutral density at a given position (x, y) by
        interpolating values from a grid.

        Args:
            time_slice: time index
            x: The x parameter represents the x-coordinate of the point at which you want to calculate
                the neutral density.
            y: The parameter "y" represents the y-coordinate of the point at which you want to calculate
                the neutral density.

        Returns:
            the neutral density at the given coordinates (x, y).
        """
        r_edge, z_edge = self.get_rz(time_slice)

        temp = None
        for neutral_density in self.ids.ggd[time_slice].neutral[0].density:
            if neutral_density.grid_subset_index == 1:  # nodes
                temp = neutral_density.values

        if temp is None:
            logger.warning("edge_profiles : neutral.density values not found for nodes grid_subset")
            return None

        n_neutral_edge = interpolate.griddata((r_edge, z_edge), temp, (x, y))
        return n_neutral_edge

    def get_cell_polygons_and_values(self, time_slice, values):
        """
        Build a list of polygon vertex arrays and corresponding per-cell scalar values for
        direct rendering with ``matplotlib.collections.PolyCollection``.

        Args:
            time_slice: time index
            values: 1-D array of scalar values, either per-cell or per-node.

        Returns:
            tuple: ``(polygons, cell_values)`` where *polygons* is a list of ``(n_corners, 2)``
                float arrays (R, Z columns) and *cell_values* is a 1-D float array of the
                same length.  Returns ``(None, None)`` when the cells grid subset is unavailable.
        """
        r_nodes, z_nodes = self.get_rz(time_slice)
        values = np.asarray(values, dtype=float)

        cells_subset = None
        for grid_subset in self.ids.grid_ggd[time_slice].grid_subset:
            if grid_subset.identifier.name.lower() == "cells":
                cells_subset = grid_subset
                break

        if cells_subset is None or len(cells_subset.element) == 0:
            logger.warning("edge_profiles: cells grid subset not found, cannot build PolyCollection")
            return None, None

        n_cells = len(cells_subset.element)
        per_cell_mode = len(values) == n_cells  # True → direct 1:1, False → average from nodes

        polygons = []
        cell_values = []
        n_nodes = len(r_nodes)
        i = 0
        for element in cells_subset.element:
            for obj in element.object:
                space_index = obj.space - 1
                dimension_index = obj.dimension - 1
                object_index = obj.index - 1
                nodes = (
                    self.ids.grid_ggd[time_slice]
                    .space[space_index]
                    .objects_per_dimension[dimension_index]
                    .object[object_index]
                    .nodes
                )
                nodes = np.asarray(nodes, dtype=int) - 1  # convert to 0-based
                if np.any(nodes >= n_nodes) or np.any(nodes < 0):
                    logger.warning("edge_profiles: cell node index out of range, skipping cell")
                    i += 1
                    continue
                verts = np.column_stack((r_nodes[nodes], z_nodes[nodes]))
                polygons.append(verts)
                if per_cell_mode:
                    cell_values.append(float(values[i]))
                else:
                    cell_values.append(float(np.mean(values[nodes])))
                i += 1

        return polygons, np.array(cell_values, dtype=float)

    def get_electron_density_on_nodes(self, time_slice):
        """
        Return raw electron density values at mesh nodes (no rectangular resampling).

        Args:
            time_slice: time index

        Returns:
            numpy array of node-centred electron density values, or ``None`` if unavailable.
        """
        for electrons_density in self.ids.ggd[time_slice].electrons.density:
            if electrons_density.grid_subset_index == 1:  # nodes
                return np.asarray(electrons_density.values)
        logger.warning("edge_profiles: electron density values not found for nodes grid_subset")
        return None

    def get_electron_density_on_cells(self, time_slice):
        """
        Return electron density values.

        cell-centred values (``grid_subset_index == 5``, one value per cell.  Falls
        back to node values (``grid_subset_index == 1``) which will be averaged per cell further

        Args:
            time_slice: time index

        Returns:
            numpy array of density values, or ``None`` if unavailable.
        """
        for ed in self.ids.ggd[time_slice].electrons.density:
            if ed.grid_subset_index == 5:  # cell-centred
                return np.asarray(ed.values)
        return self.get_electron_density_on_nodes(time_slice)

    def get_ion_density_on_nodes(self, time_slice):
        """
        Return raw ion density values at mesh nodes (no rectangular resampling).

        Args:
            time_slice: time index

        Returns:
            numpy array of node-centred ion density values, or ``None`` if unavailable.
        """
        for ion_density in self.ids.ggd[time_slice].ion[0].density:
            if ion_density.grid_subset_index == 1:  # nodes
                return np.asarray(ion_density.values)
        logger.warning("edge_profiles: ion density values not found for nodes grid_subset")
        return None

    def get_ion_density_on_cells(self, time_slice):
        """
        Return ion density values.
        cell-centred values (``grid_subset_index == 5``), falls back to node values.
        """
        for id_ in self.ids.ggd[time_slice].ion[0].density:
            if id_.grid_subset_index == 5:
                return np.asarray(id_.values)
        return self.get_ion_density_on_nodes(time_slice)

    def get_neutral_density_on_nodes(self, time_slice):
        """
        Return raw neutral density values at mesh nodes (no rectangular resampling).

        Args:
            time_slice: time index

        Returns:
            numpy array of node-centred neutral density values, or ``None`` if unavailable.
        """
        for neutral_density in self.ids.ggd[time_slice].neutral[0].density:
            if neutral_density.grid_subset_index == 1:  # nodes
                return np.asarray(neutral_density.values)
        logger.warning("edge_profiles: neutral density values not found for nodes grid_subset")
        return None

    def get_neutral_density_on_cells(self, time_slice):
        """
        Return neutral density values.
        cell-centred values (``grid_subset_index == 5``), falls back to node values.
        """
        for nd in self.ids.ggd[time_slice].neutral[0].density:
            if nd.grid_subset_index == 5:
                return np.asarray(nd.values)
        return self.get_neutral_density_on_nodes(time_slice)

    def get_rz_and_ne_on_subset(self, time_slice, subset_identifier_index):
        """
        Return R, Z coordinates and electron density for every element in a named GGD grid subset.

        For 0-D elements (nodes) the node geometry is used directly.  For higher-dimension
        elements (edges, faces, cells) the centroid of the element's nodes is used.

        Args:
            time_slice: time index
            subset_identifier_index: GGD ``identifier.index`` of the target subset,
                e.g. 11 = outer midplane, 13 = inner divertor target, 14 = outer divertor target.

        Returns:
            ``(r, z, ne)`` numpy float arrays in grid-subset element order,
            or ``(None, None, None)`` when the subset or its density data is unavailable.
        """
        subset_array_index = None
        for iset, gs in enumerate(self.ids.grid_ggd[time_slice].grid_subset):
            if gs.identifier.index == subset_identifier_index:
                subset_array_index = iset
                break

        if subset_array_index is None:
            logger.warning(f"edge_profiles: grid subset with identifier.index={subset_identifier_index} not found")
            return None, None, None

        grid_subset = self.ids.grid_ggd[time_slice].grid_subset[subset_array_index]
        if len(grid_subset.element) == 0:
            logger.warning(f"edge_profiles: grid subset {subset_identifier_index} has no elements")
            return None, None, None

        # grid_subset_index in ggd arrays stores identifier.index (semantic index), not array position
        ne_entry = None
        ne_all_nodes = None
        for dens in self.ids.ggd[time_slice].electrons.density:
            if dens.grid_subset_index == subset_identifier_index:
                ne_entry = dens
                break
            if dens.grid_subset_index == 1:  # nodes — keep as fallback
                ne_all_nodes = np.asarray(dens.values, dtype=float)

        spaces = self.ids.grid_ggd[time_slice].space
        r_list, z_list, ne_list = [], [], []

        for element in grid_subset.element:
            for obj in element.object:
                space_idx = obj.space - 1  # space
                dim_idx = obj.dimension - 1  # 0=nodes, 1=edges, 2=faces, 3=cells
                obj_idx = obj.index - 1  # convert to 0-based
                space = spaces[space_idx]
                n_nodes = len(space.objects_per_dimension[0].object)
                ggd_obj = space.objects_per_dimension[dim_idx].object[obj_idx]
                if dim_idx == 0:
                    g = ggd_obj.geometry
                    r_list.append(float(g[0]))
                    z_list.append(float(g[1]))
                    if ne_entry is None and ne_all_nodes is not None:
                        ne_list.append(float(ne_all_nodes[obj_idx]) if obj_idx < n_nodes else np.nan)
                else:
                    nodes = np.asarray(ggd_obj.nodes, dtype=int) - 1  # 0-based node indices
                    valid = nodes[(nodes >= 0) & (nodes < n_nodes)]
                    geom = [space.objects_per_dimension[0].object[n].geometry for n in valid]
                    r_list.append(float(np.mean([g[0] for g in geom])))
                    z_list.append(float(np.mean([g[1] for g in geom])))
                    if ne_entry is None and ne_all_nodes is not None:
                        valid_ne = valid[valid < len(ne_all_nodes)]
                        ne_list.append(float(np.mean(ne_all_nodes[valid_ne])) if len(valid_ne) else np.nan)

        r = np.array(r_list, dtype=float)
        z = np.array(z_list, dtype=float)

        if ne_entry is not None:
            ne_values = np.asarray(ne_entry.values, dtype=float)
            if len(ne_values) != len(r):
                logger.warning(
                    f"edge_profiles: per-subset density count {len(ne_values)} != element count {len(r)} "
                    f"for subset {subset_identifier_index}, no node-density fallback collected for this "
                    "subset, returning no data"
                )
                if len(ne_list) == len(r):
                    return r, z, np.array(ne_list, dtype=float)
                return None, None, None
            return r, z, ne_values

        if len(ne_list) == len(r):
            return r, z, np.array(ne_list, dtype=float)

        logger.warning(f"edge_profiles: electron density not found for grid subset {subset_identifier_index}")
        return None, None, None

    def get_outer_midplane_array_index(self, time_slice):
        """
        This function `get_outer_midplane_array_index` searches for a specific grid subset with an
        index of 11 and returns its position within the list of subsets.

        Returns:
            The function `getOuterMidplaneArrayIndex` returns the index of the grid subset that has an identifier
            index of 11, representing the outer midplane GGD grid subset. If the subset is found,
            it returns the index of that subset. If the subset is not found, it logs a warning message and
            returns `None`.
        """
        subset_index = None
        nsubsets = len(self.ids.grid_ggd[time_slice].grid_subset)
        for iset in range(nsubsets):
            if self.ids.grid_ggd[time_slice].grid_subset[iset].identifier.index == 11:
                subset_index = iset
        if subset_index is None:
            logger.warning("Did not find outer_midplane GGD grid subset.")
        else:
            logger.debug(f"Outer midplane GGD grid subset is number {subset_index + 1} of {nsubsets}")
        return subset_index

    def getnrho(self, time_slice):
        """
        This function `getnrho` returns the number of elements in the `rho_tor_norm` or `rho_tor` grid
        based on the provided slice index.

        Args:
            time_slice: The `time_slice` parameter in the `getnrho` method is used to specify which
                slice of the `profiles_1d` data to access.

        Returns:
            The `getnrho` method is returning the number of elements in the `rho_tor_norm` or `rho_tor`
            attribute of the grid object within the `profiles_1d` attribute of the `ids` object at the
            specified `time_slice`. If either of these attributes has elements, the length of that
            attribute is returned as the number of elements (`nrho`).
        """
        nrho = None
        try:
            if len(self.ids.profiles_1d[time_slice].grid.rho_tor_norm) > 0:
                nrho = len(self.ids.profiles_1d[time_slice].grid.rho_tor_norm)
            elif len(self.ids.profiles_1d[time_slice].grid.rho_tor) > 0:
                nrho = len(self.ids.profiles_1d[time_slice].grid.rho_tor)
        except Exception as e:
            logger.debug(f"{e}")
            logger.warning(
                f"edge_profiles.profiles_1d[{time_slice}].grid.rho_tor_norm and rho_tor could not be read. {e}"
            )
        return nrho
