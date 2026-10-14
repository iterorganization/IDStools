"""Tests of the generic helpers."""

import imas
import numpy as np
import pytest

from idstools.domain import summary as cs
from summary_testing import set_element


@pytest.fixture
def equilibrium(factory):
    eq = factory.equilibrium()
    eq.ids_properties.homogeneous_time = 1
    eq.time = np.array([0.0, 1.0])
    eq.time_slice.resize(2)
    eq.time_slice[0].global_quantities.ip = -1e6
    eq.time_slice[1].global_quantities.ip = -2e6
    eq.time_slice[0].global_quantities.q_95 = imas.ids_defs.EMPTY_FLOAT
    eq.time_slice[1].profiles_1d.psi = np.array([1.0, imas.ids_defs.EMPTY_FLOAT])
    return eq


class TestGetNode:
    def test_nested_path_with_index(self, equilibrium):
        node = cs.get_node(equilibrium, "time_slice[1]/global_quantities/ip")
        assert node.value == -2e6

    def test_missing_attribute(self, equilibrium):
        assert cs.get_node(equilibrium, "time_slice[0]/not_a_node") is None

    def test_index_out_of_range(self, equilibrium):
        assert cs.get_node(equilibrium, "time_slice[5]/global_quantities") is None


class TestGetValue:
    def test_filled_value(self, equilibrium):
        assert cs.get_value(equilibrium.time_slice[0], "global_quantities/ip") == -1e6

    def test_unfilled_value(self, equilibrium):
        assert cs.get_value(equilibrium.time_slice[0], "global_quantities/li_3") is None

    def test_empty_float_is_nan(self, equilibrium):
        # an explicitly stored EMPTY_FLOAT counts as not filled
        value = cs.get_value(equilibrium.time_slice[0], "global_quantities/q_95")
        assert value is None or np.isnan(value)

    def test_empty_float_in_array_is_nan(self, equilibrium):
        value = cs.get_value(equilibrium.time_slice[1], "profiles_1d/psi")
        assert value[0] == 1.0 and np.isnan(value[1])

    def test_structure_is_not_a_value(self, equilibrium):
        assert cs.get_value(equilibrium, "time_slice[0]/global_quantities") is None


def test_first_value(equilibrium):
    value, path = cs.first_value(
        equilibrium.time_slice[1],
        ["global_quantities/li_3", "global_quantities/ip"],
    )
    assert (value, path) == (-2e6, "global_quantities/ip")
    assert cs.first_value(equilibrium.time_slice[1], ["global_quantities/li_3"]) == (
        None,
        None,
    )


@pytest.mark.parametrize(
    "value, expected",
    [(None, np.nan), (2, 2.0), (np.array([3.0, 4.0]), 3.0), (np.array([]), np.nan)],
)
def test_as_float(value, expected):
    np.testing.assert_equal(cs.as_float(value), expected)


@pytest.mark.parametrize(
    "z_n, a, atoms_n, expected",
    [
        (1, 1.0, 1, "hydrogen"),
        (1, 2.014, 1, "deuterium"),
        (1, 3.016, 1, "tritium"),
        (1, 2.5, 1, "deuterium_tritium"),
        (2, 3.016, 1, "helium_3"),
        (2, 4.0026, 1, "helium_4"),
        (4, 9.012, 1, "beryllium"),
        (74, 183.84, 1, "tungsten"),
        (1, 2.0, 2, None),  # molecule
        (9, 19.0, 1, None),  # fluorine: no summary node
    ],
)
def test_species_name(factory, z_n, a, atoms_n, expected):
    cp = factory.core_profiles()
    cp.profiles_1d.resize(1)
    cp.profiles_1d[0].ion.resize(1)
    ion = cp.profiles_1d[0].ion[0]
    set_element(ion.element, z_n, a, atoms_n)
    assert cs.species_name(ion.element) == expected


def test_species_name_multiple_elements(factory):
    cp = factory.core_profiles()
    cp.profiles_1d.resize(1)
    cp.profiles_1d[0].ion.resize(1)
    elements = cp.profiles_1d[0].ion[0].element
    elements.resize(2)
    assert cs.species_name(elements) is None


class TestIdsTimes:
    def test_homogeneous(self, equilibrium):
        np.testing.assert_array_equal(cs.ids_times(equilibrium), [0.0, 1.0])

    def test_heterogeneous_uses_aos_times(self, factory):
        eq = factory.equilibrium()
        eq.ids_properties.homogeneous_time = 0
        eq.time_slice.resize(2)
        eq.time_slice[0].time = 3.0
        eq.time_slice[1].time = 4.0
        np.testing.assert_array_equal(cs.ids_times(eq, "time_slice"), [3.0, 4.0])
        assert cs.ids_times(eq) is None

    def test_static(self, factory):
        wall = factory.wall()
        wall.ids_properties.homogeneous_time = 2
        assert cs.ids_times(wall) is None


def test_signal_times(factory):
    nbi = factory.nbi()
    nbi.unit.resize(1)
    signal = nbi.unit[0].power_launched
    signal.time = np.array([5.0, 6.0])
    nbi.time = np.array([1.0, 2.0])
    nbi.ids_properties.homogeneous_time = 1
    np.testing.assert_array_equal(cs.signal_times(nbi, signal), [1.0, 2.0])
    nbi.ids_properties.homogeneous_time = 0
    np.testing.assert_array_equal(cs.signal_times(nbi, signal), [5.0, 6.0])
