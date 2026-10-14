"""Tests of the fillers on synthetic IDSs."""

import imas
import numpy as np
import pytest

from idstools.domain import summary as cs
from summary_testing import (
    CELL_VOLUMES,
    T_AXIS,
    V_TOTAL,
    FakeContext,
    fill_grid,
    is_dd3,
    make_core_profiles,
    set_element,
)


# --------------------------------------------------------------------------
# equilibrium and vacuum field
# --------------------------------------------------------------------------
@pytest.fixture
def equilibrium(factory):
    eq = factory.equilibrium()
    eq.ids_properties.homogeneous_time = 1
    eq.time = np.array([0.0, 2.0])
    eq.vacuum_toroidal_field.r0 = 6.2
    eq.vacuum_toroidal_field.b0 = np.array([-5.3, -5.3])
    eq.time_slice.resize(2)
    for ts, ip, q95, kind in zip(eq.time_slice, (-1e6, -3e6), (5.0, 3.0), (0, 1), strict=True):
        ts.global_quantities.ip = ip
        ts.global_quantities.q_95 = q95
        ts.global_quantities.magnetic_axis.r = 6.4
        ts.global_quantities.magnetic_axis.z = 0.5
        ts.boundary.type = kind
        ts.boundary.minor_radius = 2.0
        ts.boundary.triangularity = 0.4
        ts.boundary.triangularity_upper = 0.5
    return eq


def test_fill_equilibrium(make_ctx, equilibrium):
    ctx = make_ctx({"equilibrium": equilibrium}, time=[1.0, 2.0])
    cs.fill_equilibrium(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/ip"), [-2e6, -3e6])
    np.testing.assert_allclose(b.get("global_quantities/q_95"), [4.0, 3.0])
    np.testing.assert_allclose(b.get("local/magnetic_axis/position/r"), [6.4, 6.4])
    np.testing.assert_allclose(b.get("boundary/magnetic_axis_z"), [0.5, 0.5])
    np.testing.assert_allclose(b.get("boundary/triangularity_upper"), [0.5, 0.5])
    # boundary type is interpolated with nearest neighbour
    np.testing.assert_array_equal(b.get("boundary/type"), [1, 1])
    assert b.filled["global_quantities/ip"] == ("equilibrium/time_slice/global_quantities/ip")
    # the average triangularity is not a substitute for the lower one
    assert not b.has("boundary/triangularity_lower")


def test_fill_equilibrium_outside_time_range(make_ctx, equilibrium):
    ctx = make_ctx({"equilibrium": equilibrium}, time=[1.0, 3.0])
    cs.fill_equilibrium(ctx)
    assert not ctx.builder.filled


def test_fill_vacuum_field(make_ctx, equilibrium):
    ctx = make_ctx({"equilibrium": equilibrium})
    cs.fill_vacuum_field(ctx)
    assert ctx.builder.get("global_quantities/r0") == 6.2
    np.testing.assert_allclose(ctx.builder.get("global_quantities/b0"), [-5.3, -5.3])


def test_fill_core_profiles(make_ctx, factory):
    ctx = make_ctx({"core_profiles": make_core_profiles(factory)})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/v_loop"), [0.1, 0.2])
    np.testing.assert_allclose(b.get("volume_average/t_e"), [T_AXIS / 2] * 2)
    np.testing.assert_allclose(b.get("local/magnetic_axis/t_e"), [T_AXIS] * 2)
    np.testing.assert_allclose(b.get("local/separatrix/t_e"), [0.0] * 2)
    np.testing.assert_allclose(b.get("volume_average/n_i/deuterium"), [9e19] * 2)
    np.testing.assert_allclose(b.get("volume_average/n_i/tungsten"), [1e17] * 2)
    # n_i_total is the sum over all ion species, including molecular ions
    np.testing.assert_allclose(b.get("volume_average/n_i_total"), [9e19 + 1e17 + 1e15] * 2)
    assert "volume average" in b.filled["volume_average/t_e"]
    # no line averages (they need the chord geometry)
    assert not any(path.startswith("line_average") for path in b.filled)


def test_fill_core_profiles_partial_grid(make_ctx, factory):
    cp = make_core_profiles(factory, rho=(0.05, 0.5, 0.98))
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    filled = ctx.builder.filled
    assert not any(p.startswith(("local/", "volume_average")) for p in filled)


@pytest.mark.parametrize(
    "rho, expected",
    [
        ((0.0, 0.5, 1.0), {"magnetic_axis", "separatrix", "volume_average"}),
        ((0.007, 0.5, 1.0), {"magnetic_axis", "separatrix", "volume_average"}),
        ((0.02, 0.5, 1.0), {"separatrix", "volume_average"}),
        ((0.05, 0.5, 1.0), {"separatrix"}),
        ((0.0, 0.5, 0.995), {"magnetic_axis"}),
    ],
)
def test_profile_reductions_tolerances(factory, rho, expected):
    cp = factory.core_profiles()
    cp.profiles_1d.resize(1)
    profile = cp.profiles_1d[0]
    rho = np.asarray(rho)
    profile.grid.rho_tor_norm = rho
    profile.grid.volume = V_TOTAL * rho**2
    reductions = set(cs.profile_reductions(profile))
    # the volume integral is available exactly when the volume average is
    assert ("volume_integral" in reductions) == ("volume_average" in reductions)
    assert reductions - {"volume_integral"} == expected


# --------------------------------------------------------------------------
# core_sources
# --------------------------------------------------------------------------
def test_fill_core_sources(make_ctx, factory):
    src = factory.core_sources()
    src.ids_properties.homogeneous_time = 1
    src.time = np.array([1.0, 2.0])
    src.source.resize(4)
    # EC, named and identified by index only: summed
    src.source[0].identifier.name = "ec"
    src.source[0].identifier.index = 3
    src.source[1].identifier.index = 3
    # radiation sinks are negative in core_sources
    src.source[2].identifier.name = "bremsstrahlung"
    for source, power in zip(
        [src.source[i] for i in range(3)],
        ([1e6, 2e6], [1e6, 1e6], [-5e5, -5e5]),
        strict=True,
    ):
        source.global_quantities.resize(2)
        for gq, p in zip(source.global_quantities, power, strict=True):
            gq.power = p
    # NBI: no global quantities, volume integrals of the profiles instead
    nbi = src.source[3]
    nbi.identifier.name = "nbi"
    nbi.profiles_1d.resize(2)
    for profile in nbi.profiles_1d:
        profile.electrons.power_inside = np.array([0.0, 1e6])
        profile.total_ion_power_inside = np.array([0.0, 2e6])

    ctx = make_ctx({"core_sources": src})
    cs.fill_core_sources(ctx)
    cs.fill_derived(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("heating_current_drive/power_ec"), [2e6, 3e6])
    assert b.filled["heating_current_drive/power_ec"].startswith("core_sources/source[0]+source[1]/")
    np.testing.assert_allclose(b.get("global_quantities/power_bremsstrahlung"), [5e5] * 2)
    np.testing.assert_allclose(b.get("heating_current_drive/power_nbi"), [3e6] * 2)
    np.testing.assert_allclose(b.get("heating_current_drive/power_additional"), [5e6, 6e6])


# --------------------------------------------------------------------------
# H&CD launchers
# --------------------------------------------------------------------------
def test_fill_launchers(make_ctx, factory):
    nbi = factory.nbi()
    nbi.ids_properties.homogeneous_time = 1
    nbi.time = np.array([1.0, 2.0])
    nbi.unit.resize(2)
    for unit in nbi.unit:
        unit.power_launched.data = np.array([1e6, 2e6])
        unit.energy.data = np.array([1e6, 1e6])
        unit.species.a = 2.014
        unit.species.z_n = 1.0
        if is_dd3(factory):
            unit.species.label = "D"
        else:
            unit.species.name = "D"
    ec = factory.ec_launchers()
    ec.ids_properties.homogeneous_time = 0
    ec.beam.resize(1)
    ec.beam[0].power_launched.time = np.array([0.0, 3.0])
    ec.beam[0].power_launched.data = np.array([0.0, 3e6])

    ctx = make_ctx({"nbi": nbi, "ec_launchers": ec})
    cs.fill_launchers(ctx)
    cs.fill_derived(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("heating_current_drive/power_launched_nbi"), [2e6, 4e6])
    np.testing.assert_allclose(b.get("heating_current_drive/nbi[1]/energy"), [1e6] * 2)
    label = "label" if is_dd3(factory) else "name"
    assert b.get(f"heating_current_drive/nbi[0]/species/{label}") == "D"
    np.testing.assert_allclose(b.get("heating_current_drive/ec[0]/power_launched"), [1e6, 2e6])
    np.testing.assert_allclose(b.get("heating_current_drive/power_launched_ec"), [1e6, 2e6])
    # the additional power is the coupled power: not derived from launched power
    assert not b.has("heating_current_drive/power_additional")


# --------------------------------------------------------------------------
# GGD: edge profiles and radiation
# --------------------------------------------------------------------------
def test_ggd_grid(edge_profiles):
    grid = cs.GGDGrid(edge_profiles.grid_ggd[0])
    dimension, indices = grid.subset_objects(22)
    assert dimension == 3 and list(indices) == [0]
    np.testing.assert_allclose(grid.object_position(1, 4), [2.0, 1.0])
    np.testing.assert_allclose(grid.object_position(3, 1), [2.5, 0.5])
    cells, volumes = grid.cell_volumes()
    assert list(cells) == [0, 1]
    np.testing.assert_allclose(volumes, CELL_VOLUMES)
    assert grid.subset_objects(999) == (None, None)


@pytest.mark.parametrize(
    "name, expected",
    [("limiter", 0), ("SN", 11), ("CDN", 13), ("DDN_top", 13), ("linear", None)],
)
def test_boundary_type(factory, name, expected):
    ep = factory.edge_profiles()
    ep.grid_ggd.resize(1)
    fill_grid(ep.grid_ggd[0], name=name)
    assert cs.GGDGrid(ep.grid_ggd[0]).boundary_type() == expected


def test_fill_edge_profiles(make_ctx, edge_profiles):
    ctx = make_ctx({"edge_profiles": edge_profiles}, time=[1.5])
    cs.fill_edge_profiles(ctx, "edge_profiles")
    b = ctx.builder
    assert b.get("local/separatrix/t_e") == [100.0]
    assert b.get("local/separatrix/t_i_average") == [120.0]
    assert b.get("local/divertor_target[0]/t_e") == [20.0]  # inner: subset 104
    assert b.get("local/divertor_target[1]/n_e") == [1e20]  # outer: subset 103
    assert b.get("local/divertor_target[0]/name") == "inner target separatrix"
    np.testing.assert_allclose(b.get("local/separatrix/n_i/deuterium"), [2.8e19])
    np.testing.assert_allclose(b.get("local/separatrix/n_i_total"), [2.8e19 + 1e17])
    assert b.get("boundary/strike_point_inner_r") == [3.0]
    assert b.get("boundary/strike_point_inner_z") == [1.0]
    assert b.get("boundary/strike_point_outer_z") == [0.0]
    assert b.get("configuration") == "SN"
    assert b.get("boundary/type") == [11]
    assert "grid subset 101" in b.filled["local/separatrix/t_e"]
    assert not b.has("local/separatrix_average/t_e")


@pytest.mark.parametrize("previous, expected", [(1, 11), (0, 0)])
def test_edge_boundary_type_refines_diverted(make_ctx, edge_profiles, previous, expected):
    ctx = make_ctx({"edge_profiles": edge_profiles}, time=[1.5])
    ctx.builder.set("boundary/type", previous, "equilibrium")
    cs.fill_edge_profiles(ctx, "edge_profiles")
    assert ctx.builder.get("boundary/type") == [expected]


def test_fill_radiation(make_ctx, edge_profiles, radiation):
    ctx = make_ctx({"edge_profiles": edge_profiles, "radiation": radiation}, [1.5])
    cs.fill_radiation(ctx)
    b = ctx.builder
    # emissivities summed over the processes: 3 W/m3 (core cell), 4 W/m3 (SOL)
    sol_power = 4.0 * CELL_VOLUMES[1]
    np.testing.assert_allclose(b.get("global_quantities/power_radiated_outside_lcfs"), [sol_power])
    np.testing.assert_allclose(b.get("scrape_off_layer/power_radiated"), [sol_power])


def test_resolve_grid_missing_reference(make_ctx, radiation):
    ctx = make_ctx({"radiation": radiation}, [1.5])
    assert cs.resolve_grid(ctx, radiation) is None
    cs.fill_radiation(ctx)
    assert not ctx.builder.filled


# --------------------------------------------------------------------------
# gas injection, metadata
# --------------------------------------------------------------------------
def test_fill_gas_injection(make_ctx, factory):
    gas = factory.gas_injection()
    gas.ids_properties.homogeneous_time = 1
    gas.time = np.array([1.0, 2.0])
    gas.pipe.resize(2)
    for pipe, rate, (z_n, a) in zip(gas.pipe, ([1e20, 2e20], [1e19, 1e19]), ((1, 2.014), (10, 20.18)), strict=True):
        pipe.flow_rate.data = np.array(rate)
        pipe.species.resize(1)
        set_element(pipe.species[0].element, z_n, a)
    ctx = make_ctx({"gas_injection": gas})
    cs.fill_gas_injection(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("gas_injection_rates/total"), [1.1e20, 2.1e20])
    np.testing.assert_allclose(b.get("gas_injection_rates/deuterium"), [1e20, 2e20])
    np.testing.assert_allclose(b.get("gas_injection_rates/neon"), [1e19, 1e19])


# --------------------------------------------------------------------------
# magnetics
# --------------------------------------------------------------------------
def make_magnetics(factory, homogeneous):
    mag = factory.magnetics()
    mag.ids_properties.homogeneous_time = homogeneous
    mag.ip.resize(2)
    mag.ip[0].data = np.array([-1e6, -2e6, -3e6])
    mag.ip[1].data = np.array([-9e6, -9e6, -9e6])
    if homogeneous:
        mag.time = np.array([0.0, 1.0, 2.0])
    else:
        mag.ip[0].time = np.array([0.0, 1.0, 2.0])
        mag.ip[1].time = np.array([0.0, 1.0, 2.0])
    return mag


@pytest.mark.parametrize("homogeneous", [1, 0])
def test_fill_magnetics(make_ctx, factory, homogeneous):
    ctx = make_ctx({"magnetics": make_magnetics(factory, homogeneous)})
    cs.fill_magnetics(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/ip"), [-2e6, -3e6])
    assert b.filled["global_quantities/ip"] == "magnetics/ip[0]"


def test_fill_magnetics_is_last_fallback(make_ctx, factory, equilibrium):
    ctx = make_ctx(
        {"equilibrium": equilibrium, "magnetics": make_magnetics(factory, 1)},
        time=[1.0, 2.0],
    )
    cs.fill_equilibrium(ctx)
    cs.fill_magnetics(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/ip"), [-2e6, -3e6])
    assert b.filled["global_quantities/ip"] == ("equilibrium/time_slice/global_quantities/ip")


def test_fill_magnetics_empty(make_ctx, factory):
    mag = factory.magnetics()
    mag.ids_properties.homogeneous_time = 1
    ctx = make_ctx({"magnetics": mag})
    cs.fill_magnetics(ctx)
    assert not ctx.builder.filled


def test_fill_metadata(make_ctx, factory, edge_profiles):
    cp = make_core_profiles(factory)
    cp.code.name = "ASTRA"
    cp.code.version = "6.2"
    cp.code.library.resize(1)
    cp.code.library[0].name = "lib"
    edge_profiles.midplane.name = "magnetic_axis"
    edge_profiles.midplane.index = 1
    ctx = make_ctx({"core_profiles": cp, "edge_profiles": edge_profiles})
    cs.fill_metadata(ctx, "core_profiles")
    summary = ctx.builder.ids
    assert summary.ids_properties.homogeneous_time == 1
    assert summary.code.name == "ASTRA" and summary.code.version == "6.2"
    assert summary.code.library[0].name == "lib"
    assert summary.midplane.index == 1


def test_fill_metadata_dataset_description_dd41(factory_dd4):
    """In DD >= 4.1 the summary holds the data entry description."""
    dataset = factory_dd4.dataset_description()
    dataset.machine = "ITER"
    dataset.pulse = 106553
    dataset.simulation.workflow = "SOLPS-ITER"
    builder = cs.SummaryBuilder(imas.IDSFactory("4.1.1").summary(), [1.0])
    ctx = FakeContext(builder, {"dataset_description": dataset})
    cs.fill_metadata(ctx, "core_profiles")
    assert builder.ids.machine == "ITER"
    assert builder.ids.pulse == 106553
    assert builder.ids.simulation.workflow == "SOLPS-ITER"


def test_fill_metadata_dataset_description_not_in_summary(make_ctx, factory):
    """The DD 3 and DD 4.0 summaries have no machine/pulse nodes: skipped."""
    dataset = factory.dataset_description()
    if is_dd3(factory):
        dataset.data_entry.machine = "ITER"
    else:
        dataset.machine = "ITER"
    ctx = make_ctx({"dataset_description": dataset})
    cs.fill_metadata(ctx, "core_profiles")
    assert not any(path == "machine" for path in ctx.builder.filled)


# --------------------------------------------------------------------------
# quantities renamed between DD 3 and DD 4
# --------------------------------------------------------------------------
def test_li_names(make_ctx, factory, equilibrium):
    """li_3/li_3_mhd in the DD4 summary are li/li_mhd in DD3."""
    for ts in equilibrium.time_slice:
        ts.global_quantities.li_3 = 0.8
    cp = make_core_profiles(factory)
    cp.global_quantities.li_3 = np.array([0.7, 0.7])
    ctx = make_ctx({"equilibrium": equilibrium, "core_profiles": cp})
    cs.fill_equilibrium(ctx)
    cs.fill_core_profiles(ctx)
    li, li_mhd = ("li", "li_mhd") if is_dd3(factory) else ("li_3", "li_3_mhd")
    np.testing.assert_allclose(ctx.builder.get(f"global_quantities/{li}"), [0.7] * 2)
    np.testing.assert_allclose(ctx.builder.get(f"global_quantities/{li_mhd}"), [0.8] * 2)


def test_beta_normal_dd3(make_ctx, factory_dd3):
    """beta_normal (DD3 equilibrium) is beta_tor_norm in DD4."""
    eq = factory_dd3.equilibrium()
    eq.ids_properties.homogeneous_time = 1
    eq.time = np.array([1.0, 2.0])
    eq.time_slice.resize(2)
    for ts in eq.time_slice:
        ts.global_quantities.beta_normal = 1.8
    builder = cs.SummaryBuilder(factory_dd3.summary(), [1.0, 2.0])
    cs.fill_equilibrium(FakeContext(builder, {"equilibrium": eq}))
    np.testing.assert_allclose(builder.get("global_quantities/beta_tor_norm_mhd"), [1.8, 1.8])
    assert "beta_normal" in builder.filled["global_quantities/beta_tor_norm_mhd"]


def test_magnetic_axis_field_not_mapped_in_dd3(make_ctx, factory_dd3):
    """The DD3 summary only has an unspecified "b_field" on axis: left empty."""
    eq = factory_dd3.equilibrium()
    eq.ids_properties.homogeneous_time = 1
    eq.time = np.array([1.0, 2.0])
    eq.time_slice.resize(2)
    for ts in eq.time_slice:
        ts.global_quantities.magnetic_axis.b_field_tor = -5.6
    builder = cs.SummaryBuilder(factory_dd3.summary(), [1.0, 2.0])
    cs.fill_equilibrium(FakeContext(builder, {"equilibrium": eq}))
    assert not any("b_field" in path for path in builder.filled)


def test_static_launcher_frequency(make_ctx, factory):
    """The LH antenna frequency is a static value, constant in time."""
    lh = factory.lh_antennas()
    lh.ids_properties.homogeneous_time = 1
    lh.time = np.array([1.0, 2.0])
    lh.antenna.resize(1)
    lh.antenna[0].frequency = 5e9
    lh.antenna[0].power_launched.data = np.array([1e6, 2e6])
    ctx = make_ctx({"lh_antennas": lh})
    cs.fill_launchers(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("heating_current_drive/lh[0]/frequency"), [5e9] * 2)
    np.testing.assert_allclose(b.get("heating_current_drive/power_launched_lh"), [1e6, 2e6])
