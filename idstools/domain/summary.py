"""Create a summary IDS from the other IDSs stored in an IMAS data entry.

The summary is built from whatever IDSs are present in the entry
(equilibrium, core_profiles, core_sources, H&CD launchers, waves,
edge_profiles, radiation, gas_injection, magnetics, dataset_description, ...).
Power balance and confinement quantities (power_steady, power_loss,
tau_energy, h_98, ...) are then derived from the summary itself. Every filled
quantity records in its ``source`` node the IDS path it was taken or computed
from.

Data Dictionary 3 and 4 entries are supported. The summary is built with the
DD version the entry was produced with, so that the entry stays homogeneous
when the summary is written back into it; no conversion between DD versions
is done. Quantities whose summary or source nodes do not exist in that DD
version are skipped.

build_summary() only reads the data entry and returns the summary IDS, in
memory. write_summary() writes a summary IDS into a data entry; an existing
summary is only overwritten with ``force``.

The quantities computed from the profiles and derived from the summary itself
are documented with the create_summary script.

Example:
    >>> from idstools.domain.summary import build_summary, write_summary
    >>> summary = build_summary("imas:hdf5?path=/path/to/entry", verbose=True)
    >>> write_summary(summary, "imas:hdf5?path=/path/to/entry")
"""

import datetime
import getpass
import logging
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import imas
import imas.ids_defs
import imas.util
import numpy as np
from imas.db_entry import DBEntry
from imas.ids_data_type import IDSDataType
from numpy.typing import ArrayLike

# Any node of an IDS (structure, array of structures or data node): their
# children are attributes created from the Data Dictionary, unknown to mypy
IDSNode = Any

logger = logging.getLogger("module")

EMPTY_FLOAT = imas.ids_defs.EMPTY_FLOAT
EMPTY_INT = imas.ids_defs.EMPTY_INT

SUPPORTED_DD_MAJOR = ("3", "4")

# IDSs tried, in this order, to define the time base of the summary
TIME_BASE_CANDIDATES = [
    ("core_profiles", "profiles_1d"),
    ("plasma_profiles", "profiles_1d"),
    ("edge_profiles", "ggd"),
    ("plasma_profiles", "ggd"),
    ("equilibrium", "time_slice"),
    ("core_sources", None),
    ("magnetics", None),
]

# Radial grid of core profiles: largest rho_tor_norm of the first point for an
# axis value (profiles are flat on axis), largest distance of the last point to
# the separatrix, and largest fraction of the plasma volume that may be missing
# inside the first point for a volume average
AXIS_RHO_TOLERANCE = 0.01
SEPARATRIX_RHO_TOLERANCE = 1e-3
VOLUME_FRACTION_TOLERANCE = 1e-3

# GGD grid subset identifiers (imas.identifiers.ggd_subset_identifier)
GGD_CELLS = 5
GGD_X_POINTS = 6
GGD_CORE = 22
GGD_SOL = 23
GGD_OUTER_MIDPLANE_SEPARATRIX = 101
GGD_OUTER_TARGET_SEPARATRIX = 103
GGD_INNER_TARGET_SEPARATRIX = 104

# summary species name for (z_n, a) of single-element ions
SPECIES_BY_Z: Dict[int, Union[str, Dict[int, str]]] = {
    2: {3: "helium_3", 4: "helium_4"},
    3: "lithium",
    4: "beryllium",
    5: "boron",
    6: "carbon",
    7: "nitrogen",
    8: "oxygen",
    10: "neon",
    18: "argon",
    26: "iron",
    36: "krypton",
    54: "xenon",
    74: "tungsten",
}

# core_sources identifier name -> (summary path, sign) of the source power
CORE_SOURCE_POWERS = {
    "nbi": ("heating_current_drive/power_nbi", 1),
    "ec": ("heating_current_drive/power_ec", 1),
    "lh": ("heating_current_drive/power_lh", 1),
    "ic": ("heating_current_drive/power_ic", 1),
    "ohmic": ("global_quantities/power_ohm", 1),
    "bremsstrahlung": ("global_quantities/power_bremsstrahlung", -1),
    "synchrotron_radiation": ("global_quantities/power_synchrotron", -1),
    "line_radiation": ("global_quantities/power_line", -1),
    "radiation": ("global_quantities/power_radiated", -1),
    "fusion": ("fusion/power", 1),
}

# Hydrogenic species of the summary (for the effective hydrogenic mass)
HYDROGENIC = ("hydrogen", "deuterium", "tritium", "deuterium_tritium")

ELEMENTARY_CHARGE = 1.602176634e-19  # J/eV


class SummaryError(Exception):
    """The summary IDS cannot be created from the data entry."""


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def get_node(node: IDSNode, path: str) -> Optional[IDSNode]:
    """Return the node at ``path`` (``a/b[0]/c``) below ``node``, or None."""
    for part in path.split("/"):
        match = re.fullmatch(r"(\w+)\[(\d+)\]", part)
        name = match.group(1) if match else part
        try:
            node = getattr(node, name)
        except AttributeError:
            return None
        if match:
            index = int(match.group(2))
            if index >= len(node):
                return None
            node = node[index]
    return node


def get_value(node: IDSNode, path: str) -> Any:
    """Return the value at ``path`` below ``node``, or None when missing/empty.

    Empty floats are returned as NaN, so they can be filtered out later.
    """
    leaf = get_node(node, path)
    if leaf is None or not hasattr(leaf, "has_value") or not leaf.has_value:
        return None
    if leaf.metadata.data_type in (IDSDataType.STRUCTURE, IDSDataType.STRUCT_ARRAY):
        return None
    value = leaf.value
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "f":
            value = np.where(value <= EMPTY_FLOAT / 10, np.nan, value)
        return value
    if isinstance(value, float) and value <= EMPTY_FLOAT / 10:
        return np.nan
    return value


def first_value(node: IDSNode, paths: Sequence[str]) -> Tuple[Any, Optional[str]]:
    """Return the first non-empty value of a list of candidate paths."""
    for path in paths:
        value = get_value(node, path)
        if value is not None:
            return value, path
    return None, None


def as_float(value: Any) -> float:
    """Scalar float of a value (first element of arrays), NaN when missing."""
    if value is None:
        return np.nan
    value = np.asarray(value, dtype=float).ravel()
    return float(value[0]) if value.size else np.nan


def species_name(element_aos: IDSNode) -> Optional[str]:
    """Summary species name of an ion/neutral described by ``element_aos``."""
    if len(element_aos) != 1:
        return None
    element = element_aos[0]
    atoms_n = get_value(element, "atoms_n")
    if atoms_n not in (None, EMPTY_INT, 1):
        return None
    z_n = as_float(get_value(element, "z_n"))
    a = as_float(get_value(element, "a"))
    if not np.isfinite(z_n):
        return None
    z_n = int(round(z_n))
    if z_n == 1:
        if not np.isfinite(a):
            return None
        if abs(a - 2.5) < 0.2:
            return "deuterium_tritium"
        return {1: "hydrogen", 2: "deuterium", 3: "tritium"}.get(int(round(a)))
    name = SPECIES_BY_Z.get(z_n)
    if isinstance(name, dict):
        return name.get(int(round(a))) if np.isfinite(a) else None
    return name


def ids_times(ids: IDSNode, aos_name: Optional[str] = None) -> Optional[np.ndarray]:
    """Time vector of an IDS, or of one of its time-dependent AoS."""
    homogeneous = ids.ids_properties.homogeneous_time
    if homogeneous == imas.ids_defs.IDS_TIME_MODE_INDEPENDENT:
        return None
    if homogeneous == imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS and len(ids.time):
        return np.asarray(ids.time, dtype=float)
    if aos_name is not None:
        aos = get_node(ids, aos_name)
        if aos is not None and len(aos):
            return np.array([as_float(get_value(item, "time")) for item in aos])
    return None


def signal_times(ids: IDSNode, signal: IDSNode) -> np.ndarray:
    """Time vector of a ``{data, time}`` signal structure."""
    if ids.ids_properties.homogeneous_time == imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS:
        return np.asarray(ids.time, dtype=float)
    return np.asarray(signal.time, dtype=float)


# --------------------------------------------------------------------------
# Summary builder
# --------------------------------------------------------------------------
class SummaryBuilder:
    """Fill a summary IDS on a fixed time base, keeping track of sources.

    Quantities are written at most once: the first filler providing a
    quantity wins, so fillers are called in order of preference.
    """

    def __init__(self, summary: IDSNode, time: ArrayLike) -> None:
        self.ids = summary
        self.time = np.asarray(time, dtype=float)
        self.filled: Dict[str, str] = {}  # summary path -> source
        self.ids.time = self.time
        span = np.ptp(self.time) if self.time.size > 1 else 0.0
        self.tolerance = 1e-6 * max(1.0, span, float(np.max(np.abs(self.time))))

    def has(self, path: str) -> bool:
        return path in self.filled

    def _resolve(self, path: str) -> Optional[IDSNode]:
        """Return the node at ``path``, resizing AoS as needed; None if absent."""
        node = self.ids
        for part in path.split("/"):
            match = re.fullmatch(r"(\w+)\[(\d+)\]", part)
            name = match.group(1) if match else part
            try:
                node = getattr(node, name)
            except AttributeError:
                logger.debug("%s not in this DD version, skipped", path)
                return None
            if match:
                index = int(match.group(2))
                if len(node) <= index:
                    node.resize(index + 1, keep=True)
                node = node[index]
        return node

    def interpolate(
        self, t_src: Optional[ArrayLike], y_src: Optional[ArrayLike], nearest: bool = False
    ) -> Optional[np.ndarray]:
        """Map a signal on the summary time base; None if it does not cover it."""
        if t_src is None or y_src is None:
            return None
        t = np.atleast_1d(np.asarray(t_src, dtype=float))
        y = np.atleast_1d(np.asarray(y_src, dtype=float))
        if t.shape != y.shape:
            logger.debug("time/data shape mismatch %s %s", t.shape, y.shape)
            return None
        valid = np.isfinite(t) & np.isfinite(y)
        if not valid.any():
            return None
        t, y = t[valid], y[valid]
        order = np.argsort(t)
        t, y = t[order], y[order]
        if self.time.min() < t[0] - self.tolerance or self.time.max() > t[-1] + self.tolerance:
            return None
        if t.size == 1:
            return np.full(self.time.shape, y[0])
        if nearest:
            index = np.searchsorted(t, self.time)
            index = np.clip(index, 1, t.size - 1)
            left_closer = (self.time - t[index - 1]) < (t[index] - self.time)
            return y[np.where(left_closer, index - 1, index)]
        return np.interp(self.time, t, y)

    def set(self, path: str, value: Any, source: str, replace: bool = False) -> bool:
        """Set the summary quantity ``path`` (a value/source node, or a leaf).

        Time-dependent quantities must already be on the summary time base.
        An already filled quantity is only overwritten with ``replace``.
        Returns True if the quantity was written.
        """
        if value is None or (path in self.filled and not replace):
            return False
        node = self._resolve(path)
        if node is None:
            return False
        has_source = hasattr(node, "value") and hasattr(node, "source")
        leaf = node.value if has_source else node
        metadata = leaf.metadata
        if metadata.data_type is IDSDataType.STRUCTURE:
            logger.debug("%s is a structure, skipped", path)
            return False
        if metadata.data_type is IDSDataType.STR:
            if not value:
                return False
            leaf.value = str(value)
        elif metadata.ndim == 0:
            value = as_float(value)
            if not np.isfinite(value):
                return False
            leaf.value = int(round(value)) if metadata.data_type is IDSDataType.INT else value
        else:
            value = np.asarray(value, dtype=float)
            if value.ndim == 0:
                value = np.full(self.time.shape, float(value))
            if value.shape != self.time.shape or not np.all(np.isfinite(value)):
                logger.debug("%s: invalid or incomplete data, skipped", path)
                return False
            if metadata.data_type is IDSDataType.INT:
                value = np.rint(value).astype(np.int32)
            leaf.value = value
        if has_source:
            node.source = source
        self.filled[path] = source
        return True

    def set_signal(
        self,
        path: str,
        t_src: Optional[ArrayLike],
        y_src: Optional[ArrayLike],
        source: str,
        nearest: bool = False,
    ) -> bool:
        """Interpolate a signal on the summary time base and set it."""
        return self.set(path, self.interpolate(t_src, y_src, nearest), source)

    def get(self, path: str) -> Optional[np.ndarray]:
        """Value of an already filled quantity (None if not filled)."""
        return self.value(path) if path in self.filled else None

    def value(self, path: str) -> np.ndarray:
        """Value of a filled quantity (KeyError if not filled)."""
        if path not in self.filled:
            raise KeyError(f"{path} is not filled")
        node: IDSNode = get_node(self.ids, path)
        if hasattr(node, "source"):
            node = node.value
        return np.asarray(node.value)


class Context:
    """Data entry access shared by the fillers.

    The summary builder is attached once the time base is known.
    """

    builder: SummaryBuilder

    def __init__(self, entry: DBEntry, uri: str, available: Set[str]) -> None:
        self.entry = entry
        self.uri = uri
        self.available = available
        self._cache: Dict[str, Optional[IDSNode]] = {}

    def get(self, ids_name: str) -> Optional[IDSNode]:
        """Return the (cached) IDS, or None when not in the entry."""
        if ids_name not in self.available:
            return None
        if ids_name not in self._cache:
            logger.info("Reading %s", ids_name)
            try:
                self._cache[ids_name] = self.entry.get(ids_name, autoconvert=True)
            except Exception as exc:  # e.g. IDS not defined in this DD version
                logger.warning("Could not read %s: %s", ids_name, exc)
                self._cache[ids_name] = None
        return self._cache[ids_name]


# --------------------------------------------------------------------------
# Fillers, one per source IDS (or family of IDSs)
# --------------------------------------------------------------------------
def fill_from_slices(
    ctx: Context,
    ids: IDSNode,
    aos_name: str,
    mapping: Sequence[Tuple[str, Sequence[str], bool]],
    prefix: str,
) -> None:
    """Fill summary quantities from per-time-slice values of an AoS.

    ``mapping`` is a list of (summary path, [candidate source paths], nearest).
    """
    times = ids_times(ids, aos_name)
    aos = get_node(ids, aos_name)
    if times is None or aos is None or not len(aos):
        return
    for dst, candidates, nearest in mapping:
        if ctx.builder.has(dst):
            continue
        values, used = [], None
        for item in aos:
            value, path = first_value(item, candidates)
            values.append(as_float(value))
            used = used or path
        if used is None:
            continue
        ctx.builder.set_signal(dst, times, np.array(values), f"{prefix}/{aos_name}/{used}", nearest)


def fill_metadata(ctx: Context, time_base_ids: str) -> None:
    """ids_properties, code, data entry description and midplane."""
    summary = ctx.builder.ids
    summary.ids_properties.homogeneous_time = imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
    summary.ids_properties.provider = getpass.getuser()
    summary.ids_properties.creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # code: from the IDS defining the time base, else the first one that has it
    candidates = [time_base_ids, "dataset_description"] + sorted(ctx.available)
    for name in candidates:
        ids = ctx.get(name)
        if ids is None or not get_value(ids, "code/name"):
            continue  # no code description (dataset_description has none in DD3)
        logger.info("Copying code description from %s", name)
        for field in (
            "name",
            "description",
            "commit",
            "version",
            "repository",
            "parameters",
        ):
            ctx.builder.set(f"code/{field}", get_value(ids.code, field), name)
        for i, library in enumerate(ids.code.library):
            for field in (
                "name",
                "description",
                "commit",
                "version",
                "repository",
                "parameters",
            ):
                ctx.builder.set(f"code/library[{i}]/{field}", get_value(library, field), name)
        break

    # Data entry description: in DD >= 4.1 the summary holds the same
    # machine/pulse/type/simulation nodes as dataset_description
    dataset = ctx.get("dataset_description")
    if dataset is not None:
        for path in (
            "machine",
            "pulse",
            "type/name",
            "type/index",
            "type/description",
            "pulse_time_begin",
            "pulse_time_begin_epoch/seconds",
            "pulse_time_begin_epoch/nanoseconds",
            "pulse_time_end_epoch/seconds",
            "pulse_time_end_epoch/nanoseconds",
            "pulse_processing_time_begin",
            "description",
            "simulation/time_begin",
            "simulation/time_step",
            "simulation/time_end",
            "simulation/workflow",
        ):
            ctx.builder.set(path, get_value(dataset, path), "dataset_description")

    for name in (time_base_ids, "edge_profiles", "core_profiles"):
        ids = ctx.get(name)
        midplane = get_node(ids, "midplane") if ids is not None else None
        if midplane is not None and midplane.index.has_value:
            for field in ("name", "index", "description"):
                ctx.builder.set(f"midplane/{field}", get_value(midplane, field), f"{name}/midplane")
            break


def fill_vacuum_field(ctx: Context) -> None:
    """r0/b0 from the first IDS providing vacuum_toroidal_field."""
    for name in (
        "equilibrium",
        "core_profiles",
        "edge_profiles",
        "plasma_profiles",
        "core_sources",
        "radiation",
    ):
        ids = ctx.get(name)
        if ids is None or get_node(ids, "vacuum_toroidal_field") is None:
            continue
        vtf = ids.vacuum_toroidal_field
        r0 = get_value(vtf, "r0")
        b0 = get_value(vtf, "b0")
        if r0 is None or b0 is None:
            continue
        ctx.builder.set("global_quantities/r0", r0, f"{name}/vacuum_toroidal_field/r0")
        ctx.builder.set_signal(
            "global_quantities/b0",
            ids_times(ids),
            b0,
            f"{name}/vacuum_toroidal_field/b0",
        )
        if ctx.builder.has("global_quantities/b0"):
            return


def fill_equilibrium(ctx: Context) -> None:
    eq = ctx.get("equilibrium")
    if eq is None:
        return
    mapping = [
        ("global_quantities/ip", ["global_quantities/ip"], False),
        ("global_quantities/q_95", ["global_quantities/q_95"], False),
        # li_3_mhd (DD4) is li_mhd in DD3, with the same (li_3) definition
        ("global_quantities/li_3_mhd", ["global_quantities/li_3"], False),
        ("global_quantities/li_mhd", ["global_quantities/li_3"], False),
        ("global_quantities/beta_pol_mhd", ["global_quantities/beta_pol"], False),
        ("global_quantities/beta_tor_mhd", ["global_quantities/beta_tor"], False),
        (
            "global_quantities/beta_tor_norm_mhd",
            # beta_normal in DD3, with the same definition
            ["global_quantities/beta_tor_norm", "global_quantities/beta_normal"],
            False,
        ),
        ("global_quantities/energy_mhd", ["global_quantities/energy_mhd"], False),
        ("global_quantities/volume", ["global_quantities/volume"], False),
        (
            "global_quantities/psi_external_average",
            ["global_quantities/psi_external_average"],
            False,
        ),
        (
            "global_quantities/resistance",
            ["global_quantities/plasma_resistance"],
            False,
        ),
        (
            "local/magnetic_axis/position/r",
            ["global_quantities/magnetic_axis/r"],
            False,
        ),
        (
            "local/magnetic_axis/position/z",
            ["global_quantities/magnetic_axis/z"],
            False,
        ),
        ("local/magnetic_axis/q", ["global_quantities/q_axis"], False),
        (
            "local/magnetic_axis/b_field_phi",
            [
                "global_quantities/magnetic_axis/b_field_phi",
                "global_quantities/magnetic_axis/b_field_tor",
            ],
            False,
        ),
        (
            "local/magnetic_axis/b_field_tor",
            [
                "global_quantities/magnetic_axis/b_field_phi",
                "global_quantities/magnetic_axis/b_field_tor",
            ],
            False,
        ),
        ("boundary/type", ["boundary/type"], True),
        ("boundary/magnetic_axis_r", ["global_quantities/magnetic_axis/r"], False),
        ("boundary/magnetic_axis_z", ["global_quantities/magnetic_axis/z"], False),
        ("boundary/geometric_axis_r", ["boundary/geometric_axis/r"], False),
        ("boundary/geometric_axis_z", ["boundary/geometric_axis/z"], False),
        ("boundary/minor_radius", ["boundary/minor_radius"], False),
        ("boundary/elongation", ["boundary/elongation"], False),
        ("boundary/triangularity_upper", ["boundary/triangularity_upper"], False),
        ("boundary/triangularity_lower", ["boundary/triangularity_lower"], False),
    ]
    fill_from_slices(ctx, eq, "time_slice", mapping, "equilibrium")


def covers_plasma(rho: Optional[np.ndarray]) -> bool:
    """True if a rho_tor_norm grid goes from the magnetic axis to the separatrix."""
    return (
        rho is not None
        and rho.size >= 2
        and abs(rho[0]) < AXIS_RHO_TOLERANCE
        and abs(rho[-1] - 1) < SEPARATRIX_RHO_TOLERANCE
    )


def profile_reductions(
    profile: IDSNode, chord: Optional[np.ndarray] = None
) -> Dict[str, Callable[[np.ndarray], float]]:
    """Axis value, separatrix value, volume average and integral of a 1D profile,
    and line average when the chord width ``chord`` is given on the profile grid.

    Only defined when the radial grid reaches the axis / the separatrix
    (and, for the volume average and integral, covers the whole plasma
    volume). Returns a dict of callables taking the profile array.
    """
    rho = get_value(profile, "grid/rho_tor_norm")
    volume = get_value(profile, "grid/volume")
    reductions: Dict[str, Callable[[np.ndarray], float]] = {}
    if rho is None or rho.size < 2:
        return reductions
    at_separatrix = abs(rho[-1] - 1) < SEPARATRIX_RHO_TOLERANCE
    if abs(rho[0]) < AXIS_RHO_TOLERANCE:
        reductions["magnetic_axis"] = lambda y: y[0]
    if at_separatrix:
        reductions["separatrix"] = lambda y: y[-1]
    if (
        at_separatrix
        and volume is not None
        and volume.size == rho.size
        and volume[-1] > 0
        and abs(volume[0]) <= VOLUME_FRACTION_TOLERANCE * volume[-1]
    ):
        reductions["volume_integral"] = lambda y: np.trapezoid(y, volume)
        reductions["volume_average"] = lambda y: np.trapezoid(y, volume) / (volume[-1] - volume[0])
    if covers_plasma(rho) and chord is not None and chord.size == rho.size and chord[-1] > chord[0]:
        # the chord crosses each flux surface on both sides of the axis: the
        # integral along it is the integral over its width R_out - R_in
        reductions["line_average"] = lambda y: np.trapezoid(y, chord) / (chord[-1] - chord[0])
    return reductions


SUMMARY_LOCATION = {
    "magnetic_axis": "local/magnetic_axis",
    "separatrix": "local/separatrix",
    "volume_average": "volume_average",
    "line_average": "line_average",
}
# relative difference tolerated between the thermal energies from
# pressure_thermal and from the electron + ion pressures
THERMAL_ENERGY_TOLERANCE = 0.01

SOURCE_NOTE = {
    "magnetic_axis": "value on axis",
    "separatrix": "value at rho_tor_norm=1",
    "volume_average": "volume average",
    "line_average": "line average on the horizontal chord through the magnetic "
    "axis, from equilibrium/time_slice/profiles_1d/r_inboard and r_outboard",
}


def chord_width(
    eq: IDSNode, eq_times: Optional[np.ndarray], time: float, rho: np.ndarray, tolerance: float
) -> Optional[np.ndarray]:
    """Width R_outboard - R_inboard of the horizontal chord through the magnetic
    axis at the flux surfaces ``rho`` (rho_tor_norm) at ``time``.

    Interpolated linearly in time between the equilibrium time slices; None
    when the equilibrium does not cover ``time`` or lacks the profiles.
    """
    if eq_times is None or not np.isfinite(time):
        return None
    order = np.argsort(eq_times)
    t_sorted = eq_times[order]
    if time < t_sorted[0] - tolerance or time > t_sorted[-1] + tolerance:
        return None
    upper = int(np.clip(np.searchsorted(t_sorted, time), 0, t_sorted.size - 1))
    lower = max(upper - 1, 0)
    if abs(t_sorted[upper] - time) <= tolerance or upper == lower:
        lower = upper
    widths = []
    for index in dict.fromkeys((order[lower], order[upper])):
        profiles = eq.time_slice[index].profiles_1d
        rho_eq = get_value(profiles, "rho_tor_norm")
        r_in = get_value(profiles, "r_inboard")
        r_out = get_value(profiles, "r_outboard")
        if (
            not covers_plasma(rho_eq)
            or r_in is None
            or r_out is None
            or not r_in.size == r_out.size == rho_eq.size
            or not np.all(np.isfinite(r_out - r_in))
        ):
            return None
        widths.append(np.interp(rho, rho_eq, r_out - r_in))
    if len(widths) == 1:
        return widths[0]
    t0, t1 = t_sorted[lower], t_sorted[upper]
    weight = (time - t0) / (t1 - t0)
    return (1 - weight) * widths[0] + weight * widths[1]


def thermal_pressures(profile: IDSNode) -> Dict[str, Tuple[str, np.ndarray]]:
    """Thermal pressures [Pa] of a core profile, with the path they come from.

    Returns a dict name -> (path, pressure) for "electrons", "ions" and
    "total", each present only when it can be obtained. The total is
    electrons + ions when both are available, else pressure_thermal; in the
    first case pressure_thermal, if present, is returned as "reported_total".
    """
    n_rho = profile.grid.rho_tor_norm.size

    def valid(value: Optional[np.ndarray]) -> bool:
        return value is not None and value.size == n_rho

    def from_density(species: IDSNode, temperature: Optional[np.ndarray]) -> Tuple[Optional[np.ndarray], Optional[str]]:
        density, path = first_value(species, ["density_thermal", "density"])
        if not valid(density) or not valid(temperature):
            return None, None
        return ELEMENTARY_CHARGE * density * temperature, path

    pressures = {}
    p_e = get_value(profile, "electrons/pressure_thermal")
    if valid(p_e):
        pressures["electrons"] = ("electrons/pressure_thermal", p_e)
    else:
        p_e, path = from_density(profile.electrons, get_value(profile, "electrons/temperature"))
        if p_e is not None:
            pressures["electrons"] = (f"electrons/({path}*temperature)", p_e)

    p_i = get_value(profile, "pressure_ion_total")
    if valid(p_i):
        pressures["ions"] = ("pressure_ion_total", p_i)
    elif len(profile.ion):
        p_i, paths = 0.0, set()
        for ion in profile.ion:
            p_ion = get_value(ion, "pressure_thermal")
            if valid(p_ion):
                paths.add("pressure_thermal")
            else:
                temperature, t_path = first_value(ion, ["temperature"])
                if temperature is None:
                    temperature = get_value(profile, "t_i_average")
                    t_path = "../t_i_average"
                p_ion, path = from_density(ion, temperature)
                if p_ion is None:
                    p_i = None
                    break
                paths.add(f"{path}*{t_path}")
            p_i = p_i + p_ion
        if p_i is not None:
            pressures["ions"] = (f"ion[:]/({'|'.join(sorted(paths))})", p_i)

    # the total is the sum of the electron and ion pressures, so that the
    # summary energies are consistent; pressure_thermal is only used when a
    # component is missing, and otherwise returned to be checked
    p_total = get_value(profile, "pressure_thermal")
    if "electrons" in pressures and "ions" in pressures:
        pressures["total"] = (
            f"({pressures['electrons'][0]}+{pressures['ions'][0]})",
            pressures["electrons"][1] + pressures["ions"][1],
        )
        if valid(p_total):
            pressures["reported_total"] = ("pressure_thermal", p_total)
    elif valid(p_total):
        pressures["total"] = ("pressure_thermal", p_total)
    return pressures


def fill_core_profiles(ctx: Context) -> None:
    cp = ctx.get("core_profiles")
    if cp is None:
        return

    # 0D global quantities computed by the transport code
    if len(cp.time):
        times = ids_times(cp)
        gq = cp.global_quantities
        for dst, candidates in [
            ("global_quantities/ip", ["ip"]),
            ("global_quantities/current_non_inductive", ["current_non_inductive"]),
            ("global_quantities/current_bootstrap", ["current_bootstrap"]),
            ("global_quantities/v_loop", ["v_loop"]),
            # li_3 (DD4) is li in the DD3 summary, both with the li_3 definition
            ("global_quantities/li_3", ["li_3", "li"]),
            ("global_quantities/li", ["li_3", "li"]),
            ("global_quantities/beta_pol", ["beta_pol"]),
            ("global_quantities/beta_tor", ["beta_tor"]),
            ("global_quantities/beta_tor_norm", ["beta_tor_norm"]),
            ("global_quantities/energy_diamagnetic", ["energy_diamagnetic"]),
            ("volume_average/t_e", ["t_e_volume_average"]),
            ("volume_average/n_e", ["n_e_volume_average"]),
        ]:
            value, src = first_value(gq, candidates)
            ctx.builder.set_signal(dst, times, value, f"core_profiles/global_quantities/{src}")
        # ohmic (inductive) current, from the same code as the total current
        ip = get_value(gq, "ip")
        current_non_inductive = get_value(gq, "current_non_inductive")
        if ip is not None and current_non_inductive is not None:
            if np.shape(ip) == np.shape(current_non_inductive):
                ctx.builder.set_signal(
                    "global_quantities/current_ohm",
                    times,
                    ip - current_non_inductive,
                    "core_profiles/global_quantities/(ip-current_non_inductive)",
                )

    # Reductions of the 1D profiles
    times = ids_times(cp, "profiles_1d")
    if times is None or not len(cp.profiles_1d):
        return
    series: Dict[Tuple[str, str], List[float]] = {}  # (summary path, source) -> values per time slice
    energy_checks: List[Tuple[float, float]] = []  # thermal energy from electrons + ions, from pressure_thermal

    def add(it: int, dst: str, src: str, value: float) -> None:
        series.setdefault((dst, src), [np.nan] * len(cp.profiles_1d))
        series[(dst, src)][it] = value

    eq = ctx.get("equilibrium")
    eq_times = ids_times(eq, "time_slice") if eq is not None else None
    for it, profile in enumerate(cp.profiles_1d):
        chord = None
        if eq_times is not None and profile.grid.rho_tor_norm.has_value:
            chord = chord_width(
                eq,
                eq_times,
                times[it],
                np.asarray(profile.grid.rho_tor_norm),
                ctx.builder.tolerance,
            )
        reductions = profile_reductions(profile, chord)
        quantities = []
        for name, path in [
            ("t_e", "electrons/temperature"),
            ("n_e", "electrons/density"),
            ("t_i_average", "t_i_average"),
            ("zeff", "zeff"),
        ]:
            quantities.append((name, path, get_value(profile, path)))
        # n_i_total sums all ion species, n_i/<species> only the ones that
        # have a summary node
        n_i_total = None
        for i, ion in enumerate(profile.ion):
            density = get_value(ion, "density")
            if density is None:
                continue
            n_i_total = density if n_i_total is None else n_i_total + density
            species = species_name(ion.element)
            if species is not None:
                quantities.append((f"n_i/{species}", f"ion[{i}]/density", density))
        quantities.append(("n_i_total", "ion[:]/density", n_i_total))
        for location, reduce in reductions.items():
            if location not in SUMMARY_LOCATION:
                continue
            for name, path, y in quantities:
                if y is None or y.size != profile.grid.rho_tor_norm.size:
                    continue
                add(
                    it,
                    f"{SUMMARY_LOCATION[location]}/{name}",
                    f"core_profiles/profiles_1d/{path} ({SOURCE_NOTE[location]})",
                    float(reduce(y)),
                )
        if "volume_integral" in reductions:
            for dst, src, value in profile_integrals(profile, reductions, energy_checks):
                add(it, dst, f"core_profiles/profiles_1d/{src}", value)

    for (dst, src), values in series.items():
        ctx.builder.set_signal(dst, times, np.array(values), src)
    check_thermal_energy(energy_checks)


def check_thermal_energy(energy_checks: Sequence[Tuple[float, float]]) -> None:
    """Warn when pressure_thermal disagrees with the electron + ion pressures.

    The DD defines pressure_thermal as the electron + ion thermal pressure;
    a mismatch points to an inconsistent core_profiles IDS.
    """
    w_sum, w_reported = np.array(energy_checks, dtype=float).reshape(-1, 2).T
    bad = ~np.isclose(w_reported, w_sum, rtol=THERMAL_ENERGY_TOLERANCE, atol=0)
    if not bad.any():
        return
    first = int(np.argmax(bad))
    logger.warning(
        "core_profiles pressure_thermal disagrees with the electron + ion thermal pressures at %d of %d time(s)"
        " (first: thermal energies %.4g J and %.4g J): energy_thermal is the electron + ion energy",
        bad.sum(),
        len(bad),
        w_reported[first],
        w_sum[first],
    )


def profile_integrals(
    profile: IDSNode,
    reductions: Dict[str, Callable[[np.ndarray], float]],
    energy_checks: Optional[List[Tuple[float, float]]] = None,
) -> List[Tuple[str, str, float]]:
    """Energy contents and hydrogenic composition of a core profile.

    Returns a list of (summary path, source path, value). When the thermal
    energy is computed from the electron and ion pressures and the profile
    also has pressure_thermal, (energy from the components, energy from
    pressure_thermal) is appended to ``energy_checks``.
    """
    integrate = reductions["volume_integral"]
    average = reductions["volume_average"]
    n_rho = profile.grid.rho_tor_norm.size
    results = []

    # W = 3/2 * integral of the pressure over the plasma volume
    pressures = thermal_pressures(profile)
    for dst, key in (
        ("global_quantities/energy_thermal", "total"),
        ("global_quantities/energy_electrons_thermal", "electrons"),
        ("global_quantities/energy_ion_total_thermal", "ions"),
    ):
        if key in pressures:
            path, pressure = pressures[key]
            src = f"{path} (3/2 volume integral)"
            results.append((dst, src, 1.5 * integrate(pressure)))
    if "reported_total" in pressures and energy_checks is not None:
        energy_checks.append((1.5 * integrate(pressures["total"][1]), 1.5 * integrate(pressures["reported_total"][1])))
    # total kinetic pressure (p_par + 2 p_perp) / 3, including fast particles
    p_par = get_value(profile, "pressure_parallel")
    p_perp = get_value(profile, "pressure_perpendicular")
    if p_par is not None and p_perp is not None and p_par.size == p_perp.size == n_rho:
        results.append(
            (
                "global_quantities/energy_total",
                "(pressure_parallel/2+pressure_perpendicular) (volume integral)",
                integrate(p_par / 2 + p_perp),
            )
        )

    # effective mass and hydrogen fraction of the hydrogenic ions
    densities: List[float] = []
    masses: List[float] = []
    is_hydrogen: List[bool] = []
    for ion in profile.ion:
        species = species_name(ion.element)
        density = get_value(ion, "density")
        if species not in HYDROGENIC or density is None or density.size != n_rho:
            continue
        densities.append(average(density))
        masses.append(as_float(get_value(ion.element[0], "a")))
        is_hydrogen.append(species == "hydrogen")
    n_hydrogenic = np.array(densities)
    if n_hydrogenic.size and n_hydrogenic.sum() > 0:
        src = "ion[hydrogenic]/density and element/a (volume average)"
        results.append(
            (
                "volume_average/meff_hydrogenic",
                src,
                float(np.dot(masses, n_hydrogenic) / n_hydrogenic.sum()),
            )
        )
        results.append(
            (
                "volume_average/isotope_fraction_hydrogen",
                src,
                float(n_hydrogenic[is_hydrogen].sum() / n_hydrogenic.sum()),
            )
        )
    return results


def source_power(cs: IDSNode, source: IDSNode) -> Optional[Tuple[np.ndarray, np.ndarray, str]]:
    """(times, total power, source path) of a core source, or None.

    Uses global_quantities/power, else the volume integrals of the
    profiles_1d at the last radial point, else the integral of the energy
    source densities over the plasma volume.
    """
    homogeneous = cs.ids_properties.homogeneous_time == imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
    if len(source.global_quantities):
        times = (
            np.asarray(cs.time, dtype=float)
            if homogeneous
            else np.array([as_float(get_value(g, "time")) for g in source.global_quantities])
        )
        power = np.array([as_float(get_value(g, "power")) for g in source.global_quantities])
        if np.isfinite(power).any():
            return times, power, "global_quantities/power"
    if len(source.profiles_1d):
        times = (
            np.asarray(cs.time, dtype=float)
            if homogeneous
            else np.array([as_float(get_value(p, "time")) for p in source.profiles_1d])
        )
        edge_power: List[float] = []
        for profile in source.profiles_1d:
            parts = [get_value(profile, path) for path in ("electrons/power_inside", "total_ion_power_inside")]
            parts = [part[-1] for part in parts if part is not None and part.size]
            edge_power.append(sum(parts) if parts else np.nan)
        power = np.array(edge_power, dtype=float)
        if np.isfinite(power).any():
            return (
                times,
                power,
                "profiles_1d/" "(electrons/power_inside+total_ion_power_inside)[-1]",
            )
        power = np.array([energy_source_integral(p) for p in source.profiles_1d])
        if np.isfinite(power).any():
            return (
                times,
                power,
                "profiles_1d/(electrons/energy+total_ion_energy) (volume integral)",
            )
    return None


def energy_source_integral(profile: IDSNode) -> float:
    """Integral of the electron and ion energy sources over the plasma volume
    (NaN if the grid does not cover it or no energy source is given)."""
    rho = get_value(profile, "grid/rho_tor_norm")
    volume = get_value(profile, "grid/volume")
    if (
        rho is None
        or volume is None
        or volume.size != rho.size
        or volume.size < 2
        or abs(rho[-1] - 1) >= SEPARATRIX_RHO_TOLERANCE
        or volume[-1] <= 0
        or abs(volume[0]) > VOLUME_FRACTION_TOLERANCE * volume[-1]
    ):
        return np.nan
    parts = [get_value(profile, path) for path in ("electrons/energy", "total_ion_energy")]
    parts = [part for part in parts if part is not None and part.size == volume.size]
    return sum(np.trapezoid(part, volume) for part in parts) if parts else np.nan


def fill_core_sources(ctx: Context) -> None:
    cs = ctx.get("core_sources")
    if cs is None:
        return
    names_by_index = {m.index: m.name for m in imas.identifiers.core_source_identifier}
    totals: Dict[str, List[Any]] = {}  # summary path -> [times, values, source names, source path]
    for i, source in enumerate(cs.source):
        name = source.identifier.name.strip().lower()
        if not name:
            name = names_by_index.get(source.identifier.index.value, "")
        if name not in CORE_SOURCE_POWERS:
            continue
        dst, sign = CORE_SOURCE_POWERS[name]
        result = source_power(cs, source)
        if result is None:
            continue
        times, power, path = result
        if dst in totals:
            if not (np.array_equal(totals[dst][0], times) and totals[dst][3] == path):
                logger.warning(
                    "core_sources: cannot add source[%d] to %s (different time base or quantity)",
                    i,
                    dst,
                )
                continue
            totals[dst][1] = totals[dst][1] + sign * power
            totals[dst][2].append(f"source[{i}]")
        else:
            totals[dst] = [times, sign * power, [f"source[{i}]"], path]
    for dst, (times, power, sources, path) in totals.items():
        src = f"core_sources/{'+'.join(sources)}/{path}"
        ctx.builder.set_signal(dst, times, power, src)


def launcher_signal(
    ids: IDSNode, launcher: IDSNode, field: str
) -> Optional[Tuple[Optional[np.ndarray], Union[np.ndarray, float]]]:
    """(times, data) of a launcher quantity, or None.

    Most quantities are {data, time} signals; a static value (e.g. the
    frequency of an LH antenna) is constant in time.
    """
    node = get_node(launcher, field)
    if node is None:
        return None
    if hasattr(node, "data"):
        if not node.data.has_value:
            return None
        return signal_times(ids, node), np.asarray(node.data)
    value = get_value(launcher, field)
    if value is None or np.ndim(value):
        return None
    return None, float(value)


def fill_launchers(ctx: Context) -> None:
    """Launched powers, frequencies and energies from the H&CD IDSs."""
    systems = [
        # (IDS, AoS names (DD4, DD3), summary AoS, summary total, extra fields)
        (
            "ec_launchers",
            ("beam", "launcher"),
            "ec",
            "power_launched_ec",
            ["frequency"],
        ),
        ("nbi", ("unit",), "nbi", "power_launched_nbi", ["energy"]),
        ("ic_antennas", ("antenna",), "ic", "power_launched_ic", ["frequency"]),
        ("lh_antennas", ("antenna",), "lh", "power_launched_lh", ["frequency"]),
    ]
    builder = ctx.builder
    for ids_name, aos_names, dst_aos, dst_total, extras in systems:
        ids = ctx.get(ids_name)
        if ids is None:
            continue
        aos_name = next((n for n in aos_names if get_node(ids, n) is not None), None)
        if aos_name is None:
            continue
        total = None
        for i, launcher in enumerate(getattr(ids, aos_name)):
            for field in ["power_launched", *extras]:
                signal = launcher_signal(ids, launcher, field)
                if signal is None:
                    continue
                times, data = signal
                values: Optional[Union[np.ndarray, float]]
                if times is None:  # static value
                    values, src = data, f"{ids_name}/{aos_name}[{i}]/{field}"
                else:
                    values = builder.interpolate(times, data)
                    src = f"{ids_name}/{aos_name}[{i}]/{field}/data"
                builder.set(f"heating_current_drive/{dst_aos}[{i}]/{field}", values, src)
                if field == "power_launched" and values is not None:
                    total = values if total is None else total + values
            if ids_name == "nbi":
                src = f"nbi/unit[{i}]/species"
                # species name in DD4, label in DD3
                for field in ("a", "z_n", "name", "label"):
                    builder.set(
                        f"heating_current_drive/nbi[{i}]/species/{field}",
                        get_value(launcher, f"species/{field}"),
                        src,
                    )
        builder.set(
            f"heating_current_drive/{dst_total}",
            total,
            f"{ids_name}/{aos_name}[:]/power_launched/data",
        )


# waves coherent_wave/identifier/type/index -> (launcher IDS, AoS names (DD4,
# DD3), summary AoS)
WAVE_SYSTEMS = {
    1: ("ec_launchers", ("beam", "launcher"), "ec"),
    2: ("ic_antennas", ("antenna",), "ic"),
    3: ("lh_antennas", ("antenna",), "lh"),
}


def fill_waves(ctx: Context) -> None:
    """Power coupled to the plasma by each EC/IC/LH launcher, from waves.

    Coherent waves are attributed to the launchers by antenna name; the
    power of the waves launched by the same antenna is summed.
    """
    waves = ctx.get("waves")
    if waves is None or not len(waves.coherent_wave):
        return
    builder = ctx.builder
    launchers: Dict[int, Tuple[str, Dict[str, int]]] = {}  # wave type -> (summary AoS, {launcher name: index})
    for type_index, (ids_name, aos_names, dst_aos) in WAVE_SYSTEMS.items():
        ids = ctx.get(ids_name)
        if ids is None:
            continue
        aos_name = next((n for n in aos_names if get_node(ids, n) is not None), None)
        if aos_name is None:
            continue
        by_name: Dict[str, int] = {}
        for i, launcher in enumerate(getattr(ids, aos_name)):
            name = str(get_value(launcher, "name") or "").strip()
            if name:
                by_name.setdefault(name, i)
        launchers[type_index] = (dst_aos, by_name)

    homogeneous = waves.ids_properties.homogeneous_time == imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
    # (summary AoS, launcher index) -> (power, wave indices), None if a wave
    # of the launcher does not cover the time base
    totals: Dict[Tuple[str, int], Optional[Tuple[np.ndarray, List[int]]]] = {}
    for j, wave in enumerate(waves.coherent_wave):
        system = launchers.get(get_value(wave, "identifier/type/index"))
        name = str(get_value(wave, "identifier/antenna_name") or "").strip()
        if system is None or name not in system[1] or not len(wave.global_quantities):
            continue
        key = (system[0], system[1][name])
        times = (
            np.asarray(waves.time, dtype=float)
            if homogeneous
            else [as_float(get_value(g, "time")) for g in wave.global_quantities]
        )
        power = [as_float(get_value(g, "power")) for g in wave.global_quantities]
        values = builder.interpolate(times, power)
        if values is None or (key in totals and totals[key] is None):
            totals[key] = None
            continue
        previous = totals.get(key)
        totals[key] = (values, [j]) if previous is None else (previous[0] + values, previous[1] + [j])
    for (dst_aos, i), entry in totals.items():
        if entry is None:
            continue
        waves_used = "+".join(f"coherent_wave[{j}]" for j in entry[1])
        builder.set(
            f"heating_current_drive/{dst_aos}[{i}]/power",
            entry[0],
            f"waves/{waves_used}/global_quantities/power",
        )


class GGDGrid:
    """Geometry of a 2D (poloidal) GGD grid needed for the summary."""

    def __init__(self, grid: IDSNode) -> None:
        self.grid = grid
        self.subsets = {int(s.identifier.index): s for s in grid.grid_subset}
        space = grid.space[0]
        self.nodes = np.array([obj.geometry[:2] for obj in space.objects_per_dimension[0].object])
        self.space = space

    @property
    def name(self) -> str:
        return self.grid.identifier.name

    def boundary_type(self) -> Optional[int]:
        """summary boundary/type from the grid type: 0 (limiter), 1 (diverted),
        11 (LSN), 12 (USN), 13 (DN), 14 (snowflake); None if unknown."""
        name = self.name.strip().lower()
        if name == "limiter":
            return 0
        if name.startswith(("cdn", "ddn")):
            return 13
        if "snowflake" in name:
            return 14
        if name == "sn":
            dimension, indices = self.subset_objects(GGD_X_POINTS)
            _, omp = self.subset_objects(GGD_OUTER_MIDPLANE_SEPARATRIX)
            if dimension == 1 and omp is not None:
                below = self.nodes[indices, 1].mean() < self.nodes[omp[0], 1]
                return 11 if below else 12
            return 1
        return None

    def subset_objects(self, index: int) -> Tuple[Optional[int], Optional[np.ndarray]]:
        """(dimension, 0-based object indices) of the elements of a subset."""
        subset = self.subsets.get(index)
        if subset is None or not len(subset.element):
            return None, None
        objects = [el.object[0] for el in subset.element]
        return int(objects[0].dimension), np.array([o.index - 1 for o in objects])

    def object_position(self, dimension: int, index: int) -> np.ndarray:
        """(r, z) of a node, or mean position of the nodes of an edge/cell."""
        if dimension == 1:
            return self.nodes[index]
        obj = self.space.objects_per_dimension[dimension - 1].object[index]
        return self.nodes[np.asarray(obj.nodes, dtype=int) - 1].mean(axis=0)

    def object_weights(self, dimension: int, indices: np.ndarray) -> np.ndarray:
        """Surface (edges) or volume (cells) of objects, up to a 2*pi factor."""
        objects = self.space.objects_per_dimension[dimension - 1].object
        measure = np.array([objects[i].measure for i in indices])
        r_centre = np.array([self.object_position(dimension, i)[0] for i in indices])
        return measure * r_centre

    def cell_volumes(self, subset_index: int = GGD_CELLS) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Volumes of the cells of a subset (toroidally symmetric grid)."""
        dimension, indices = self.subset_objects(subset_index)
        if dimension != 3 or indices is None:
            return None, None
        return indices, 2 * np.pi * self.object_weights(3, indices)


def resolve_grid(ctx: Context, ids: IDSNode, it: int = 0) -> Optional[GGDGrid]:
    """Return the GGD grid used by ``ids`` (following a grid_ggd path)."""
    if not len(ids.grid_ggd):
        return None
    grid = ids.grid_ggd[min(it, len(ids.grid_ggd) - 1)]
    if len(grid.space):
        return GGDGrid(grid)
    path = get_value(grid, "path")  # not in older DD 3 versions
    match = re.fullmatch(r"#(\w+)/grid_ggd\((\d+)\)", (path or "").strip())
    if match:
        other = ctx.get(match.group(1))
        index = int(match.group(2)) - 1
        if other is not None and index < len(other.grid_ggd):
            return GGDGrid(other.grid_ggd[index])
    return None


def subset_values(quantity_aos: IDSNode, subset_index: int) -> Optional[np.ndarray]:
    for item in quantity_aos:
        if item.grid_subset_index == subset_index and item.values.has_value:
            return np.asarray(item.values)
    return None


def fill_edge_profiles(ctx: Context, ids_name: str) -> None:
    """Separatrix and target values, strike points from GGD plasma profiles."""
    ids = ctx.get(ids_name)
    if ids is None or not len(ids.ggd):
        return
    times = ids_times(ids, "ggd")
    grid = resolve_grid(ctx, ids)
    if grid is None or times is None:
        return
    builder = ctx.builder

    # Values on the single-element grid subsets the code provides for these
    # locations (the separatrix average, a flux surface average, cannot be
    # computed from the GGD data alone and is not filled)
    locations = [
        (
            "local/separatrix",
            GGD_OUTER_MIDPLANE_SEPARATRIX,
            "outer midplane separatrix",
        ),
        (
            "local/divertor_target[0]",
            GGD_INNER_TARGET_SEPARATRIX,
            "inner target separatrix",
        ),
        (
            "local/divertor_target[1]",
            GGD_OUTER_TARGET_SEPARATRIX,
            "outer target separatrix",
        ),
    ]
    series: Dict[Tuple[str, str], List[float]] = {}
    for it, ggd in enumerate(ids.ggd):
        quantities = [
            ("t_e", "electrons/temperature", ggd.electrons.temperature),
            ("n_e", "electrons/density", ggd.electrons.density),
            ("t_i_average", "t_i_average", ggd.t_i_average),
            ("zeff", "zeff", ggd.zeff),
        ]
        ions = [(species_name(ion.element), f"ion[{i}]/density", ion.density) for i, ion in enumerate(ggd.ion)]
        for location, subset, description in locations:
            values: Dict[str, Tuple[str, Optional[np.ndarray]]] = {}
            for name, path, aos in quantities:
                values[name] = (path, subset_values(aos, subset))
            n_i_total = None
            for species, path, aos in ions:
                density = subset_values(aos, subset)
                if density is None:
                    continue
                n_i_total = density if n_i_total is None else n_i_total + density
                if species is not None:
                    values[f"n_i/{species}"] = (path, density)
            values["n_i_total"] = ("ion[:]/density", n_i_total)
            for name, (path, value) in values.items():
                if value is None or value.size != 1:
                    continue
                key = (
                    f"{location}/{name}",
                    f"{ids_name}/ggd/{path} (grid subset {subset}: {description})",
                )
                series.setdefault(key, [np.nan] * len(ids.ggd))[it] = value[0]
    for (dst, src), per_slice in series.items():
        builder.set_signal(dst, times, np.array(per_slice), src)
    for location, subset, description in locations:
        if location.startswith("local/divertor_target") and any(
            dst.startswith(location + "/") for dst in builder.filled
        ):
            builder.set(
                f"{location}/name",
                description,
                f"{ids_name}/grid_ggd (grid subset {subset})",
            )

    # Strike points (grid geometry)
    for side, subset in (
        ("inner", GGD_INNER_TARGET_SEPARATRIX),
        ("outer", GGD_OUTER_TARGET_SEPARATRIX),
    ):
        dimension, indices = grid.subset_objects(subset)
        if dimension is None or indices is None or indices.size != 1:
            continue
        r, z = grid.object_position(dimension, indices[0])
        src = f"{ids_name}/grid_ggd (grid subset {subset})"
        builder.set(f"boundary/strike_point_{side}_r", r, src)
        builder.set(f"boundary/strike_point_{side}_z", z, src)

    # Magnetic configuration from the grid type
    name = grid.name.strip()
    if name:
        src = f"{ids_name}/grid_ggd/identifier"
        builder.set("configuration", name.upper(), src)
        boundary_type = grid.boundary_type()
        if boundary_type is not None:
            # refine a plain "diverted" (e.g. from equilibrium) with the subtype
            current = builder.get("boundary/type")
            replace = current is not None and boundary_type > 1 and bool(np.all(current == 1))
            builder.set("boundary/type", boundary_type, src, replace=replace)


def species_emissivity(species: IDSNode) -> Optional[np.ndarray]:
    """Sum of the cell emissivities of a species (or of its states)."""
    values = subset_values(species.emissivity, GGD_CELLS)
    if values is None and hasattr(species, "state"):
        for state in species.state:
            state_values = subset_values(state.emissivity, GGD_CELLS)
            if state_values is not None:
                values = state_values if values is None else values + state_values
    return values


def fill_radiation(ctx: Context) -> None:
    rad = ctx.get("radiation")
    if rad is None or not len(rad.process):
        return
    builder = ctx.builder

    # Integrated powers provided by the code
    for path, field in (
        ("global_quantities/power_radiated_inside_lcfs", "inside_lcfs/power"),
        ("global_quantities/power_radiated_outside_lcfs", "outside_lcfs/power"),
    ):
        total, times = None, None
        for process in rad.process:
            if not len(process.global_quantities):
                continue
            power = np.array([as_float(get_value(g, field)) for g in process.global_quantities])
            times = (
                ids_times(rad)
                if rad.ids_properties.homogeneous_time == 1
                else (np.array([g.time for g in process.global_quantities]))
            )
            total = power if total is None else total + power
        builder.set_signal(path, times, total, f"radiation/process[:]/global_quantities/{field}")

    # Integration of the GGD emissivities on the cells
    grid = resolve_grid(ctx, rad)
    if grid is None:
        return
    cells, volumes = grid.cell_volumes()
    if cells is None or volumes is None:
        return
    core_cells = grid.subset_objects(GGD_CORE)[1]
    sol_cells = grid.subset_objects(GGD_SOL)[1]
    in_core = np.isin(cells, core_cells if core_cells is not None else np.array([], dtype=int))
    in_sol = np.isin(cells, sol_cells if sol_cells is not None else np.array([], dtype=int))
    n_times = max(len(p.ggd) for p in rad.process)
    times = ids_times(rad, "process[0]/ggd")
    if times is None or len(times) != n_times:
        return
    p_total, p_core, p_sol = (np.full(n_times, np.nan) for _ in range(3))
    for it in range(n_times):
        emissivity = np.zeros(cells.size)
        for process in rad.process:
            if it >= len(process.ggd):
                continue
            ggd = process.ggd[it]
            for species in [ggd.electrons] + list(ggd.ion) + list(ggd.neutral):
                values = species_emissivity(species)
                if values is not None and values.size == cells.size:
                    emissivity += values
        power = emissivity * volumes
        p_total[it], p_core[it], p_sol[it] = (
            power.sum(),
            power[in_core].sum(),
            power[in_sol].sum(),
        )
    src = "radiation/process[:]/ggd/*/emissivity integrated over the grid cells"
    if in_core.any():
        builder.set_signal(
            "global_quantities/power_radiated_outside_lcfs",
            times,
            p_total - p_core,
            src + " outside the core subset",
        )
    if in_sol.any():
        builder.set_signal("scrape_off_layer/power_radiated", times, p_sol, src + " of the SOL subset")


def fill_gas_injection(ctx: Context) -> None:
    gas = ctx.get("gas_injection")
    if gas is None:
        return
    builder = ctx.builder
    total = None
    by_species: Dict[str, np.ndarray] = {}
    for pipe in gas.pipe:
        if not pipe.flow_rate.data.has_value:
            continue
        values = builder.interpolate(signal_times(gas, pipe.flow_rate), pipe.flow_rate.data)
        if values is None:
            continue
        total = values if total is None else total + values
        if len(pipe.species) == 1:
            species = species_name(pipe.species[0].element)
            if species is not None:
                by_species[species] = by_species.get(species, 0) + values
    builder.set("gas_injection_rates/total", total, "gas_injection/pipe[:]/flow_rate")
    for species, values in by_species.items():
        builder.set(f"gas_injection_rates/{species}", values, "gas_injection/pipe[:]/flow_rate")


def fill_magnetics(ctx: Context) -> None:
    """Plasma current from the first magnetics method, as a last fallback."""
    mag = ctx.get("magnetics")
    if mag is None or not len(mag.ip) or not mag.ip[0].data.has_value:
        return
    ctx.builder.set_signal(
        "global_quantities/ip",
        signal_times(mag, mag.ip[0]),
        mag.ip[0].data,
        "magnetics/ip[0]",
    )


def fill_derived(ctx: Context) -> None:
    """Quantities derived from other summary quantities."""
    builder = ctx.builder
    coupled = [f"heating_current_drive/power_{s}" for s in ("nbi", "ec", "ic", "lh")]
    present = [p for p in coupled if builder.has(p)]
    if present:
        builder.set(
            "heating_current_drive/power_additional",
            sum(builder.value(p) for p in present),
            "summary/" + "+".join(present),
        )
    fill_single_launcher_powers(builder)
    fill_power_balance(builder)
    fill_confinement(builder)


def fill_single_launcher_powers(builder: SummaryBuilder) -> None:
    """Coupled power of a system with a single launcher: the system total."""
    for system in ("nbi", "ec", "ic", "lh"):
        total = f"heating_current_drive/power_{system}"
        aos = get_node(builder.ids, f"heating_current_drive/{system}")
        if builder.has(total) and aos is not None and len(aos) == 1:
            builder.set(
                f"heating_current_drive/{system}[0]/power",
                builder.value(total),
                f"summary/{total} (single launcher)",
            )


def fill_power_balance(builder: SummaryBuilder) -> None:
    """dW/dt, power_steady and power_loss (power through the separatrix).

    The heating powers all come from core_sources, so a source absent from
    it does not heat the plasma in the simulation and counts as zero.
    """
    time = builder.time
    if time.size < 2 or np.any(np.diff(time) <= 0):
        return
    if builder.has("global_quantities/energy_thermal"):
        builder.set(
            "global_quantities/denergy_thermal_dt",
            np.gradient(builder.value("global_quantities/energy_thermal"), time),
            "d/dt of summary/global_quantities/energy_thermal",
        )
    heating = [
        path
        for path in (
            "global_quantities/power_ohm",
            "heating_current_drive/power_additional",
            "fusion/power",
        )
        if builder.has(path)
    ]
    if not heating or not builder.has("global_quantities/denergy_thermal_dt"):
        return
    builder.set(
        "global_quantities/power_steady",
        sum(builder.value(path) for path in heating) - builder.value("global_quantities/denergy_thermal_dt"),
        "summary/(" + "+".join(heating) + ")-global_quantities/denergy_thermal_dt",
    )
    # radiation inside the separatrix: from the radiation IDS, else from the
    # core_sources radiation sinks (inside the core transport domain)
    radiated = next(
        (
            [path]
            for path in (
                "global_quantities/power_radiated_inside_lcfs",
                "global_quantities/power_radiated",
            )
            if builder.has(path)
        ),
        [
            path
            for path in (
                "global_quantities/power_bremsstrahlung",
                "global_quantities/power_synchrotron",
                "global_quantities/power_line",
            )
            if builder.has(path)
        ],
    )
    if builder.has("global_quantities/power_steady") and radiated:
        builder.set(
            "global_quantities/power_loss",
            builder.value("global_quantities/power_steady") - sum(builder.value(path) for path in radiated),
            "summary/global_quantities/power_steady-(" + "+".join(radiated) + ")",
        )


def tau_ipb98(
    ip: np.ndarray,
    b0: np.ndarray,
    r0: np.ndarray,
    r_geo: np.ndarray,
    a: np.ndarray,
    volume: np.ndarray,
    n_e: np.ndarray,
    p_loss: np.ndarray,
    meff: np.ndarray,
) -> np.ndarray:
    """IPB98(y,2) energy confinement time [s] (ITER Physics Basis, 1999).

    SI inputs; the toroidal field is taken at the geometric axis and the
    elongation is the area elongation volume / (2 pi^2 r_geo a^2).
    """
    kappa_a = volume / (2 * np.pi**2 * r_geo * a**2)
    return (
        0.0562
        * (np.abs(ip) / 1e6) ** 0.93
        * (np.abs(b0) * r0 / r_geo) ** 0.15
        * (n_e / 1e19) ** 0.41
        * (p_loss / 1e6) ** -0.69
        * r_geo**1.97
        * kappa_a**0.78
        * (a / r_geo) ** 0.58
        * meff**0.19
    )


def fill_confinement(builder: SummaryBuilder) -> None:
    """tau_energy, IPB98(y,2) scaling, h_98 and Greenwald fraction.

    tau_energy = energy_thermal / power_steady, the loss power of the
    IPB98(y,2) scaling (heating power minus dW/dt, radiation not subtracted).
    """
    gq = "global_quantities"

    def get(*paths: str) -> Optional[List[np.ndarray]]:
        if not all(builder.has(path) for path in paths):
            return None
        return [builder.value(path) for path in paths]

    def positive(value: ArrayLike) -> np.ndarray:
        value = np.asarray(value, dtype=float)
        return np.where(value > 0, value, np.nan)

    values = get(f"{gq}/energy_thermal", f"{gq}/power_steady")
    if values:
        energy, power = values
        builder.set(
            f"{gq}/tau_energy",
            energy / positive(power),
            f"summary/{gq}/energy_thermal / {gq}/power_steady",
        )
    values = get("line_average/n_e", f"{gq}/ip", "boundary/minor_radius")
    if values:
        n_e, ip, a = values
        builder.set(
            f"{gq}/greenwald_fraction",
            (n_e / 1e20) / positive(np.abs(ip) / 1e6 / (np.pi * a**2)),
            "summary/line_average/n_e / " f"(|{gq}/ip| [MA] / (pi boundary/minor_radius^2))",
        )
    inputs = (
        f"{gq}/ip",
        f"{gq}/b0",
        f"{gq}/r0",
        "boundary/geometric_axis_r",
        "boundary/minor_radius",
        f"{gq}/volume",
        "line_average/n_e",
        f"{gq}/power_steady",
        "volume_average/meff_hydrogenic",
    )
    values = get(*inputs)
    if values:
        values[7] = positive(values[7])
        builder.set(
            f"{gq}/tau_energy_98",
            tau_ipb98(*values),
            "IPB98(y,2) scaling of summary/" + ", ".join(inputs),
        )
    values = get(f"{gq}/tau_energy", f"{gq}/tau_energy_98")
    if values:
        builder.set(
            f"{gq}/h_98",
            values[0] / values[1],
            f"summary/{gq}/tau_energy / {gq}/tau_energy_98",
        )


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def is_netcdf(uri: str) -> bool:
    """True if ``uri`` is a netCDF file (same rule as imas.DBEntry)."""
    return uri.endswith(".nc") and not uri.startswith("imas:")


def entry_contents(entry: DBEntry) -> Set[str]:
    """Names of the IDSs (occurrence 0) present in the entry."""
    # IDS names differ between DD versions (e.g. dataset_description was
    # removed in DD 4.1): list the names of all DD 4 versions and of the
    # latest DD 3, as the entry may have been written with any of them
    names = set(entry.factory.ids_names())
    versions = imas.dd_zip.dd_xml_versions()
    dd3 = [v for v in versions if v.startswith("3.")]
    for version in [v for v in versions if v.startswith("4.")] + dd3[-1:]:
        names.update(imas.IDSFactory(version).ids_names())
    available = set()
    for name in sorted(names):
        try:
            if 0 in entry.list_all_occurrences(name):
                available.add(name)
        except Exception as exc:  # backends not supporting the query
            logger.debug("Could not list occurrences of %s: %s", name, exc)
    return available


def open_entry(uri: str, mode: str = "r", dd_version: Optional[str] = None) -> DBEntry:
    """Open a data entry, raising SummaryError if it cannot be opened."""
    try:
        return imas.DBEntry(uri, mode, dd_version=dd_version)
    except Exception as exc:  # e.g. unknown backend, missing or invalid file
        raise SummaryError(f"Could not open {uri}: {exc}") from exc


def has_summary(uri: str) -> bool:
    """True if the data entry holds a readable, non-empty summary IDS.

    The occurrence list alone is not enough: e.g. an HDF5 master file may
    still reference a summary whose data file is missing.
    """
    with open_entry(uri) as entry:
        try:
            if 0 not in entry.list_all_occurrences("summary"):
                return False
            summary = entry.get("summary", lazy=True, autoconvert=False)
            return summary.ids_properties.homogeneous_time.value != EMPTY_INT
        except Exception as exc:
            logger.info("No readable summary in the entry (%s)", exc)
            return False


def check_writable(uri: str, force: bool = False) -> None:
    """Raise SummaryError if a summary IDS cannot be written into the entry.

    An existing summary is only overwritten with ``force``, and never in a
    netCDF file, whose backend cannot overwrite an IDS.
    """
    if not has_summary(uri):
        return
    if is_netcdf(uri):
        raise SummaryError(f"{uri} already contains a summary IDS, which cannot be overwritten in a netCDF file")
    if not force:
        raise SummaryError(f"{uri} already contains a summary IDS (use --force, or force=True, to overwrite it)")


def entry_dd_version(entry: DBEntry, available: Set[str]) -> Optional[str]:
    """DD version the entry was written with (from version_put)."""
    for name in sorted(available):
        ids = entry.get(name, lazy=True, autoconvert=False)
        version = ids.ids_properties.version_put.data_dictionary.value
        if version:
            return version
    return None


def select_time_base(ctx: Context, requested: Optional[str]) -> Tuple[str, np.ndarray]:
    candidates = TIME_BASE_CANDIDATES
    if requested:
        candidates = [(requested, aos) for name, aos in TIME_BASE_CANDIDATES if name == requested] or [
            (requested, None)
        ]
    for name, aos in candidates:
        ids = ctx.get(name)
        if ids is None:
            continue
        times = ids_times(ids, aos)
        if times is not None and len(times) and np.all(np.isfinite(times)):
            logger.info("Time base: %s (%d time(s))", name, len(times))
            return name, times
    raise SummaryError(
        f"Could not determine a time base from {', '.join(n for n, _ in candidates)}" " (use --time-base)"
    )


def source_ids(sources: Iterable[str], available: Set[str]) -> List[str]:
    """Names of the IDSs of the entry referenced as paths in the source texts.

    Only IDSs present in the entry count, so that descriptive text in the
    sources (e.g. "d/dt of summary/...", "IPB98(y,2) scaling") is ignored.
    The summary quantities derived from other summary quantities add no IDS:
    their inputs record their own.
    """
    used = set()
    for source in sources:
        for name in re.findall(r"(?<![\w/])([a-z][a-z0-9_]*)/", source):
            if name in available:
                used.add(name)
    return sorted(used)


def set_provenance(summary: IDSNode, references: Sequence[str]) -> None:
    """Record the source IDSs in ids_properties/provenance (whole IDS)."""
    provenance = get_node(summary, "ids_properties/provenance/node")
    if provenance is None or not references:
        return
    provenance.resize(1)
    node = provenance[0]
    if hasattr(node, "reference"):
        node.reference.resize(len(references))
        for reference, name in zip(node.reference, references, strict=True):
            reference.name = name
    elif hasattr(node, "sources"):  # older DD 3 versions
        node.sources = references


FILLERS: List[Callable[[Context], None]] = [
    fill_vacuum_field,
    fill_equilibrium,
    fill_core_profiles,
    fill_core_sources,
    fill_launchers,
    fill_waves,
    lambda ctx: fill_edge_profiles(ctx, "edge_profiles"),
    lambda ctx: fill_edge_profiles(ctx, "plasma_profiles"),
    fill_radiation,
    fill_gas_injection,
    fill_magnetics,
    fill_derived,
]


def print_summary(builder: SummaryBuilder) -> None:
    """Print the filled summary quantities, their first values and sources."""
    time = builder.time
    print(f"Summary on {len(time)} time(s) [{time.min():g}, {time.max():g}] s, {len(builder.filled)} quantities:")
    for path, source in builder.filled.items():
        value = builder.value(path)
        shown = np.array2string(value.ravel()[:3], precision=4) if value.ndim else repr(value.item())
        print(f"  {path:55s} {shown:30s} <- {source}")


def build_summary(
    uri: str,
    time_base: Optional[str] = None,
    comment: Optional[str] = None,
    verbose: bool = False,
) -> IDSNode:
    """Build the summary IDS of a data entry, in memory.

    The data entry is only read: use write_summary() to write the summary.
    A summary IDS already present in the entry is ignored.

    Args:
        uri: IMAS URI of the data entry.
        time_base: IDS defining the summary time base (default: the first of
            TIME_BASE_CANDIDATES present in the entry).
        comment: summary ids_properties/comment (default: the list of IDSs
            the summary was built from).
        verbose: print the filled quantities, their first values and sources.

    Returns:
        The summary IDS, in the DD version of the entry. Its
        ids_properties/provenance references the IDSs of ``uri`` it was built
        from, also when it is written into another entry.

    Raises:
        SummaryError: if the summary cannot be built from the entry.

    Example:
        >>> summary = build_summary("imas:hdf5?path=/path/to/entry")
    """
    with open_entry(uri) as entry:
        available = entry_contents(entry)
        available.discard("summary")
        if not available:
            raise SummaryError(f"No IDS other than summary found in {uri}")
        dd_version = entry_dd_version(entry, available)
    if dd_version is None or dd_version.split(".")[0] not in SUPPORTED_DD_MAJOR:
        raise SummaryError(f"Only DD 3 and DD 4 entries are supported (found {dd_version})")
    if dd_version not in imas.dd_zip.dd_xml_versions():
        raise SummaryError(f"DD version {dd_version} is not available in IMAS-Python")
    logger.info("Entry DD version: %s, IDSs: %s", dd_version, ", ".join(sorted(available)))

    with open_entry(uri, dd_version=dd_version) as entry:
        ctx = Context(entry, uri, available)
        time_base_ids, time = select_time_base(ctx, time_base)
        builder = SummaryBuilder(entry.factory.summary(), time)
        ctx.builder = builder
        fillers = [lambda ctx: fill_metadata(ctx, time_base_ids)] + FILLERS
        for filler in fillers:
            try:
                filler(ctx)
            except Exception:
                logger.exception("Filler failed, continuing with the next one")

    summary = builder.ids
    used = source_ids(builder.filled.values(), available)
    summary.ids_properties.comment = comment or f"Generated by create_summary from: {', '.join(used)}"
    set_provenance(summary, [f"{uri}#{name}" for name in used])
    summary.validate()
    if verbose:
        print_summary(builder)
    return summary


def write_summary(summary: IDSNode, uri: str, force: bool = False) -> None:
    """Write a summary IDS into an existing data entry.

    The summary is written in its own DD version, which must have the same
    major version as the other IDSs of the entry.

    Args:
        summary: the summary IDS, e.g. from build_summary().
        uri: IMAS URI of the data entry.
        force: overwrite the summary IDS if the entry already holds one.

    Raises:
        SummaryError: if the entry cannot be opened, already holds a summary
            (and ``force`` is not given, or the entry is a netCDF file), uses
            another DD major version, or if the summary is not valid.

    Example:
        >>> write_summary(build_summary(uri), uri)
    """
    check_writable(uri, force)
    dd_version = imas.util.get_data_dictionary_version(summary)
    with open_entry(uri) as entry:
        available = entry_contents(entry)
        available.discard("summary")
        entry_version = entry_dd_version(entry, available) if available else None
    if entry_version is not None and entry_version != dd_version:
        if entry_version.split(".")[0] != dd_version.split(".")[0]:
            raise SummaryError(f"Cannot write a DD {dd_version} summary into {uri}, written with DD {entry_version}")
        logger.warning("Writing a DD %s summary into %s, written with DD %s", dd_version, uri, entry_version)
    try:
        summary.validate()
    except Exception as exc:
        raise SummaryError(f"Invalid summary IDS: {exc}") from exc
    with open_entry(uri, "a", dd_version=dd_version) as entry:
        entry.put(summary)
