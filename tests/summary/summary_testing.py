"""Helpers of the create_summary tests: synthetic IDSs and a minimal filler context."""

import numpy as np

DD_VERSIONS = ["3.42.0", "4.0.0"]


def is_dd3(factory):
    return factory.dd_version.startswith("3.")


class FakeContext:
    """Stand-in for summary.Context, serving IDSs from a dict."""

    def __init__(self, builder, ids=None):
        self.builder = builder
        self.ids = dict(ids or {})
        self.uri = "imas:memory?path=test"

    @property
    def available(self):
        return set(self.ids)

    def get(self, name):
        return self.ids.get(name)


def set_element(element_aos, z_n, a, atoms_n=1):
    element_aos.resize(1)
    element_aos[0].z_n = z_n
    element_aos[0].a = a
    element_aos[0].atoms_n = atoms_n


# --------------------------------------------------------------------------
# A small GGD grid
#
#   Z=1  4 ---- 5 ---- 6        nodes 1..6, cells 1 (core) and 2 (SOL)
#        | c1   | c2   |        cell areas 1 m2, cell centres R=1.5, R=2.5
#   Z=0  1 ---- 2 ---- 3
#       R=1    R=2    R=3
#
# subsets: 1 nodes, 5 cells, 6 x-point (node 1), 22 core (cell 1),
# 23 SOL (cell 2), 101 outer midplane separatrix (node 5), 103 outer
# target separatrix (node 3), 104 inner target separatrix (node 6)
# --------------------------------------------------------------------------
NODES = [(1.0, 0.0), (2.0, 0.0), (3.0, 0.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]


CELLS = [[1, 2, 5, 4], [2, 3, 6, 5]]


SUBSETS = {
    1: (1, [1, 2, 3, 4, 5, 6]),
    5: (3, [1, 2]),
    6: (1, [1]),
    22: (3, [1]),
    23: (3, [2]),
    101: (1, [5]),
    103: (1, [3]),
    104: (1, [6]),
}


# volumes of the cells (area * 2 pi R_centre)
CELL_VOLUMES = 2 * np.pi * np.array([1.5, 2.5])


def fill_grid(grid, name="SN", index=4):
    grid.identifier.name = name
    grid.identifier.index = index
    grid.space.resize(1)
    space = grid.space[0]
    space.objects_per_dimension.resize(3)
    nodes = space.objects_per_dimension[0].object
    nodes.resize(len(NODES))
    for obj, (r, z) in zip(nodes, NODES, strict=True):
        obj.geometry = np.array([r, z])
    cells = space.objects_per_dimension[2].object
    cells.resize(len(CELLS))
    for obj, cell_nodes in zip(cells, CELLS, strict=True):
        obj.nodes = np.array(cell_nodes, dtype=np.int32)
        obj.measure = 1.0
    grid.grid_subset.resize(len(SUBSETS))
    for subset, (index_, (dimension, objects)) in zip(grid.grid_subset, SUBSETS.items(), strict=True):
        subset.identifier.index = index_
        subset.dimension = dimension
        subset.element.resize(len(objects))
        for element, obj_index in zip(subset.element, objects, strict=True):
            element.object.resize(1)
            element.object[0].space = 1
            element.object[0].dimension = dimension
            element.object[0].index = obj_index


def add_subset_values(aos, values_by_subset):
    aos.resize(len(values_by_subset))
    for item, (subset, values) in zip(aos, values_by_subset.items(), strict=True):
        item.grid_index = 1
        item.grid_subset_index = subset
        item.values = np.atleast_1d(np.asarray(values, dtype=float))


# --------------------------------------------------------------------------
# core_profiles
# --------------------------------------------------------------------------
V_TOTAL = 800.0


T_AXIS = 1000.0


def make_core_profiles(factory, rho=(0.0, 0.5, 1.0)):
    """t_e = T_AXIS (1 - rho^2) and volume = V_TOTAL rho^2: <t_e> = T_AXIS / 2."""
    rho = np.asarray(rho)
    cp = factory.core_profiles()
    cp.ids_properties.homogeneous_time = 1
    cp.time = np.array([1.0, 2.0])
    cp.global_quantities.ip = np.array([-1e6, -2e6])
    cp.global_quantities.v_loop = np.array([0.1, 0.2])
    cp.profiles_1d.resize(2)
    for profile, t in zip(cp.profiles_1d, cp.time, strict=True):
        profile.time = t
        profile.grid.rho_tor_norm = rho
        profile.grid.volume = V_TOTAL * rho**2
        profile.electrons.temperature = T_AXIS * (1 - rho**2)
        profile.electrons.density = np.full(rho.size, 1e20)
        profile.zeff = np.full(rho.size, 1.5)
        profile.ion.resize(3)
        for ion, (z_n, a, atoms_n), density in zip(
            profile.ion,
            ((1, 2.014, 1), (74, 183.84, 1), (1, 1.0, 2)),
            (9e19, 1e17, 1e15),
            strict=True,
        ):
            set_element(ion.element, z_n, a, atoms_n)
            ion.density = np.full(rho.size, density)
    return cp
