"""Tests of the energy, power balance and confinement quantities."""

import numpy as np
import pytest

from idstools.domain import summary as cs
from summary_testing import T_AXIS, V_TOTAL, make_core_profiles, set_element

E = cs.ELEMENTARY_CHARGE
# integral of T_AXIS (1 - rho^2) over the volume V_TOTAL rho^2: the
# trapezoidal rule on rho = (0, 0.5, 1) gives the exact value
T_E_VOLUME_INTEGRAL = T_AXIS * V_TOTAL / 2


# --------------------------------------------------------------------------
# core_profiles: energies, composition, ohmic current, line averages
# --------------------------------------------------------------------------
def test_core_profiles_energies(make_ctx, factory):
    cp = make_core_profiles(factory)
    cp.global_quantities.current_non_inductive = np.array([-0.5e6, -0.5e6])
    for profile in cp.profiles_1d:
        profile.t_i_average = profile.electrons.temperature
        profile.pressure_parallel = np.full(3, 1e5)
        profile.pressure_perpendicular = np.full(3, 2e5)
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    b = ctx.builder

    w_e = 1.5 * E * 1e20 * T_E_VOLUME_INTEGRAL
    w_i = 1.5 * E * (9e19 + 1e17 + 1e15) * T_E_VOLUME_INTEGRAL
    np.testing.assert_allclose(b.get("global_quantities/energy_electrons_thermal"), [w_e] * 2)
    np.testing.assert_allclose(b.get("global_quantities/energy_ion_total_thermal"), [w_i] * 2)
    np.testing.assert_allclose(b.get("global_quantities/energy_thermal"), [w_e + w_i] * 2)
    # (p_par / 2 + p_perp) * volume
    np.testing.assert_allclose(b.get("global_quantities/energy_total"), [2e8] * 2)
    assert b.filled["global_quantities/energy_electrons_thermal"] == (
        "core_profiles/profiles_1d/electrons/(density*temperature) " "(3/2 volume integral)"
    )
    np.testing.assert_allclose(b.get("global_quantities/current_ohm"), [-0.5e6, -1.5e6])


def test_core_profiles_pressures_preferred(make_ctx, factory):
    cp = make_core_profiles(factory)
    for profile in cp.profiles_1d:
        profile.pressure_thermal = np.full(3, 1e5)
        profile.electrons.pressure_thermal = np.full(3, 4e4)
        profile.pressure_ion_total = np.full(3, 6e4)
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/energy_thermal"), [1.2e8] * 2)
    np.testing.assert_allclose(b.get("global_quantities/energy_electrons_thermal"), [4.8e7] * 2)
    np.testing.assert_allclose(b.get("global_quantities/energy_ion_total_thermal"), [7.2e7] * 2)
    # the total is the sum of the components, pressure_thermal only checks it
    assert b.filled["global_quantities/energy_thermal"] == (
        "core_profiles/profiles_1d/(electrons/pressure_thermal+pressure_ion_total) (3/2 volume integral)"
    )
    # no fast particle pressures: no total energy
    assert not b.has("global_quantities/energy_total")


@pytest.mark.parametrize("p_total, warned", [(1.005e5, False), (13.3, True)])
def test_core_profiles_inconsistent_pressure_thermal(make_ctx, factory, caplog, p_total, warned):
    """A pressure_thermal inconsistent with the electron + ion pressures is
    reported, and the thermal energy stays the sum of its components."""
    cp = make_core_profiles(factory)
    for profile in cp.profiles_1d:
        profile.pressure_thermal = np.full(3, p_total)
        profile.electrons.pressure_thermal = np.full(3, 4e4)
        profile.pressure_ion_total = np.full(3, 6e4)
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    np.testing.assert_allclose(ctx.builder.get("global_quantities/energy_thermal"), [1.2e8] * 2)
    messages = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert any("pressure_thermal disagrees" in m and "at 2 of 2 time(s)" in m for m in messages) == warned


def test_core_profiles_pressure_thermal_only(make_ctx, factory, caplog):
    """pressure_thermal is used when the ion pressure is missing."""
    cp = make_core_profiles(factory)  # no ion temperature
    for profile in cp.profiles_1d:
        profile.pressure_thermal = np.full(3, 1e5)
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/energy_thermal"), [1.2e8] * 2)
    assert b.filled["global_quantities/energy_thermal"].startswith("core_profiles/profiles_1d/pressure_thermal ")
    assert not b.has("global_quantities/energy_ion_total_thermal")
    assert "disagrees" not in caplog.text


def test_core_profiles_no_ion_temperature(make_ctx, factory):
    ctx = make_ctx({"core_profiles": make_core_profiles(factory)})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    assert b.has("global_quantities/energy_electrons_thermal")
    assert not b.has("global_quantities/energy_ion_total_thermal")
    assert not b.has("global_quantities/energy_thermal")


def test_core_profiles_hydrogenic_mass(make_ctx, factory):
    cp = make_core_profiles(factory)
    for profile in cp.profiles_1d:
        # third ion: H atoms instead of H2 molecules
        set_element(profile.ion[2].element, 1, 1.0)
    ctx = make_ctx({"core_profiles": cp})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    # tungsten is not hydrogenic
    np.testing.assert_allclose(
        b.get("volume_average/meff_hydrogenic"),
        [(2.014 * 9e19 + 1e15) / (9e19 + 1e15)] * 2,
    )
    np.testing.assert_allclose(b.get("volume_average/isotope_fraction_hydrogen"), [1e15 / (9e19 + 1e15)] * 2)


@pytest.fixture
def chord_equilibrium(factory):
    """R_out - R_in = 4 rho at t=0 and 2 rho at t=3 (linear in rho)."""
    eq = factory.equilibrium()
    eq.ids_properties.homogeneous_time = 1
    eq.time = np.array([0.0, 3.0])
    eq.time_slice.resize(2)
    rho = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    for ts, half_width in zip(eq.time_slice, (2.0, 1.0), strict=True):
        ts.profiles_1d.rho_tor_norm = rho
        ts.profiles_1d.r_inboard = 6.0 - half_width * rho
        ts.profiles_1d.r_outboard = 6.0 + half_width * rho
    return eq


def test_chord_width(chord_equilibrium):
    rho = np.array([0.0, 0.5, 1.0])
    times = cs.ids_times(chord_equilibrium, "time_slice")
    np.testing.assert_allclose(cs.chord_width(chord_equilibrium, times, 0.0, rho, 1e-6), 4 * rho)
    # linear interpolation in time
    np.testing.assert_allclose(cs.chord_width(chord_equilibrium, times, 1.0, rho, 1e-6), 10 / 3 * rho)
    assert cs.chord_width(chord_equilibrium, times, 3.5, rho, 1e-6) is None


def test_core_profiles_line_average(make_ctx, factory, chord_equilibrium):
    cp = make_core_profiles(factory)
    ctx = make_ctx({"core_profiles": cp, "equilibrium": chord_equilibrium})
    cs.fill_core_profiles(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("line_average/n_e"), [1e20] * 2)
    # uniform weight in rho: trapezoidal mean of (1000, 750, 0) = 625
    np.testing.assert_allclose(b.get("line_average/t_e"), [625.0] * 2)
    np.testing.assert_allclose(b.get("line_average/n_i/deuterium"), [9e19] * 2)
    assert "r_inboard" in b.filled["line_average/n_e"]


def test_core_profiles_line_average_needs_whole_chord(make_ctx, factory, chord_equilibrium):
    for ts in chord_equilibrium.time_slice:
        ts.profiles_1d.rho_tor_norm = np.array([0.0, 0.25, 0.5, 0.75, 0.9])
    ctx = make_ctx({"core_profiles": make_core_profiles(factory), "equilibrium": chord_equilibrium})
    cs.fill_core_profiles(ctx)
    assert not any(p.startswith("line_average") for p in ctx.builder.filled)


# --------------------------------------------------------------------------
# core_sources fusion power, waves, single launchers
# --------------------------------------------------------------------------
def test_fusion_power(make_ctx, factory):
    src = factory.core_sources()
    src.ids_properties.homogeneous_time = 1
    src.time = np.array([1.0, 2.0])
    src.source.resize(1)
    src.source[0].identifier.index = 6  # fusion
    src.source[0].global_quantities.resize(2)
    for gq, power in zip(src.source[0].global_quantities, (1e8, 2e8), strict=True):
        gq.power = power
    ctx = make_ctx({"core_sources": src})
    cs.fill_core_sources(ctx)
    np.testing.assert_allclose(ctx.builder.get("fusion/power"), [1e8, 2e8])


def test_core_source_power_from_energy_densities(make_ctx, factory):
    """Sources with only energy source densities are integrated over volume."""
    src = factory.core_sources()
    src.ids_properties.homogeneous_time = 1
    src.time = np.array([1.0, 2.0])
    src.source.resize(2)
    src.source[0].identifier.index = 7  # ohmic: electrons only
    src.source[1].identifier.index = 3  # ec: electrons and ions
    rho = np.array([0.0, 0.5, 1.0])
    for source in src.source:
        source.profiles_1d.resize(2)
        for profile in source.profiles_1d:
            profile.grid.rho_tor_norm = rho
            profile.grid.volume = 800 * rho**2
            profile.electrons.energy = np.full(3, 1e3)
    for profile in src.source[1].profiles_1d:
        profile.total_ion_energy = np.full(3, 2e3)
    ctx = make_ctx({"core_sources": src})
    cs.fill_core_sources(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("global_quantities/power_ohm"), [8e5] * 2)
    np.testing.assert_allclose(b.get("heating_current_drive/power_ec"), [2.4e6] * 2)
    assert b.filled["global_quantities/power_ohm"].endswith(
        "profiles_1d/(electrons/energy+total_ion_energy) (volume integral)"
    )

    # not integrated when the grid does not reach the separatrix
    for source in src.source:
        for profile in source.profiles_1d:
            profile.grid.rho_tor_norm = rho * 0.9
    ctx = make_ctx({"core_sources": src})
    cs.fill_core_sources(ctx)
    assert not ctx.builder.filled


@pytest.fixture
def ec_launchers(factory):
    ec = factory.ec_launchers()
    ec.ids_properties.homogeneous_time = 1
    ec.time = np.array([1.0, 2.0])
    ec.beam.resize(2)
    for beam, name in zip(ec.beam, ("A", "B"), strict=True):
        beam.name = name
        beam.power_launched.data = np.array([2e6, 2e6])
    return ec


def test_fill_waves(make_ctx, factory, ec_launchers):
    waves = factory.waves()
    waves.ids_properties.homogeneous_time = 1
    waves.time = np.array([0.0, 3.0])
    waves.coherent_wave.resize(4)
    for wave, antenna, wave_type, power in zip(
        waves.coherent_wave,
        ("A", "B", "A", "C"),
        (1, 1, 1, 1),
        ((1e6, 1e6), (1.5e6, 1.5e6), (0.0, 3e5), (1e6, 1e6)),
        strict=True,
    ):
        wave.identifier.antenna_name = antenna
        wave.identifier.type.index = wave_type
        wave.global_quantities.resize(2)
        for gq, p in zip(wave.global_quantities, power, strict=True):
            gq.power = p
    ctx = make_ctx({"waves": waves, "ec_launchers": ec_launchers})
    cs.fill_launchers(ctx)
    cs.fill_waves(ctx)
    b = ctx.builder
    np.testing.assert_allclose(b.get("heating_current_drive/ec[0]/power"), [1.1e6, 1.2e6])
    assert b.filled["heating_current_drive/ec[0]/power"] == (
        "waves/coherent_wave[0]+coherent_wave[2]/global_quantities/power"
    )
    np.testing.assert_allclose(b.get("heating_current_drive/ec[1]/power"), [1.5e6] * 2)
    # antenna C is not an EC launcher of the entry
    assert len(b.ids.heating_current_drive.ec) == 2


def test_single_launcher_power(make_ctx, factory, ec_launchers):
    ctx = make_ctx({"ec_launchers": ec_launchers})
    cs.fill_launchers(ctx)
    ctx.builder.set("heating_current_drive/power_ec", [1e6, 2e6], "test")
    cs.fill_derived(ctx)
    # two launchers: the total power cannot be attributed
    assert not ctx.builder.has("heating_current_drive/ec[0]/power")

    ec_launchers.beam.resize(1, keep=True)
    ctx = make_ctx({"ec_launchers": ec_launchers})
    cs.fill_launchers(ctx)
    ctx.builder.set("heating_current_drive/power_ec", [1e6, 2e6], "test")
    cs.fill_derived(ctx)
    np.testing.assert_allclose(ctx.builder.get("heating_current_drive/ec[0]/power"), [1e6, 2e6])


# --------------------------------------------------------------------------
# power balance and confinement
# --------------------------------------------------------------------------
ITER = {
    "global_quantities/energy_thermal": [3.0e8, 3.5e8, 4.0e8],  # dW/dt = 5e7 W
    "global_quantities/power_ohm": [1e6] * 3,
    "heating_current_drive/power_ec": [5e7] * 3,
    "fusion/power": [8.6e7] * 3,
    "global_quantities/power_radiated": [3e7] * 3,
    "global_quantities/ip": [-15e6] * 3,
    "global_quantities/b0": [-5.3] * 3,
    "global_quantities/r0": 6.2,
    "boundary/geometric_axis_r": [6.2] * 3,
    "boundary/minor_radius": [2.0] * 3,
    "global_quantities/volume": [830.0] * 3,
    "line_average/n_e": [1.0e20] * 3,
    "volume_average/meff_hydrogenic": [2.5] * 3,
}


def make_derived_ctx(make_ctx, values, time=(1.0, 2.0, 3.0)):
    ctx = make_ctx(time=time)
    for path, value in values.items():
        ctx.builder.set(path, np.asarray(value, dtype=float), "test")
    cs.fill_derived(ctx)
    return ctx.builder


def test_power_balance_and_confinement(make_ctx):
    b = make_derived_ctx(make_ctx, ITER)
    np.testing.assert_allclose(b.get("global_quantities/denergy_thermal_dt"), [5e7] * 3)
    p_steady = 1e6 + 5e7 + 8.6e7 - 5e7
    np.testing.assert_allclose(b.get("global_quantities/power_steady"), [p_steady] * 3)
    np.testing.assert_allclose(b.get("global_quantities/power_loss"), [p_steady - 3e7] * 3)
    assert b.filled["global_quantities/power_loss"] == (
        "summary/global_quantities/power_steady-(global_quantities/power_radiated)"
    )
    np.testing.assert_allclose(
        b.get("global_quantities/tau_energy"),
        np.array(ITER["global_quantities/energy_thermal"]) / p_steady,
    )
    np.testing.assert_allclose(b.get("global_quantities/greenwald_fraction"), [np.pi * 4 / 15] * 3)
    # IPB98(y,2) with the ITER Q=10 reference parameters gives about 3.7 s
    kappa_a = 830 / (2 * np.pi**2 * 6.2 * 4)
    tau_98 = (
        0.0562
        * 15**0.93
        * 5.3**0.15
        * 10**0.41
        * (p_steady / 1e6) ** -0.69
        * 6.2**1.97
        * kappa_a**0.78
        * (2 / 6.2) ** 0.58
        * 2.5**0.19
    )
    np.testing.assert_allclose(b.get("global_quantities/tau_energy_98"), [tau_98] * 3)
    assert 3.0 < tau_98 < 4.5
    np.testing.assert_allclose(
        b.get("global_quantities/h_98"),
        b.get("global_quantities/tau_energy") / tau_98,
    )


def test_power_loss_prefers_radiation_inside_lcfs(make_ctx):
    values = dict(ITER, **{"global_quantities/power_radiated_inside_lcfs": [2e7] * 3})
    b = make_derived_ctx(make_ctx, values)
    np.testing.assert_allclose(
        b.get("global_quantities/power_loss"),
        b.get("global_quantities/power_steady") - 2e7,
    )


def test_power_balance_needs_two_times(make_ctx):
    values = {k: (v[:1] if isinstance(v, list) else v) for k, v in ITER.items()}
    b = make_derived_ctx(make_ctx, values, time=(1.0,))
    for path in ("denergy_thermal_dt", "power_steady", "tau_energy", "h_98"):
        assert not b.has(f"global_quantities/{path}")
    # the Greenwald fraction does not depend on time derivatives
    assert b.has("global_quantities/greenwald_fraction")


def test_no_confinement_time_without_heating(make_ctx):
    values = {
        k: v
        for k, v in ITER.items()
        if k
        not in (
            "global_quantities/power_ohm",
            "heating_current_drive/power_ec",
            "fusion/power",
        )
    }
    b = make_derived_ctx(make_ctx, values)
    assert b.has("global_quantities/denergy_thermal_dt")
    for path in ("power_steady", "power_loss", "tau_energy", "tau_energy_98", "h_98"):
        assert not b.has(f"global_quantities/{path}")


def test_no_confinement_time_with_negative_loss_power(make_ctx):
    values = dict(ITER, **{"global_quantities/energy_thermal": [3e8, 3e8, 6e8]})
    b = make_derived_ctx(make_ctx, values)
    assert b.has("global_quantities/power_steady")
    assert not b.has("global_quantities/tau_energy")
    assert not b.has("global_quantities/h_98")
