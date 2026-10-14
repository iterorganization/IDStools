"""Fixtures of the create_summary tests.

Tests using the ``factory`` fixture run for every DD version in DD_VERSIONS.
"""

import imas
import numpy as np
import pytest

from idstools.domain import summary as cs
from summary_testing import DD_VERSIONS, FakeContext, add_subset_values, fill_grid, set_element


@pytest.fixture(scope="session", params=DD_VERSIONS)
def factory(request):
    return imas.IDSFactory(request.param)


@pytest.fixture(scope="session")
def factory_dd3():
    return imas.IDSFactory(DD_VERSIONS[0])


@pytest.fixture(scope="session")
def factory_dd4():
    return imas.IDSFactory(DD_VERSIONS[1])


@pytest.fixture
def make_builder(factory):
    def make(time=(1.0, 2.0)):
        return cs.SummaryBuilder(factory.summary(), np.asarray(time, dtype=float))

    return make


@pytest.fixture
def make_ctx(make_builder):
    def make(ids=None, time=(1.0, 2.0)):
        return FakeContext(make_builder(time), ids)

    return make


@pytest.fixture
def edge_profiles(factory):
    """edge_profiles with one GGD time slice at t=1.5 s on the test grid."""
    ep = factory.edge_profiles()
    ep.ids_properties.homogeneous_time = 1
    ep.time = np.array([1.5])
    ep.grid_ggd.resize(1)
    fill_grid(ep.grid_ggd[0])
    ep.ggd.resize(1)
    ggd = ep.ggd[0]
    ggd.time = 1.5
    add_subset_values(ggd.electrons.temperature, {101: 100.0, 103: 10.0, 104: 20.0})
    add_subset_values(ggd.electrons.density, {101: 3e19, 103: 1e20, 104: 2e20})
    add_subset_values(ggd.t_i_average, {101: 120.0, 103: 12.0, 104: 22.0})
    add_subset_values(ggd.zeff, {101: 1.5, 103: 1.6, 104: 1.7})
    ggd.ion.resize(2)
    set_element(ggd.ion[0].element, 1, 2.0)  # D+
    ggd.ion[0].name = "D"
    add_subset_values(ggd.ion[0].density, {101: 2.8e19, 103: 9e19, 104: 1.8e20})
    set_element(ggd.ion[1].element, 1, 2.0, atoms_n=2)  # D2+ molecular ion
    ggd.ion[1].name = "D2+"
    add_subset_values(ggd.ion[1].density, {101: 1e17, 103: 1e18, 104: 2e18})
    return ep


@pytest.fixture
def radiation(factory):
    """radiation with emissivities on the cells, grid referenced by path."""
    rad = factory.radiation()
    rad.ids_properties.homogeneous_time = 1
    rad.time = np.array([1.5])
    rad.grid_ggd.resize(1)
    rad.grid_ggd[0].path = "#edge_profiles/grid_ggd(1)"
    rad.process.resize(2)
    for process, emissivity in zip(rad.process, ([2.0, 3.0], [1.0, 1.0]), strict=True):
        process.ggd.resize(1)
        process.ggd[0].time = 1.5
        process.ggd[0].ion.resize(1)
        set_element(process.ggd[0].ion[0].element, 1, 2.0)
        add_subset_values(process.ggd[0].ion[0].emissivity, {5: emissivity})
    return rad
