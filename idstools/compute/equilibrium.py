"""
This module provides compute functions and classes for equilibrium ids data

`refer data dictionary <https://imas-data-dictionary.readthedocs.io/en/latest/>`_.

"""

import logging
from typing import Union

try:
    import imaspy as imas
except ImportError:
    import imas
import numpy as np

from idstools.compute.common import get_compat_attr
from idstools.database import DBMaster

_IDS_VALID_THRESHOLD = abs(imas.ids_defs.EMPTY_FLOAT)

logger = logging.getLogger("module")


class EquilibriumCompute:
    """This class provides compute functions for equilibrium ids.

    Attributes:
        ids (object): The equilibrium IDS (Integrated Data Structure) object containing
            time-resolved equilibrium data including profiles, magnetic field information,
            constraints, and boundary information.
    """

    def __init__(self, ids: object):
        """Initialization EquilibriumCompute object.

        Args:
            ids : equilibrium ids object
        """
        self.ids = ids

    def get2d_cartesian_grid(self, time_slice: int, profiles2d_index: int = 0) -> Union[dict, None]:
        """
        This function returns a dictionary containing 2D Cartesian grid coordinates and psi values from
        an equilibrium IDS object.

        Args:
            time_slice (int): The time slice index of the equilibrium data to be used for generating the
            2D Cartesian grid. Defaults to 0
            profiles2d_index (int): An integer parameter that represents the index of the
            ``profiles_2d`` to be used in the calculation. It is used to access the specific 2D profile from the
            list of profiles in the `time_slice` object. Defaults to 0

        Returns:
            A dictionary containing the 2D Cartesian grid coordinates (r2d and z2d) and the corresponding psi
            values (psi2d), or None if the data is unavailable or invalid.

        Example:
            .. code-block:: python

            import imas
            connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3","r")
            idsObj = connection.get('equilibrium')
            computeObj = EquilibriumCompute(idsObj)
            result = computeObj.get2d_cartesian_grid(time_slice=0)

            {'r2d': array([...]), 'z2d': array([...]), 'psi2d': array([...])}
        """
        profiles2d = r1d = z1d = None
        try:
            profiles2d = self.ids.time_slice[time_slice].profiles_2d[profiles2d_index]
        except IndexError:
            logger.error(f"equilibrium.time_slice[{time_slice}].profiles_2d[{profiles2d_index}] is not available")
            return None

        profiles2d = self.ids.time_slice[time_slice].profiles_2d[profiles2d_index]

        if profiles2d.grid_type.index == 1 and profiles2d.grid.dim1 is not None and profiles2d.grid.dim2 is not None:
            logger.info(
                f"Using equilibrium.time_slice[{time_slice}]"
                f".profiles_2d[{profiles2d_index}].grid.dim1/dim2 for the 2D grid"
            )
            r1d = profiles2d.grid.dim1
            z1d = profiles2d.grid.dim2
        else:
            logger.error("Only rectangular cylindrical grid (grid_type=1) is supported for now")
            return None

        psi2d = profiles2d.psi

        if np.all(psi2d == 0.0):
            logger.error(
                "All values of psi2d are 0. No contour levels were found within the data range, Can not plot contour"
            )
            return None

        return {"r2d": r1d, "z2d": z1d, "psi2d": psi2d}

    def get_phi2d(self, time_slice: int, profiles2d_index: int = 0) -> Union[np.ndarray, None]:
        """
        Returns the toroidal magnetic flux Φ(R,Z) on the 2D grid.

        Reads ``equilibrium.time_slice[i].profiles_2d[j].phi`` directly from the IDS.

        Args:
            time_slice (int): Index of the time slice in the equilibrium IDS. Defaults to 0.
            profiles2d_index (int): Index into ``profiles_2d`` from which
                ``phi`` (toroidal flux, Wb) is read. Defaults to 0.

        Returns:
            np.ndarray or None: 2-D array of toroidal flux Φ [Wb] with the same shape as
            the ``profiles_2d`` grid, or None if ``phi`` is unavailable or all-NaN.

        Examples:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3", "r")
                idsObj = connection.get('equilibrium')
                computeObj = EquilibriumCompute(idsObj)
                result = computeObj.get_phi2d(time_slice=0)

        """
        phi = None
        try:  # using https://docs.python.org/2/glossary.html#term-eafp style
            phi = self.ids.time_slice[time_slice].profiles_2d[profiles2d_index].phi
            if len(phi) == 0:
                logger.error(f"equilibrium.time_slice[{time_slice}].profiles_2d[{profiles2d_index}].phi not available")
                return None
        except IndexError:
            logger.error(f"equilibrium.time_slice[{time_slice}].profiles_2d[{profiles2d_index}].phi not available")
            return None
        if np.isnan(phi).all() is True:
            logger.error(
                f"all values are nan for equilibrium.time_slice[{time_slice}].profiles_2d[{profiles2d_index}].phi "
            )
            return None
        return phi

    def get_b_total(self, time_slice: int) -> tuple:
        """
        This function calculates the total magnetic field strength at a given time slice based on the radial,
        vertical, and toroidal components of the magnetic field.

        Args:
            time_slice (int): time_slice is an integer parameter representing the index of the time slice for which
                the magnetic field is being calculated from profiles 2D.

        Returns:
            Index in `profiles_2d`
            Array of total magnetic field strength (bTotal) at a given time slice, calculated using the square
            root of the sum of the squares of the radial, vertical, and toroidal components of the magnetic field.
            If there are no profiles available for the given time slice, the function returns None.

        Examples:
            .. code-block:: python

            import imas
            connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3", "r")
            idsObj = connection.get('equilibrium')
            computeObj = EquilibriumCompute(idsObj)
            indices = idsobj.get_b_total(time_slice=0)
            (0, array([[10.99503929

        Notes:

            .. math:: bTotal = \\sqrt{b\\_field\\_r^2 + b\\_field\\_z^2 + b\\_field\\_tor^2}

            ``profiles_2d`` has information about following fields
            ``b_field_r`` (R component of the poloidal magnetic field)
            ``b_field_z`` (Z component of the poloidal magnetic field)
            ``b_field_tor`` (Toroidal component of the magnetic field)

        """
        list_of_profiles = self.get2d_profiles_indices(time_slice)
        b_total = None
        profile2d_index = -99

        if list_of_profiles is not None:
            # TODO Check if we should always pick up first profile
            profile2d_index = list_of_profiles[0]
            b_field_tor = get_compat_attr(
                self.ids.time_slice[time_slice].profiles_2d[profile2d_index], "b_field_tor", "b_field_phi"
            )

            b_total = np.sqrt(
                self.ids.time_slice[time_slice].profiles_2d[profile2d_index].b_field_r ** 2
                + self.ids.time_slice[time_slice].profiles_2d[profile2d_index].b_field_z ** 2
                + b_field_tor**2
            )
        else:
            print("------------------------------------------------")
            print("No rectangular R,Z grid found in equilibrium IDS")
            print("--> Abort.")
            print("------------------------------------------------")
        return profile2d_index, b_total

    def get2d_profiles_indices(self, time_slice: int, grid_type: int = 1) -> list:
        """Return the indices of ``profiles_2d`` of the specified grid type

        Args:
            time_slice (int): time slice index
            grid_type (int, optional): grid type. Defaults to 1.

        Returns:
            list: list of indices of the 2D profiles at a given time slice. If no such 2D profiles are found,
            it returns None

        Raises:
            AttributeError: The ``Raises`` section is a list of all exceptions that are relevant to the interface.

        Notes:
            Multiple 2D representations of the equilibrium are stored in ``profiles_2d``.
            Various grid types are available like rectangular, inverse etc. read more on profiles_2d(i1) section

        See also:
            :meth:`getFluxSurfaces`
            :meth:`getBTotal`

        Examples:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3","r")
                idsObj = connection.get('equilibrium')
                computeObj = EquilibriumCompute(idsObj)
                indices = idsobj.get2d_profiles_indices(time_slice=0, gridType=1)

                [0]
        """
        return [
            index
            for index in range(len(self.ids.time_slice[time_slice].profiles_2d))
            if self.ids.time_slice[time_slice].profiles_2d[index].grid_type.index == grid_type
        ] or None

    def get_flux_surfaces(self, time_slice: int) -> dict:
        """
        This function returns a dictionary containing 2D profiles and rho values for a given time slice.

        Args:
            time_slice (int): The time slice parameter represents the time step at which the flux surfaces are to
                be calculated.

        Returns:
            a dictionary containing information about flux surfaces at a specific time slice. The dictionary includes
            a 2D Cartesian grid, a 2D profile index, and a 2D array of rho_tor_norm [-] values (dimensionless,
            range [0, 1]). If no profiles are found, the function returns None.
        """
        GRID_TYPE_RECTANGULAR = 1
        list_of_profiles = self.get2d_profiles_indices(time_slice, GRID_TYPE_RECTANGULAR)
        if list_of_profiles is None:
            return None

        logger.debug(f"list Of rectangualar profiles found : {list_of_profiles}")
        profile2d_index = list_of_profiles[0]

        result_dict = self.get2d_cartesian_grid(time_slice, profile2d_index)
        phi2d = self.get_phi2d(time_slice, profile2d_index)
        if phi2d is None:
            phi2d = []
        result_dict["phi2d"] = phi2d
        return result_dict

    def get_ip(self) -> list:
        """
        This function returns a list of Plasma current (toroidal component) values for each time slice.

        Returns:
            a list of plasma currents for each time slice in `self.ids.time_slice`. The plasma current is
            calculated by multiplying the global quantity `ip` by -1.0e-6.

        Examples:
            .. code-block:: python

                import imas
                connection = imas.DBEntry("imas:mdsplus?user=public;pulse=134173;run=106;database=ITER;version=3","r")
                idsObj = connection.get('equilibrium')
                computeObj = EquilibriumCompute(idsObj)
                result = computeObj.getIP()

                array([[]])
        """
        return [
            -self.ids.time_slice[time_index].global_quantities.ip * 1.0e-6
            for time_index in range(len(self.ids.time_slice))
        ]

    def get_boundary_data(self, time_slice: int) -> dict:
        """Return boundary data for a given time slice.

        Reads ``boundary/outline``, ``boundary_separatrix`` (DD3), or
        ``contour_tree`` (DD4) for the separatrix outline, X-points, and
        strike-points. If the separatrix is still missing, falls back to
        ``boundary/outline`` for diverted plasmas (``type==1``) or
        ``boundary/lcfs`` for limiter/unknown.

        Returns a dict with keys ``bnd_r``, ``bnd_z``, ``bnd_type``,
        ``bnd_psi_norm``, ``bnd_geom_r``, ``bnd_geom_z``, ``sep_r``,
        ``sep_z``, ``sep_xpoints``, ``sep_strikepoints``.
        """

        def _valid_arr(arr):
            a = np.asarray(arr, dtype=float)
            return a.size > 0 and np.any(np.isfinite(a) & (np.abs(a) < _IDS_VALID_THRESHOLD))

        def _valid_scalar(val):
            try:
                v = float(val)
                return np.isfinite(v) and abs(v) < _IDS_VALID_THRESHOLD
            except Exception as exc:
                logger.debug(f"get_boundary_data: invalid scalar {val!r} ({exc})")
                return False

        def _clean(arr):
            a = np.array(arr, dtype=float, copy=True)
            a[(~np.isfinite(a)) | (np.abs(a) >= _IDS_VALID_THRESHOLD)] = np.nan
            return a

        def _read_outline(node):
            try:
                r = np.asarray(node.outline.r, dtype=float)
                z = np.asarray(node.outline.z, dtype=float)
            except Exception as exc:
                logger.debug(f"get_boundary_data: could not read outline from {node!r}: {exc}")
                return None
            if not (_valid_arr(r) and _valid_arr(z)):
                logger.debug("get_boundary_data: outline has no valid data " f"(r.size={r.size}, z.size={z.size})")
                return None
            r, z = _clean(r), _clean(z)
            # Insert NaN at large jumps so disconnected arcs are not joined
            dist = np.sqrt(np.diff(r) ** 2 + np.diff(z) ** 2)
            median_dist = np.nanmedian(dist)
            if median_dist > 0:
                breaks = np.where(dist > 20.0 * median_dist)[0] + 1
                if len(breaks):
                    r = np.insert(r, breaks, np.nan)
                    z = np.insert(z, breaks, np.nan)
            return (r, z)

        def _read_points(node, attr, ids_path):
            pts = []
            try:
                arr = getattr(node, attr)
            except AttributeError:
                logger.debug(f"get_boundary_data: {ids_path}/{attr} is not available")
                return pts
            except Exception as exc:
                logger.debug(f"get_boundary_data: could not access {ids_path}/{attr}: {exc}")
                return pts
            try:
                n_points = len(arr)
            except Exception as exc:
                logger.debug(f"get_boundary_data: could not get length of {ids_path}/{attr}: {exc}")
                n_points = None
            for pt_index, pt in enumerate(arr):
                try:
                    r, z = float(pt.r), float(pt.z)
                except Exception as exc:
                    logger.debug(f"get_boundary_data: could not read {ids_path}/{attr}[{pt_index}]/r|z: {exc}")
                    continue
                if _valid_scalar(r) and _valid_scalar(z):
                    pts.append((r, z))
                else:
                    logger.debug(f"get_boundary_data: {ids_path}/{attr}[{pt_index}]/r|z invalid ({r}, {z})")
            logger.debug(f"get_boundary_data: {ids_path}/{attr} — read {len(pts)} valid points out of {n_points}")
            return pts

        def _read_contour_tree(ts_node):
            """Read separatrix/X-point data from ``time_slice.contour_tree.node``.

            * ``node.critical_type == 1`` for X-points (saddle points)
            * first valid X-point ``node.levelset.r/z`` as separatrix contour
            """
            sep_outlines = []
            xpoints = []

            nodes = ts_node.contour_tree.node
            n_nodes = len(nodes)
            n_saddles = 0
            for node_index, node in enumerate(nodes):
                try:
                    critical_type = int(node.critical_type)
                except Exception as exc:
                    logger.debug(
                        f"get_boundary_data: could not read contour_tree.node[{node_index}].critical_type: {exc}"
                    )
                    continue

                if critical_type != 1:  # 1 = saddle / X-point
                    continue
                n_saddles += 1

                try:
                    xr = float(node.r)
                    xz = float(node.z)
                except Exception as exc:
                    logger.debug(f"get_boundary_data: could not read contour_tree.node[{node_index}].r/z: {exc}")
                    xr = xz = None

                if xr is not None and _valid_scalar(xr) and xz is not None and _valid_scalar(xz):
                    xpoints.append((xr, xz))
                else:
                    logger.debug(
                        f"get_boundary_data: contour_tree.node[{node_index}] saddle has invalid r/z " f"({xr}, {xz})"
                    )

                # if sep_r is not None and sep_z is not None:
                #    continue

                try:
                    r = np.asarray(node.levelset.r, dtype=float)
                    z = np.asarray(node.levelset.z, dtype=float)
                except Exception as exc:
                    logger.debug(
                        f"get_boundary_data: could not read contour_tree.node[{node_index}].levelset.r/z: {exc}"
                    )
                    continue

                if not (_valid_arr(r) and _valid_arr(z)):
                    logger.debug(
                        f"get_boundary_data: contour_tree.node[{node_index}].levelset has no valid data "
                        f"(r.size={r.size}, z.size={z.size})"
                    )
                    continue

                if r is not None and z is not None:
                    sep_outlines.append((_clean(r), _clean(z)))

            logger.debug(
                "get_boundary_data: contour_tree summary "
                f"(nodes={n_nodes}, saddles={n_saddles}, xpoints={len(xpoints)}, "
                f"has_separatrix={len(sep_outlines) > 0})"
            )

            return sep_outlines, xpoints

        result = {
            "bnd_outline": None,
            "bnd_type": None,
            "bnd_psi_norm": None,
            "bnd_geom_axis": None,
            "sep_outlines": [],
            "sep_xpoints": [],
            "sep_strikepoints": [],
        }

        try:
            ts = self.ids.time_slice[time_slice]
        except Exception as exc:
            logger.debug(f"get_boundary_data: could not access time_slice[{time_slice}]: {exc}")
            return result

        # boundary
        try:
            bnd = ts.boundary
            result["bnd_outline"] = _read_outline(bnd)
            result["sep_xpoints"] = _read_points(bnd, "x_point", f"time_slice[{time_slice}]/boundary")
            result["sep_strikepoints"] = _read_points(bnd, "strike_point", f"time_slice[{time_slice}]/boundary")
            logger.debug(
                f"get_boundary_data: time_slice[{time_slice}]/boundary summary "
                f"(has_outline={result['bnd_outline'] is not None}, "
                f"xpoints={len(result['sep_xpoints'])}, strikepoints={len(result['sep_strikepoints'])})"
            )

            bnd_type = int(bnd.type)
            if _valid_scalar(bnd_type):
                result["bnd_type"] = bnd_type
        except Exception as exc:
            logger.debug(f"get_boundary_data: could not read time_slice[{time_slice}]/boundary: {exc}")

        try:
            psi_norm = float(ts.boundary.psi_norm)
            if _valid_scalar(psi_norm):
                result["bnd_psi_norm"] = psi_norm
        except Exception as exc:
            logger.debug(f"get_boundary_data: could not read time_slice[{time_slice}]/boundary/psi_norm: {exc}")

        try:
            gax_r = float(ts.boundary.geometric_axis.r)
            gax_z = float(ts.boundary.geometric_axis.z)
            if _valid_scalar(gax_r) and _valid_scalar(gax_z):
                result["bnd_geom_axis"] = (gax_r, gax_z)
        except Exception as exc:
            logger.debug(
                f"get_boundary_data: could not read time_slice[{time_slice}]/boundary/geometric_axis/r|z: {exc}"
            )

        # boundary_separatrix (DD3 )
        if hasattr(ts, "boundary_separatrix"):
            sep = ts.boundary_separatrix
            try:
                sep_outline = _read_outline(sep)
                if sep_outline is not None:
                    (result["sep_outlines"]).append(sep_outline)
                sep_xpoints = _read_points(sep, "x_point", f"time_slice[{time_slice}]/boundary_separatrix")
                for xp in sep_xpoints:
                    (result["sep_xpoints"]).append(xp)
                sep_strikepoints = _read_points(sep, "strike_point", f"time_slice[{time_slice}]/boundary_separatrix")
                for sp in sep_strikepoints:
                    (result["sep_strikepoints"]).append(sp)
                logger.debug(
                    f"get_boundary_data: time_slice[{time_slice}]/boundary_separatrix summary "
                    f"(has_outline={len(result['sep_outlines']) > 0}, "
                    f"xpoints={len(sep_xpoints)}, strikepoints={len(sep_strikepoints)})"
                )
            except Exception as exc:
                logger.debug(f"get_boundary_data: could not read time_slice[{time_slice}]/boundary_separatrix: {exc}")

        # boundary_secondary_separatrix (DD3 )
        if hasattr(ts, "boundary_secondary_separatrix"):
            sep = ts.boundary_secondary_separatrix
            try:
                sep_outline = _read_outline(sep)
                if sep_outline is not None:
                    (result["sep_outlines"]).append(sep_outline)
                sep_xpoints = _read_points(sep, "x_point", f"time_slice[{time_slice}]/boundary_secondary_separatrix")
                for xp in sep_xpoints:
                    (result["sep_xpoints"]).append(xp)
                sep_strikepoints = _read_points(
                    sep, "strike_point", f"time_slice[{time_slice}]/boundary_secondary_separatrix"
                )
                for sp in sep_strikepoints:
                    (result["sep_strikepoints"]).append(sp)
                logger.debug(
                    f"get_boundary_data: time_slice[{time_slice}]/boundary_secondary_separatrix summary "
                    f"(has_outline={len(result['sep_outlines']) > 1}, "
                    f"xpoints={len(sep_xpoints)}, strikepoints={len(sep_strikepoints)})"
                )
            except Exception as exc:
                logger.debug(
                    f"get_boundary_data: could not read time_slice[{time_slice}]/boundary_secondary_separatrix: {exc}"
                )

        #  contour_tree.node (DD4)
        if hasattr(ts, "contour_tree") and hasattr(ts.contour_tree, "node"):
            contour_sep, contour_xpoints = _read_contour_tree(ts)

            for sep in contour_sep:
                (result["sep_outlines"]).append(sep)

            for xp in contour_xpoints:
                (result["sep_xpoints"]).append(xp)

        # Separatrix fallback when boundary_separatrix / contour_tree provided nothing.
        if len(result["sep_outlines"]) < 0:
            if result["bnd_type"] == 1:
                # type=1 (diverted): boundary/outline IS the separatrix — reuse directly.
                if result["bnd_outline"] is not None:
                    result["sep_outlines"] = [result["bnd_outline"]]
                    logger.debug(
                        f"get_boundary_data: time_slice[{time_slice}]/boundary/outline/r|z "
                        f"— sep outline reused (type=1 diverted)"
                    )
            else:
                # type=0 (limiter) or unknown: outline is the limiter contour, not the LCFS.
                # Fall back to boundary/lcfs
                try:
                    r_raw = np.asarray(ts.boundary.lcfs.r, dtype=float)
                    z_raw = np.asarray(ts.boundary.lcfs.z, dtype=float)
                    mask = r_raw > 0
                    r_raw, z_raw = _clean(r_raw[mask]), _clean(z_raw[mask])
                    if r_raw.size > 0:
                        result["sep_outlines"] = [(r_raw, z_raw)]
                        logger.debug(
                            f"get_boundary_data: time_slice[{time_slice}]/boundary/lcfs/r|z "
                            f"— sep outline filled (type=2 limiter)"
                        )
                except Exception as exc:
                    logger.debug(f"get_boundary_data: could not read time_slice[{time_slice}]/boundary/lcfs/r|z: {exc}")

        logger.debug(
            "get_boundary_data: final summary "
            f"(has_boundary={result['bnd_outline'] is not None}, "
            f"has_separatrix={len(result['sep_outlines']) > 0}, "
            f"xpoints={len(result['sep_xpoints'])}, strikepoints={len(result['sep_strikepoints'])})"
        )

        return result

    def get_magnetic_axis(self, time_slice: int) -> Union[dict, None]:
        """Return the magnetic axis position for a given time slice.

        Reads ``global_quantities.magnetic_axis.r/z`` and validates the
        scalar values.

        Args:
            time_slice (int): Index into ``time_slice``.

        Returns:
            dict with scalar keys ``"r"`` and ``"z"`` (floats), or
            ``None`` if the data are absent or invalid.
        """
        try:
            mag_ax = self.ids.time_slice[time_slice].global_quantities.magnetic_axis
            r = float(mag_ax.r)
            z = float(mag_ax.z)
        except Exception as exc:
            logger.debug(f"get_magnetic_axis: could not read magnetic_axis – {exc}")
            return None

        def _valid(val):
            return np.isfinite(val) and abs(val) < _IDS_VALID_THRESHOLD

        if not (_valid(r) and _valid(z)):
            logger.debug("get_magnetic_axis: magnetic_axis contains no valid data")
            return None

        return {"r": r, "z": z}

    def get_current_centre(self, time_slice: int) -> Union[dict, None]:
        """Return the current centroid position for a given time slice.

        Reads ``global_quantities.current_centre.r/z`` and validates the
        scalar values.

        Args:
            time_slice (int): Index into ``time_slice``.

        Returns:
            dict with scalar keys ``"r"`` and ``"z"`` (floats), or
            ``None`` if the data are absent or invalid.
        """
        try:
            cc = self.ids.time_slice[time_slice].global_quantities.current_centre
            r = float(cc.r)
            z = float(cc.z)
        except Exception as exc:
            path = f"time_slice[{time_slice}]/global_quantities/current_centre/r|z"
            logger.debug(f"get_current_centre: could not read {path} – {exc}")
            return None

        def _valid(val):
            return np.isfinite(val) and abs(val) < _IDS_VALID_THRESHOLD

        if not (_valid(r) and _valid(z)):
            path = f"time_slice[{time_slice}]/global_quantities/current_centre/r|z"
            logger.debug(f"get_current_centre: {path} contains no valid data")
            return None

        return {"r": r, "z": z}

    def get_scalar_annotation_quantities(self, time_slice: int) -> list:
        """Return validated scalar global/boundary quantities for annotation display.

        Reads a fixed set of scalar fields from ``global_quantities`` and
        ``boundary``, validates each value (finite and below the IDS fill
        value threshold), and returns
        only those with valid data.

        Args:
            time_slice (int): Index into ``time_slice``.

        Returns:
            list of dicts, each with ``"label"`` (LaTeX str) and ``"text"``
            (formatted value + unit str).  Empty list if nothing is valid.
        """

        def _valid(val):
            try:
                v = float(val)
                return np.isfinite(v) and abs(v) < _IDS_VALID_THRESHOLD
            except Exception:
                return False

        items = []
        ts = self.ids.time_slice[time_slice]
        gq = ts.global_quantities
        bnd = ts.boundary

        _specs = [
            (lambda: float(gq.ip), lambda v: {"label": "$I_p$", "text": f"{v / 1e6:.3f} MA"}),
            (
                lambda: float(
                    getattr(
                        gq.magnetic_axis, "b_field_phi" if hasattr(gq.magnetic_axis, "b_field_phi") else "b_field_tor"
                    )
                ),
                lambda v: {"label": r"$B_\phi$(axis)", "text": f"{v:.3f} T"},
            ),
            (lambda: float(gq.psi_axis), lambda v: {"label": r"$\psi_{\rm axis}$", "text": f"{v:.4g} Wb"}),
            (lambda: float(gq.psi_boundary), lambda v: {"label": r"$\psi_{\rm bnd}$", "text": f"{v:.4g} Wb"}),
            (lambda: float(gq.q_axis), lambda v: {"label": "$q_0$", "text": f"{v:.3f}"}),
            (lambda: float(gq.q_95), lambda v: {"label": "$q_{95}$", "text": f"{v:.3f}"}),
            (lambda: float(bnd.minor_radius), lambda v: {"label": "$a$", "text": f"{v:.3f} m"}),
            (lambda: float(bnd.elongation), lambda v: {"label": r"$\kappa$", "text": f"{v:.3f}"}),
            (lambda: float(bnd.triangularity), lambda v: {"label": r"$\delta$", "text": f"{v:.3f}"}),
        ]
        for getter, formatter in _specs:
            try:
                val = getter()
                if _valid(val):
                    items.append(formatter(val))
            except Exception:
                pass
        return items

    def get_top_view(self, time_slice: int) -> dict:
        """
        The function returns data for plotting the top view of a 2D shape.

        Args:
            time_slice (int): time_slice is an index of time_slice. If not specified, it defaults to 0. Defaults to 0

        Returns:
            The function `get_top_view` returns a dictionary `topViewDict` containing the following keys

            - "r0": the geometric axis r of the boundary at the given `time_slice`
            - "amin": the minor radius of the boundary at the given `time_slice`
            - "phit": an array of 100 evenly spaced values between 0 and 2 * pi
            - "xpla": left x-coordinate of a point in polar coordinates
            - "ypla": left y-coordinate of a point in polar coordinates
            - "xplap": right x-coordinate of a point in polar coordinates
            - "yplap": right y-coordinate of a point in polar coordinates

        """
        # TODO Correct documentation and naming of return variables
        top_view_dict = {}
        top_view_dict["r0"] = r0 = self.ids.time_slice[time_slice].boundary.geometric_axis.r
        top_view_dict["amin"] = amin = self.ids.time_slice[time_slice].boundary.minor_radius
        top_view_dict["phit"] = phit = np.linspace(0, 2 * np.pi, 100)
        top_view_dict["xpla"] = (r0 - amin) * np.cos(phit)
        top_view_dict["ypla"] = (r0 - amin) * np.sin(phit)
        top_view_dict["xplap"] = (r0 + amin) * np.cos(phit)
        top_view_dict["yplap"] = (r0 + amin) * np.sin(phit)
        return top_view_dict

    def getmrho(self, time_slice: int):
        """
        This function calculates the number of elements in a list that are less than zero.

        Args:
            time_slice (int): The `time_slice` parameter

        Returns:
            The function `getmrho` is returning the number of elements in the `rho_tor_norm` list that are
            less than 0.
        """
        mrho = 0
        for i in range(len(self.ids.time_slice[time_slice].profiles_1d.rho_tor_norm)):
            if self.ids.time_slice[time_slice].profiles_1d.rho_tor_norm[i] < 0:
                mrho = mrho + 1

        return mrho

    def getgm3(self, r, time_slice: int):
        """
        The function `getgm3` calculates and returns a value based on interpolation and division
        operations.

        Args:
            r: The `r` parameter in the `getgm3` function represents the radial coordinate at which you
                want to calculate the value of `gm3`. This function interpolates the value of `gm3` at the
                specified radial coordinate `r` based on the provided data.
            time_slice (int): The `time_slice` parameter

        Returns:
            The function `getgm3` returns the value of `gm3`, which is calculated based on the input
            parameters `r` and `time_slice`. The calculation involves interpolation of
            `time_slice[time_slice].profiles_1d.gm3` based on `r` and normalization by
            `rho_tor_sep` squared.
        """
        rho_tor_sep = self.ids.time_slice[time_slice].profiles_1d.rho_tor[time_slice]
        gm3 = (
            np.interp(
                r,
                self.ids.time_slice[time_slice].profiles_1d.rho_tor_norm,
                self.ids.time_slice[time_slice].profiles_1d.gm3,
            )
            / rho_tor_sep**2
        )
        return gm3

    def getgm7(self, r, time_slice: int):
        """
        The function `getgm7` calculates and returns the normalized value of gm7 at a given radial
        position `r` for a specific time slice.

        Args:
            r: The `r` parameter in the `getgm7` method is used as the input radial coordinate for which
                you want to calculate the value of `gm7`.
            time_slice (int): The `time_slice` parameter

        Returns:
            The function `getgm7` returns the value of `gm7`, which is calculated based on the input
            parameters `r` and `time_slice`.
        """
        rho_tor_sep = self.ids.time_slice[time_slice].profiles_1d.rho_tor[time_slice]
        gm7 = (
            np.interp(
                r,
                self.ids.time_slice[time_slice].profiles_1d.rho_tor_norm,
                self.ids.time_slice[time_slice].profiles_1d.gm7,
            )
            / rho_tor_sep
        )
        return gm7

    def rescale(self, rescale_factor, dd_update=False):
        """
        The function rescales various magnetic field properties in an equilibrium by a specified
        factor.

        Args:
            rescale_factor: The `rescale` method you provided rescales various magnetic field components
                in an equilibrium object by a specified rescale factor. The rescale factor is a float value that
                you pass to the method to determine the extent of rescaling for the magnetic field components.

        Returns:
            The `rescale` method returns the rescaled equilibrium `equout` after applying the rescaling
            factor to various magnetic field components and properties within the equilibrium data
            structure. The method also updates the comment in the `ids_properties` of the equilibrium to
            indicate that the magnetic field has been rescaled by a certain factor.
        """
        from copy import deepcopy

        from packaging.version import Version

        try:
            dd_version = self.ids.ids_properties.version_put.data_dictionary.value
        except Exception as e:
            logger.debug(f"{e}")
            dd_version = "0.0.0"

        equout = deepcopy(self.ids)
        if dd_update:
            dd_version = DBMaster.get_dd_version()

        equout.ids_properties.version_put.data_dictionary = dd_version

        for itime in range(len(self.ids.vacuum_toroidal_field.b0)):
            equout.vacuum_toroidal_field.b0[itime] = self.ids.vacuum_toroidal_field.b0[itime] * rescale_factor

        for itime in range(len(self.ids.time_slice)):
            if (
                hasattr(self.ids.time_slice[itime].boundary, "psi")
                and self.ids.time_slice[itime].boundary.psi.has_value
            ):
                equout.time_slice[itime].boundary.psi = self.ids.time_slice[itime].boundary.psi * rescale_factor

            if (
                hasattr(self.ids.time_slice[itime].boundary_separatrix, "psi")
                and self.ids.time_slice[itime].boundary_separatrix.psi.has_value
            ):
                equout.time_slice[itime].boundary_separatrix.psi = (
                    self.ids.time_slice[itime].boundary_separatrix.psi * rescale_factor
                )

            if (
                hasattr(self.ids.time_slice[itime].boundary_secondary_separatrix, "psi")
                and self.ids.time_slice[itime].boundary_secondary_separatrix.psi.has_value
            ):
                equout.time_slice[itime].boundary_secondary_separatrix.psi = (
                    self.ids.time_slice[itime].boundary_secondary_separatrix.psi * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.b_field_tor_vacuum_r.measured.has_value:
                equout.time_slice[itime].constraints.b_field_tor_vacuum_r.measured = (
                    self.ids.time_slice[itime].constraints.b_field_tor_vacuum_r.measured * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.b_field_tor_vacuum_r.reconstructed.has_value:
                equout.time_slice[itime].constraints.b_field_tor_vacuum_r.reconstructed = (
                    self.ids.time_slice[itime].constraints.b_field_tor_vacuum_r.reconstructed * rescale_factor
                )

            for i1 in range(len(self.ids.time_slice[itime].constraints.bpol_probe)):
                equout.time_slice[itime].constraints.bpol_probe[i1].measured = (
                    self.ids.time_slice[itime].constraints.bpol_probe[i1].measured * rescale_factor
                )
                equout.time_slice[itime].constraints.bpol_probe[i1].reconstructed = (
                    self.ids.time_slice[itime].constraints.bpol_probe[i1].reconstructed * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.diamagnetic_flux.measured.has_value:
                equout.time_slice[itime].constraints.diamagnetic_flux.measured = (
                    self.ids.time_slice[itime].constraints.diamagnetic_flux.measured * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.diamagnetic_flux.reconstructed.has_value:
                equout.time_slice[itime].constraints.diamagnetic_flux.reconstructed = (
                    self.ids.time_slice[itime].constraints.diamagnetic_flux.reconstructed * rescale_factor
                )

            for i1 in range(len(self.ids.time_slice[itime].constraints.faraday_angle)):
                equout.time_slice[itime].constraints.faraday_angle[i1].measured = (
                    self.ids.time_slice[itime].constraints.faraday_angle[i1].measured * rescale_factor
                )
                equout.time_slice[itime].constraints.faraday_angle[i1].reconstructed = (
                    self.ids.time_slice[itime].constraints.faraday_angle[i1].reconstructed * rescale_factor
                )

            for i1 in range(len(self.ids.time_slice[itime].constraints.flux_loop)):
                equout.time_slice[itime].constraints.flux_loop[i1].measured = (
                    self.ids.time_slice[itime].constraints.flux_loop[i1].measured * rescale_factor
                )
                equout.time_slice[itime].constraints.flux_loop[i1].reconstructed = (
                    self.ids.time_slice[itime].constraints.flux_loop[i1].reconstructed * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.ip.measured.has_value:
                equout.time_slice[itime].constraints.ip.imeasured = (
                    self.ids.time_slice[itime].constraints.ip.measured * rescale_factor
                )

            if self.ids.time_slice[itime].constraints.ip.reconstructed.has_value:
                equout.time_slice[itime].constraints.ip.reconstructed = (
                    self.ids.time_slice[itime].constraints.ip.reconstructed * rescale_factor
                )

            if self.ids.time_slice[itime].global_quantities.ip.has_value:
                equout.time_slice[itime].global_quantities.ip = (
                    self.ids.time_slice[itime].global_quantities.ip * rescale_factor
                )

            if self.ids.time_slice[itime].global_quantities.psi_axis.has_value:
                equout.time_slice[itime].global_quantities.psi_axis = (
                    self.ids.time_slice[itime].global_quantities.psi_axis * rescale_factor
                )

            if self.ids.time_slice[itime].global_quantities.psi_boundary.has_value:
                equout.time_slice[itime].global_quantities.psi_boundary = (
                    self.ids.time_slice[itime].global_quantities.psi_boundary * rescale_factor
                )

            b_field_tor = get_compat_attr(
                self.ids.time_slice[itime].global_quantities.magnetic_axis, "b_field_tor", "b_field_phi"
            )

            if b_field_tor.has_value:
                if hasattr(equout.time_slice[itime].global_quantities.magnetic_axis, "b_field_tor"):
                    equout.time_slice[itime].global_quantities.magnetic_axis.b_field_tor = b_field_tor * rescale_factor
                elif hasattr(equout.time_slice[itime].global_quantities.magnetic_axis, "b_field_phi"):
                    equout.time_slice[itime].global_quantities.magnetic_axis.b_field_phi = b_field_tor * rescale_factor

            if Version(dd_version) > Version("3.14.0"):
                if self.ids.time_slice[itime].global_quantities.energy_mhd.has_value:
                    equout.time_slice[itime].global_quantities.energy_mhd = (
                        self.ids.time_slice[itime].global_quantities.energy_mhd * rescale_factor**2
                    )
            else:
                if self.ids.time_slice[itime].global_quantities.w_mhd.has_value:
                    equout.time_slice[itime].global_quantities.energy_mhd = (
                        self.ids.time_slice[itime].global_quantities.w_mhd * rescale_factor**2
                    )

            if Version(dd_version) > Version("3.31.0"):
                if self.ids.time_slice[itime].global_quantities.psi_external_average.has_value:
                    equout.time_slice[itime].global_quantities.psi_external_average = (
                        self.ids.time_slice[itime].global_quantities.psi_external_average * rescale_factor
                    )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.psi)):
                equout.time_slice[itime].profiles_1d.psi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.psi[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.phi)):
                equout.time_slice[itime].profiles_1d.phi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.phi[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.pressure)):
                equout.time_slice[itime].profiles_1d.pressure[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.pressure[i1d] * rescale_factor**2
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.f)):
                equout.time_slice[itime].profiles_1d.f[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.f[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.dpressure_dpsi)):
                equout.time_slice[itime].profiles_1d.dpressure_dpsi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.dpressure_dpsi[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.f_df_dpsi)):
                equout.time_slice[itime].profiles_1d.f_df_dpsi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.f_df_dpsi[i1d] * rescale_factor
                )

            j_tor_1d = get_compat_attr(self.ids.time_slice[itime].profiles_1d, "j_tor", "j_phi")
            if j_tor_1d is not None:
                if hasattr(equout.time_slice[itime].profiles_1d, "j_tor"):
                    for i1d in range(len(j_tor_1d)):
                        equout.time_slice[itime].profiles_1d.j_tor[i1d] = j_tor_1d[i1d] * rescale_factor
                elif hasattr(equout.time_slice[itime].profiles_1d, "j_phi"):
                    for i1d in range(len(j_tor_1d)):
                        equout.time_slice[itime].profiles_1d.j_phi[i1d] = j_tor_1d[i1d] * rescale_factor

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.j_parallel)):
                equout.time_slice[itime].profiles_1d.j_parallel[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.j_parallel[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.dpsi_drho_tor)):
                equout.time_slice[itime].profiles_1d.dpsi_drho_tor[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.dpsi_drho_tor[i1d] * rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.dvolume_dpsi)):
                equout.time_slice[itime].profiles_1d.dvolume_dpsi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.dvolume_dpsi[i1d] / rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.darea_dpsi)):
                equout.time_slice[itime].profiles_1d.darea_dpsi[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.darea_dpsi[i1d] / rescale_factor
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.gm4)):
                equout.time_slice[itime].profiles_1d.gm4[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.gm4[i1d] / rescale_factor**2
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.gm5)):
                equout.time_slice[itime].profiles_1d.gm5[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.gm5[i1d] * rescale_factor**2
                )

            for i1d in range(len(self.ids.time_slice[itime].profiles_1d.gm6)):
                equout.time_slice[itime].profiles_1d.gm6[i1d] = (
                    self.ids.time_slice[itime].profiles_1d.gm6[i1d] / rescale_factor**2
                )

            if Version(dd_version) > Version("3.5.0"):
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_field_average)):
                    equout.time_slice[itime].profiles_1d.b_field_average[i1d] = (
                        self.ids.time_slice[itime].profiles_1d.b_field_average[i1d] * rescale_factor
                    )
            else:
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_average)):
                    equout.time_slice[itime].profiles_1d.b_field_average[i1d] = (
                        abs(self.ids.time_slice[itime].profiles_1d.b_average[i1d]) * rescale_factor
                    )

            if Version(dd_version) > Version("3.5.0"):
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_field_min)):
                    equout.time_slice[itime].profiles_1d.b_field_min[i1d] = (
                        self.ids.time_slice[itime].profiles_1d.b_field_min[i1d] * rescale_factor
                    )
            else:
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_min)):
                    equout.time_slice[itime].profiles_1d.b_field_min[i1d] = (
                        abs(self.ids.time_slice[itime].profiles_1d.b_min[i1d]) * rescale_factor
                    )

            if Version(dd_version) > Version("3.5.0"):
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_field_max)):
                    equout.time_slice[itime].profiles_1d.b_field_max[i1d] = (
                        self.ids.time_slice[itime].profiles_1d.b_field_max[i1d] * rescale_factor
                    )
            else:
                for i1d in range(len(self.ids.time_slice[itime].profiles_1d.b_max)):
                    equout.time_slice[itime].profiles_1d.b_field_max[i1d] = (
                        abs(self.ids.time_slice[itime].profiles_1d.b_max[i1d]) * rescale_factor
                    )

            for i2d in range(len(self.ids.time_slice[itime].profiles_2d)):
                for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].psi)):
                    for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].psi[ir])):
                        equout.time_slice[itime].profiles_2d[i2d].psi[ir][iz] = (
                            self.ids.time_slice[itime].profiles_2d[i2d].psi[ir][iz] * rescale_factor
                        )

                for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].phi)):
                    for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].phi[ir])):
                        equout.time_slice[itime].profiles_2d[i2d].phi[ir][iz] = (
                            self.ids.time_slice[itime].profiles_2d[i2d].phi[ir][iz] * rescale_factor
                        )

                j_tor_2d = get_compat_attr(self.ids.time_slice[itime].profiles_2d[i2d], "j_tor", "j_phi")
                if j_tor_2d is not None:
                    if hasattr(equout.time_slice[itime].profiles_2d[i2d], "j_tor"):
                        for ir in range(len(j_tor_2d)):
                            for iz in range(len(j_tor_2d[ir])):
                                equout.time_slice[itime].profiles_2d[i2d].j_tor[ir][iz] = (
                                    j_tor_2d[ir][iz] * rescale_factor
                                )
                    elif hasattr(equout.time_slice[itime].profiles_2d[i2d], "j_phi"):
                        for ir in range(len(j_tor_2d)):
                            for iz in range(len(j_tor_2d[ir])):
                                equout.time_slice[itime].profiles_2d[i2d].j_phi[ir][iz] = (
                                    j_tor_2d[ir][iz] * rescale_factor
                                )

                for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].j_parallel)):
                    for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].j_parallel[ir])):
                        equout.time_slice[itime].profiles_2d[i2d].j_parallel[ir][iz] = (
                            self.ids.time_slice[itime].profiles_2d[i2d].j_parallel[ir][iz] * rescale_factor
                        )

                if Version(dd_version) > Version("3.5.0"):
                    for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_field_r)):
                        for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_field_r[ir])):
                            equout.time_slice[itime].profiles_2d[i2d].b_field_r[ir][iz] = (
                                self.ids.time_slice[itime].profiles_2d[i2d].b_field_r[ir][iz] * rescale_factor
                            )
                else:
                    for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_r)):
                        for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_r[ir])):
                            equout.time_slice[itime].profiles_2d[i2d].b_field_r[ir][iz] = (
                                self.ids.time_slice[itime].profiles_2d[i2d].b_r[ir][iz] * rescale_factor
                            )

                if Version(dd_version) > Version("3.5.0"):
                    for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_field_z)):
                        for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_field_z[ir])):
                            equout.time_slice[itime].profiles_2d[i2d].b_field_z[ir][iz] = (
                                self.ids.time_slice[itime].profiles_2d[i2d].b_field_z[ir][iz] * rescale_factor
                            )
                else:
                    for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_z)):
                        for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_z[ir])):
                            equout.time_slice[itime].profiles_2d[i2d].b_field_z[ir][iz] = (
                                self.ids.time_slice[itime].profiles_2d[i2d].b_z[ir][iz] * rescale_factor
                            )

                if Version(dd_version) > Version("3.5.0"):
                    b_field_tor = get_compat_attr(
                        self.ids.time_slice[itime].profiles_2d[i2d], "b_field_tor", "b_field_phi"
                    )
                    if b_field_tor:
                        for ir in range(len(b_field_tor)):
                            for iz in range(len(b_field_tor[ir])):
                                if hasattr(equout.time_slice[itime].profiles_2d[i2d], "b_field_tor"):
                                    equout.time_slice[itime].profiles_2d[i2d].b_field_tor[ir][iz] = (
                                        b_field_tor[ir][iz] * rescale_factor
                                    )
                                if hasattr(equout.time_slice[itime].profiles_2d[i2d], "b_field_phi"):
                                    equout.time_slice[itime].profiles_2d[i2d].b_field_phi[ir][iz] = (
                                        b_field_tor[ir][iz] * rescale_factor
                                    )
                else:
                    for ir in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_tor)):
                        for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].b_tor[ir])):
                            equout.time_slice[itime].profiles_2d[i2d].b_field_tor[ir][iz] = (
                                self.ids.time_slice[itime].profiles_2d[i2d].b_tor[ir][iz] * rescale_factor
                            )

            for iggd in range(len(self.ids.time_slice[itime].ggd)):
                for i2 in range(len(self.ids.time_slice[itime].ggd[iggd].psi)):
                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].psi[i2].values)):
                        equout.time_slice[itime].ggd[iggd].psi[i2].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].psi[i2].values[i] * rescale_factor
                        )
                        for j in range(len(self.ids.time_slice[itime].ggd[iggd].psi[i2].values[i])):
                            equout.time_slice[itime].ggd[iggd].psi[i2].coefficients[i][j] = (
                                self.ids.time_slice[itime].ggd[iggd].psi[i2].coefficients[i][j] * rescale_factor
                            )

                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].phi[i2].values)):
                        equout.time_slice[itime].ggd[iggd].phi[i2].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].phi[i2].values[i] * rescale_factor
                        )
                        for j in range(len(self.ids.time_slice[itime].ggd[iggd].phi[i2].values[i])):
                            equout.time_slice[itime].ggd[iggd].phi[i2].coefficients[i][j] = (
                                self.ids.time_slice[itime].ggd[iggd].phi[i2].coefficients[i][j] * rescale_factor
                            )

                    j_tor_ggd = get_compat_attr(self.ids.time_slice[itime].ggd[iggd], "j_tor", "j_phi")
                    if j_tor_ggd is not None:
                        equout_j_tor_ggd = get_compat_attr(equout.time_slice[itime].ggd[iggd], "j_tor", "j_phi")
                        for i in range(len(j_tor_ggd[i2].values)):
                            equout_j_tor_ggd[i2].values[i] = j_tor_ggd[i2].values[i] * rescale_factor
                            for j in range(len(j_tor_ggd[i2].values[i])):
                                equout_j_tor_ggd[i2].coefficients[i][j] = (
                                    j_tor_ggd[i2].coefficients[i][j] * rescale_factor
                                )

                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].j_parallel[i2].values)):
                        equout.time_slice[itime].ggd[iggd].j_parallel[i2].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].j_parallel[i2].values[i] * rescale_factor
                        )
                        for j in range(len(self.ids.time_slice[itime].ggd[iggd].j_parallel[i2].values[i])):
                            equout.time_slice[itime].ggd[iggd].j_parallel[i2].coefficients[i][j] = (
                                self.ids.time_slice[itime].ggd[iggd].j_parallel[i2].coefficients[i][j] * rescale_factor
                            )

                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].b_field_r[i2].values)):
                        equout.time_slice[itime].ggd[iggd].b_field_r[i2].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].b_field_r[i2].values[i] * rescale_factor
                        )
                        for j in range(len(self.ids.time_slice[itime].ggd[iggd].b_field_r[i2].values[i])):
                            equout.time_slice[itime].ggd[iggd].b_field_r[i2].coefficients[i][j] = (
                                self.ids.time_slice[itime].ggd[iggd].b_field_r[i2].coefficients[i][j] * rescale_factor
                            )

                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].b_field_z[i2].values)):
                        equout.time_slice[itime].ggd[iggd].b_field_z[i2].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].b_field_z[i2].values[i] * rescale_factor
                        )
                        for j in range(len(self.ids.time_slice[itime].ggd[iggd].b_field_z[i2].values[i])):
                            equout.time_slice[itime].ggd[iggd].b_field_z[i2].coefficients[i][j] = (
                                self.ids.time_slice[itime].ggd[iggd].b_field_z[i2].coefficients[i][j] * rescale_factor
                            )

                    b_field_tor = get_compat_attr(self.ids.time_slice[itime].ggd[iggd], "b_field_tor", "b_field_phi")

                    for i in range(len(b_field_tor[i2].values)):
                        if hasattr(equout.time_slice[itime].ggd[iggd], "b_field_tor"):
                            equout.time_slice[itime].ggd[iggd].b_field_tor[i2].values[i] = (
                                b_field_tor[i2].values[i] * rescale_factor
                            )
                            for j in range(len(b_field_tor[i2].values[i])):
                                equout.time_slice[itime].ggd[iggd].b_field_tor[i2].coefficients[i][j] = (
                                    b_field_tor[i2].coefficients[i][j] * rescale_factor
                                )
                        elif hasattr(equout.time_slice[itime].ggd[iggd], "b_field_phi"):
                            equout.time_slice[itime].ggd[iggd].b_field_phi[i2].values[i] = (
                                b_field_tor[i2].values[i] * rescale_factor
                            )
                            for j in range(len(b_field_tor[i2].values[i])):
                                equout.time_slice[itime].ggd[iggd].b_field_phi[i2].coefficients[i][j] = (
                                    b_field_tor[i2].coefficients[i][j] * rescale_factor
                                )

        equout.ids_properties.comment = (
            self.ids.ids_properties.comment + " (field rescaled by " + str(rescale_factor) + ")"
        )
        return equout

    def z_shift(self, shift, dd_update=False):
        """
        The function `z_shift` rigidly shifts the vertical position of various components within an
        equilibrium by a specified amount.

        Args:
            shift: The `shift` parameter in the `z_shift` method represents the vertical shift in meters
                that will be applied to the equilibrium data. This shift will be added to the z-coordinates of
                various points and boundaries within the equilibrium data structure.

        Returns:
            The `z_shift` method returns a vertically shifted equilibrium object (`equilibrium IDS`) after
            applying the specified vertical shift in meters to various components of the equilibrium data
            structure. The method modifies the z-coordinates of different components within the equilibrium
            object based on the provided shift value. Additionally, it updates the comment of the
            equilibrium object to indicate that it has been shifted vertically by a certain amount.
        """
        from copy import deepcopy

        try:
            dd_version = self.ids.ids_properties.version_put.data_dictionary.value
        except Exception as e:
            logger.debug(f"{e}")
            dd_version = "0.0.0"

        equout = deepcopy(self.ids)
        if dd_update:
            dd_version = DBMaster.get_dd_version()

        equout.ids_properties.version_put.data_dictionary = dd_version
        for itime in range(len(self.ids.time_slice)):
            for iz in range(len(self.ids.time_slice[itime].boundary.outline.z)):
                equout.time_slice[itime].boundary.outline.z[iz] = (
                    self.ids.time_slice[itime].boundary.outline.z[iz] + shift
                )

            for iz in range(len(self.ids.time_slice[itime].boundary.lcfs.z)):
                equout.time_slice[itime].boundary.lcfs.z[iz] = self.ids.time_slice[itime].boundary.lcfs.z[iz] + shift
            equout.time_slice[itime].boundary.geometric_axis.z = (
                self.ids.time_slice[itime].boundary.geometric_axis.z + shift
            )

            for ixpt in range(len(self.ids.time_slice[itime].boundary.x_point)):
                equout.time_slice[itime].boundary.x_point[ixpt].z = (
                    self.ids.time_slice[itime].boundary.x_point[ixpt].z + shift
                )

            for istr in range(len(self.ids.time_slice[itime].boundary.strike_point)):
                equout.time_slice[itime].boundary.strike_point[istr].z = (
                    self.ids.time_slice[itime].boundary.strike_point[istr].z + shift
                )
            equout.time_slice[itime].boundary.active_limiter_point.z = (
                self.ids.time_slice[itime].boundary.active_limiter_point.z + shift
            )

            for iz in range(len(self.ids.time_slice[itime].boundary_separatrix.outline.z)):
                equout.time_slice[itime].boundary_separatrix.outline.z[iz] = (
                    self.ids.time_slice[itime].boundary_separatrix.outline.z[iz] + shift
                )
            equout.time_slice[itime].boundary_separatrix.geometric_axis.z = (
                self.ids.time_slice[itime].boundary_separatrix.geometric_axis.z + shift
            )

            for ixpt in range(len(self.ids.time_slice[itime].boundary_separatrix.x_point)):
                equout.time_slice[itime].boundary_separatrix.x_point[ixpt].z = (
                    self.ids.time_slice[itime].boundary_separatrix.x_point[ixpt].z + shift
                )

            for istr in range(len(self.ids.time_slice[itime].boundary_separatrix.strike_point)):
                equout.time_slice[itime].boundary_separatrix.strike_point[istr].z = (
                    self.ids.time_slice[itime].boundary_separatrix.strike_point[istr].z + shift
                )
            equout.time_slice[itime].boundary_separatrix.active_limiter_point.z = (
                self.ids.time_slice[itime].boundary_separatrix.active_limiter_point.z + shift
            )
            equout.time_slice[itime].boundary_separatrix.closest_wall_point.z = (
                self.ids.time_slice[itime].boundary_separatrix.closest_wall_point.z + shift
            )
            equout.time_slice[itime].boundary_separatrix.dr_dz_zero_point.z = (
                self.ids.time_slice[itime].boundary_separatrix.dr_dz_zero_point.z + shift
            )

            for iz in range(len(self.ids.time_slice[itime].boundary_secondary_separatrix.outline.z)):
                equout.time_slice[itime].boundary_secondary_separatrix.outline.z[iz] = (
                    self.ids.time_slice[itime].boundary_secondary_separatrix.outline.z[iz] + shift
                )

            for ixpt in range(len(self.ids.time_slice[itime].boundary_secondary_separatrix.x_point)):
                equout.time_slice[itime].boundary_secondary_separatrix.x_point[ixpt].z = (
                    self.ids.time_slice[itime].boundary_secondary_separatrix.x_point[ixpt].z + shift
                )

            for istr in range(len(self.ids.time_slice[itime].boundary_secondary_separatrix.strike_point)):
                equout.time_slice[itime].boundary_secondary_separatrix.strike_point[istr].z = (
                    self.ids.time_slice[itime].boundary_secondary_separatrix.strike_point[istr].z + shift
                )

            for iq in range(len(self.ids.time_slice[itime].constraints.q)):
                equout.time_slice[itime].constraints.q[iq].position.z = (
                    self.ids.time_slice[itime].constraints.q[iq].position.z + shift
                )

            for ixpt in range(len(self.ids.time_slice[itime].constraints.x_point)):
                equout.time_slice[itime].constraints.x_point[ixpt].position_measured.z = (
                    self.ids.time_slice[itime].constraints.x_point[ixpt].position_measured.z + shift
                )
                equout.time_slice[itime].constraints.x_point[ixpt].position_reconstructed.z = (
                    self.ids.time_slice[itime].constraints.x_point[ixpt].position_reconstructed.z + shift
                )

            for istr in range(len(self.ids.time_slice[itime].constraints.strike_point)):
                equout.time_slice[itime].constraints.strike_point[istr].position_measured.z = (
                    self.ids.time_slice[itime].constraints.strike_point[istr].position_measured.z + shift
                )
            equout.time_slice[itime].global_quantities.magnetic_axis.z = (
                self.ids.time_slice[itime].global_quantities.magnetic_axis.z + shift
            )

            for iz in range(len(self.ids.time_slice[itime].profiles_1d.geometric_axis.z)):
                equout.time_slice[itime].profiles_1d.geometric_axis.z[iz] = (
                    self.ids.time_slice[itime].profiles_1d.geometric_axis.z[iz] + shift
                )

            for i2d in range(len(self.ids.time_slice[itime].profiles_2d)):
                if self.ids.time_slice[itime].profiles_2d[i2d].grid_type == 1:
                    for iz in range(len(self.ids.time_slice[itime].profiles_2d[i2d].grid.dim2)):
                        equout.time_slice[itime].profiles_2d[i2d].grid.dim2[iz] = (
                            self.ids.time_slice[itime].profiles_2d[i2d].grid.dim2[iz] + shift
                        )

                for i1 in range(len(self.ids.time_slice[itime].profiles_2d[i2d].z)):
                    for i2 in range(len(self.ids.time_slice[itime].profiles_2d[i2d].z[i1])):
                        equout.time_slice[itime].profiles_2d[i2d].z[i1][i2] = (
                            self.ids.time_slice[itime].profiles_2d[i2d].z[i1][i2] + shift
                        )

            for iggd in range(len(self.ids.time_slice[itime].ggd)):
                for iz in range(len(self.ids.time_slice[itime].ggd[iggd].z)):
                    for i in range(len(self.ids.time_slice[itime].ggd[iggd].z[iz].values)):
                        equout.time_slice[itime].ggd[iggd].z[iz].values[i] = (
                            self.ids.time_slice[itime].ggd[iggd].z[iz].values[i] + shift
                        )

            if self.ids.time_slice[itime].coordinate_system.grid_type == 1:
                for iz in range(len(self.ids.time_slice[itime].coordinate_system.grid.dim2)):
                    equout.time_slice[itime].coordinate_system.grid.dim2[iz] = (
                        self.ids.time_slice[itime].coordinate_system.grid.dim2[iz] + shift
                    )

            for i1 in range(len(self.ids.time_slice[itime].coordinate_system.z)):
                for i2 in range(len(self.ids.time_slice[itime].coordinate_system.z[i1])):
                    equout.time_slice[itime].coordinate_system.z[i1][i2] = (
                        self.ids.time_slice[itime].coordinate_system.z[i1][i2] + shift
                    )

        equout.ids_properties.comment = (
            self.ids.ids_properties.comment + " (shifted vertically by " + str(shift) + " m)"
        )
        return equout

    def get_profiles_1d_quantities(self, time_slice, attributes=None):
        """
        The function `get_profiles_1d_quantities` retrieves specified attributes from a 1D profile at a
        given time slice.

        Args:
            time_slice: Time slice is a parameter
            attributes: The `attributes` parameter in the `get_profiles_1d_quantities` function is a list
        of strings that represent the quantities or attributes you want to retrieve from the profiles_1d
        object for a specific time slice. defaults it retrives pressure, q, beta_pol

        Returns:
            A dictionary containing the values of the specified attributes ("pressure", "q", "beta_pol")
        for the given time slice from the profiles_1d data.
        """
        quantities = {}
        if attributes is None:
            attributes = ["pressure", "q", "beta_pol"]
        for attribute in attributes:
            ids_field = eval(f"self.ids.time_slice[{time_slice}].profiles_1d.{attribute}")
            if ids_field.has_value:
                quantities[attribute] = eval(f"self.ids.time_slice[{time_slice}].profiles_1d.{attribute}")
            else:
                logger.warning(f"self.ids.time_slice[{time_slice}].profiles_1d.{attribute} not found")
        return quantities

    def get_global_quantities(self, time_slice=None, attributes=None):
        """
        This Python function retrieves global quantities from a time slice object based on specified
        attributes.

        Args:
            time_slice: The `time_slice` parameter in the `get_global_quantities` function is used to
                specify a particular time slice for which you want to retrieve global quantities. If
                `time_slice` is not provided (i.e., it is `None`), the function will retrieve global quantities
                for all time slices
            attributes: The `attributes` parameter in the `get_global_quantities` function is used to
                specify a list of quantities that you want to retrieve from the global quantities of a time
                slice. The default list of attributes includes "q_min", "q_95", "li_3", "beta_tor

        Returns:
            The `get_global_quantities` function returns a dictionary `quantities` containing global
        quantities based on the provided `time_slice` and `attributes`. If `time_slice` is not
        specified, it calculates the global quantities for all time slices and stores them in arrays
        within the dictionary. If `time_slice` is specified, it retrieves the global quantities for that
        specific time slice and returns them in the dictionary format
        """
        quantities = {}
        if attributes is None:
            attributes = ["q_min.value", "q_95", "li_3", "beta_tor", "energy_mhd"]
        if not isinstance(attributes, list):
            logger.warning("attributes argument is not provided as list of quantities, returning None")
            return None

        if time_slice is not None:
            for attribute in attributes:
                quantities[attribute] = {}
                quantities[attribute]["node"] = []
                quantities[attribute]["coordinate"] = self.ids.time
            for attribute in attributes:
                info_flag = True
                for ti in range(len(self.ids.time_slice)):
                    node = eval(f"self.ids.time_slice[{ti}].global_quantities.{attribute}")
                    if info_flag:
                        quantities[attribute]["unit"] = node.metadata.units
                        quantities[attribute]["coordinate_unit"] = self.ids.time.metadata.units or "s"

                        quantities[attribute]["name"] = node.metadata.name
                        quantities[attribute]["coordinate_name"] = "time"
                        info_flag = False
                    quantities[attribute]["node"].append(node)
                counter = 0
                quantities[attribute]["has_value"] = True
                for node in quantities[attribute]["node"]:
                    if node == imas.ids_defs.EMPTY_INT or node == imas.ids_defs.EMPTY_FLOAT:
                        counter += 1

                if len(quantities[attribute]["node"]) == counter:
                    quantities[attribute]["has_value"] = False
            for attribute in attributes:
                quantities[attribute]["node"] = np.array(quantities[attribute]["node"])
        else:
            for attribute in attributes:
                quantities[attribute] = eval(f"self.ids.time_slice[{time_slice}].global_quantities.{attribute}")
        return quantities
        # q_min = self.ids.time_slice[ti].global_quantities.q_min
        # q_95 = self.ids.time_slice[ti].global_quantities.q_95
        # li_3 = self.ids.time_slice[ti].global_quantities.li_3
        # beta_tor = self.ids.time_slice[ti].global_quantities.beta_tor
        # energy_mhd= self.ids.time_slice[ti].global_quantities.energy_mhd

    def get_equilibria(self, selection=None):
        """
        The function `get_equilibria` retrieves equilibrium data from a given object and organizes it
        into a dictionary for further analysis.

        Args:
            selection (list, optional): List of data types to calculate and return. If None, returns all data.
                Possible values include: 'time', 'nt', 'ip', 'q0', 'beta', 'rmag', 'zmag', 'psi_axis',
                'psi_boundary', 'psi1D', 'qpsi1D', 'press1D', 'psi2D', 'jtor2D', 'r2D', 'z2D', 'rb',
                'zb', 'r', 'z', 'j_tor1D', 'rin1D', 'rout1D', 'output_flag', 'name', 'num_iterations',
                'iteration_error', 'constraints', 'ip_constraints', 'pf_constraints', 'passive_constraints',
                'bpol_constraints', 'fluxloop_constraints', 'profiles_1d', 'profiles_2d', 'boundaries',
                'global_quantities', 'all_constraints'

        Returns:
            The `get_equilibria` method returns a dictionary named `data` containing the requested equilibrium
            data such as time, magnetic field parameters, profiles in 1D and 2D, boundary information,
            constraints information, and other relevant details.
        """
        if selection is None:
            selection = ["all"]
        elif isinstance(selection, str):
            selection = [selection]

        selection_groups = {
            "all": [
                "time",
                "nt",
                "ip",
                "q0",
                "beta",
                "rmag",
                "zmag",
                "psi_axis",
                "psi_boundary",
                "psi1D",
                "qpsi1D",
                "press1D",
                "psi2D",
                "jtor2D",
                "r2D",
                "z2D",
                "rb",
                "zb",
                "r",
                "z",
                "j_tor1D",
                "rin1D",
                "rout1D",
                "output_flag",
                "name",
                "num_iterations",
                "iteration_error",
                "constraints",
            ],
            "basic": ["time", "nt", "ip", "q0", "beta", "rmag", "zmag", "psi_axis", "psi_boundary"],
            "profiles_1d": ["psi1D", "qpsi1D", "press1D", "j_tor1D", "rin1D", "rout1D"],
            "profiles_2d": ["psi2D", "jtor2D", "r2D", "z2D", "r", "z"],
            "boundaries": ["rb", "zb"],
            "global_quantities": ["ip", "q0", "beta", "rmag", "zmag", "psi_axis", "psi_boundary"],
            "constraints": [
                "ip_constraints",
                "pf_constraints",
                "passive_constraints",
                "bpol_constraints",
                "fluxloop_constraints",
            ],
            "all_constraints": [
                "ip_constraints",
                "pf_constraints",
                "passive_constraints",
                "bpol_constraints",
                "fluxloop_constraints",
            ],
        }

        expanded_selection = []
        for item in selection:
            if item in selection_groups:
                expanded_selection.extend(selection_groups[item])
            else:
                expanded_selection.append(item)

        selection = list(dict.fromkeys(expanded_selection))

        homogeneous_time = self.ids.ids_properties.homogeneous_time
        name = self.ids.code.name
        if homogeneous_time == 1:
            time = self.ids.time
        else:
            # Extract time from time_slice array
            time = np.array([ts.time for ts in self.ids.time_slice]) if len(self.ids.time_slice) > 0 else np.array([])
        nt = time.size

        data = {}

        if "time" in selection:
            data["time"] = time
        if "nt" in selection:
            data["nt"] = nt
        if "name" in selection:
            data["name"] = name
        need_global_quantities = any(
            item in selection
            for item in [
                "ip",
                "q0",
                "beta",
                "rmag",
                "zmag",
                "psi_axis",
                "psi_boundary",
                "num_iterations",
                "iteration_error",
                "output_flag",
            ]
        )

        if need_global_quantities:
            ip = np.zeros(nt) if "ip" in selection else None
            q0 = np.zeros(nt) if "q0" in selection else None
            beta = np.zeros(nt) if "beta" in selection else None
            rmag = np.zeros(nt) if "rmag" in selection else None
            zmag = np.zeros(nt) if "zmag" in selection else None
            psi_axis = np.zeros(nt) if "psi_axis" in selection else None
            psi_boundary = np.zeros(nt) if "psi_boundary" in selection else None
            num_iterations = np.zeros(nt) if "num_iterations" in selection else None
            iteration_error = np.zeros(nt) if "iteration_error" in selection else None

            if "output_flag" in selection:
                output_flag = self.ids.code.output_flag
                if len(output_flag) == 0:
                    output_flag = np.zeros(len(self.ids.time_slice), dtype=int)
                data["output_flag"] = output_flag

        need_profiles_1d = any(
            item in selection for item in ["psi1D", "qpsi1D", "press1D", "j_tor1D", "rin1D", "rout1D"]
        )
        need_profiles_2d = any(item in selection for item in ["psi2D", "jtor2D", "r2D", "z2D", "r", "z"])
        need_boundaries = any(item in selection for item in ["rb", "zb"])
        need_constraints = any(
            item in selection
            for item in [
                "constraints",
                "ip_constraints",
                "pf_constraints",
                "passive_constraints",
                "bpol_constraints",
                "fluxloop_constraints",
            ]
        )

        need_ip_constraints = "ip_constraints" in selection or "constraints" in selection
        need_pf_constraints = "pf_constraints" in selection or "constraints" in selection
        need_passive_constraints = "passive_constraints" in selection or "constraints" in selection
        need_bpol_constraints = "bpol_constraints" in selection or "constraints" in selection
        need_fluxloop_constraints = "fluxloop_constraints" in selection or "constraints" in selection

        n = 0
        n2 = 0
        n3 = 0
        n4 = 0
        n5 = 0
        n6 = 0
        n7 = 0
        n8 = 0

        if self.ids.time_slice:
            for time_slice in self.ids.time_slice:
                if time_slice:
                    if need_profiles_1d and hasattr(time_slice, "profiles_1d") and time_slice.profiles_1d:
                        n = time_slice.profiles_1d.psi.size
                    if need_profiles_2d and hasattr(time_slice, "profiles_2d") and time_slice.profiles_2d:
                        n2 = time_slice.profiles_2d[0].psi.shape
                    if need_boundaries and (
                        hasattr(time_slice, "boundary")
                        and time_slice.boundary
                        and hasattr(time_slice.boundary, "outline")
                        and time_slice.boundary.outline
                    ):
                        boundary_size = time_slice.boundary.outline.r.size
                        if n3 == 0:  # Set n3 to first valid boundary size
                            n3 = boundary_size
                    if need_constraints:
                        constraints_obj = time_slice.constraints
                        if need_ip_constraints and hasattr(constraints_obj, "ip") and constraints_obj.ip:
                            n4 = 1
                        if (
                            need_pf_constraints
                            and hasattr(constraints_obj, "pf_current")
                            and constraints_obj.pf_current
                        ):
                            n5 = len(constraints_obj.pf_current)
                        if (
                            need_passive_constraints
                            and hasattr(constraints_obj, "pf_passive_current")
                            and constraints_obj.pf_passive_current
                        ):
                            n6 = len(constraints_obj.pf_passive_current)
                        if (
                            need_bpol_constraints
                            and hasattr(constraints_obj, "bpol_probe")
                            and constraints_obj.bpol_probe
                        ):
                            n7 = len(constraints_obj.bpol_probe)
                        if (
                            need_fluxloop_constraints
                            and hasattr(constraints_obj, "flux_loop")
                            and constraints_obj.flux_loop
                        ):
                            n8 = len(constraints_obj.flux_loop)

                    profiles_ok = not need_profiles_1d or n > 0
                    profiles_2d_ok = not need_profiles_2d or n2
                    boundaries_ok = not need_boundaries or n3 > 0

                    if profiles_ok and profiles_2d_ok and boundaries_ok:
                        break  # Exits the loop

        if need_profiles_1d and n > 0:
            psi1D = np.zeros((nt, n)) if "psi1D" in selection else None
            qpsi1D = np.zeros((nt, n)) if "qpsi1D" in selection else None
            press1D = np.zeros((nt, n)) if "press1D" in selection else None
            j_tor1D = np.zeros((nt, n)) if "j_tor1D" in selection else None
            rin1D = np.zeros((nt, n)) if "rin1D" in selection else None
            rout1D = np.zeros((nt, n)) if "rout1D" in selection else None

            i = -1
            for time_slice in self.ids.time_slice:
                i = i + 1

                if need_global_quantities:
                    if ip is not None:
                        ip[i] = time_slice.global_quantities.ip
                    if q0 is not None:
                        q0[i] = time_slice.global_quantities.q_axis
                    if beta is not None:
                        beta[i] = time_slice.global_quantities.beta_tor
                    if rmag is not None:
                        rmag[i] = time_slice.global_quantities.magnetic_axis.r
                    if zmag is not None:
                        zmag[i] = time_slice.global_quantities.magnetic_axis.z
                    if psi_axis is not None:
                        psi_axis[i] = time_slice.global_quantities.psi_axis
                    if psi_boundary is not None:
                        psi_boundary[i] = time_slice.global_quantities.psi_boundary
                    if num_iterations is not None:
                        num_iterations[i] = time_slice.convergence.iterations_n
                    if iteration_error is not None:
                        iteration_error[i] = time_slice.convergence.grad_shafranov_deviation_value

                if time_slice.profiles_1d.psi.size > 0 and psi1D is not None:
                    psi1D[i, :] = time_slice.profiles_1d.psi
                if time_slice.profiles_1d.q.size > 0 and qpsi1D is not None:
                    qpsi1D[i, :] = time_slice.profiles_1d.q
                if time_slice.profiles_1d.pressure.size > 0 and press1D is not None:
                    press1D[i, :] = time_slice.profiles_1d.pressure
                j_tor_1d = get_compat_attr(time_slice.profiles_1d, "j_tor", "j_phi")
                if j_tor_1d is not None and j_tor_1d.size > 0 and j_tor1D is not None:
                    j_tor1D[i, :] = j_tor_1d
                if time_slice.profiles_1d.r_inboard.size > 0 and rin1D is not None:
                    rin1D[i, :] = time_slice.profiles_1d.r_inboard
                if time_slice.profiles_1d.r_outboard.size > 0 and rout1D is not None:
                    rout1D[i, :] = time_slice.profiles_1d.r_outboard
        elif need_global_quantities:
            psi1D = qpsi1D = press1D = j_tor1D = rin1D = rout1D = None
            for i, time_slice in enumerate(self.ids.time_slice):
                if ip is not None:
                    ip[i] = time_slice.global_quantities.ip
                if q0 is not None:
                    q0[i] = time_slice.global_quantities.q_axis
                if beta is not None:
                    beta[i] = time_slice.global_quantities.beta_tor
                if rmag is not None:
                    rmag[i] = time_slice.global_quantities.magnetic_axis.r
                if zmag is not None:
                    zmag[i] = time_slice.global_quantities.magnetic_axis.z
                if psi_axis is not None:
                    psi_axis[i] = time_slice.global_quantities.psi_axis
                if psi_boundary is not None:
                    psi_boundary[i] = time_slice.global_quantities.psi_boundary
                if num_iterations is not None:
                    num_iterations[i] = time_slice.convergence.iterations_n
                if iteration_error is not None:
                    iteration_error[i] = time_slice.convergence.grad_shafranov_deviation_value
        else:
            psi1D = qpsi1D = press1D = j_tor1D = rin1D = rout1D = None
            ip = q0 = beta = rmag = zmag = psi_axis = psi_boundary = num_iterations = iteration_error = None

        # Initialize variables with defaults
        rb = zb = r = z = psi2D = jtor2D = r2D = z2D = None

        if need_profiles_2d and isinstance(n2, tuple):
            psi2D = np.zeros((nt, n2[0], n2[1])) if "psi2D" in selection else None
            jtor2D = np.zeros((nt, n2[0], n2[1])) if "jtor2D" in selection else None
            r2D = np.zeros((nt, n2[0], n2[1])) if "r2D" in selection else None
            z2D = np.zeros((nt, n2[0], n2[1])) if "z2D" in selection else None

            i = -1
            for time_slice in self.ids.time_slice:
                i = i + 1
                if len(time_slice.profiles_2d) > 0:
                    if time_slice.profiles_2d[0].r.size > 0 and r2D is not None:
                        r2D[i, :, :] = time_slice.profiles_2d[0].r
                    if time_slice.profiles_2d[0].z.size > 0 and z2D is not None:
                        z2D[i, :, :] = time_slice.profiles_2d[0].z
                    if time_slice.profiles_2d[0].psi.size > 0 and psi2D is not None:
                        psi2D[i, :, :] = time_slice.profiles_2d[0].psi
                    j_tor_2d = get_compat_attr(time_slice.profiles_2d[0], "j_tor", "j_phi")
                    if j_tor_2d is not None and j_tor_2d.size > 0 and jtor2D is not None:
                        jtor2D[i, :, :] = j_tor_2d
                    if "r" in selection and time_slice.profiles_2d[0].grid.dim1.size > 0:
                        r = time_slice.profiles_2d[0].grid.dim1
                    if "z" in selection and time_slice.profiles_2d[0].grid.dim2.size > 0:
                        z = time_slice.profiles_2d[0].grid.dim2

        # Initialize boundary arrays - each time slice can have different size
        rb = [] if "rb" in selection else None
        zb = [] if "zb" in selection else None

        if need_boundaries:
            for i, time_slice in enumerate(self.ids.time_slice):
                if time_slice.boundary.outline.r.size > 0 and rb is not None:
                    rb.append(time_slice.boundary.outline.r)
                elif rb is not None:
                    rb.append(np.array([]))

                if time_slice.boundary.outline.z.size > 0 and zb is not None:
                    zb.append(time_slice.boundary.outline.z)
                elif zb is not None:
                    zb.append(np.array([]))

            # Convert lists to arrays of objects to allow variable-length arrays
            if rb is not None:
                rb = np.array(rb, dtype=object)
            if zb is not None:
                zb = np.array(zb, dtype=object)

        constraints = None
        if need_constraints:
            constr_ip_meas = constr_ip_recon = constr_ip_source = None
            constr_pf_meas = constr_pf_recon = constr_pf_source = None
            constr_pas_meas = constr_pas_recon = constr_pas_source = None
            constr_bpol_meas = constr_bpol_recon = constr_bpol_source = None
            constr_fluxloop_meas = constr_fluxloop_recon = constr_fluxloop_source = None

            if need_ip_constraints and n4 > 0:
                constr_ip_meas = np.zeros((nt, 1))
                constr_ip_recon = np.zeros((nt, 1))
                constr_ip_source = np.zeros((nt, 1), dtype=object)

                for i, time_slice in enumerate(self.ids.time_slice):
                    constr_ip_meas[i, 0] = time_slice.constraints.ip.measured
                    constr_ip_recon[i, 0] = time_slice.constraints.ip.reconstructed
                    constr_ip_source[i, 0] = time_slice.constraints.ip.source

            if need_pf_constraints and n5 > 0:
                constr_pf_meas = np.zeros((nt, n5))
                constr_pf_recon = np.zeros((nt, n5))
                constr_pf_source = np.empty((nt, n5), dtype=object)

                for i, time_slice in enumerate(self.ids.time_slice):
                    pf_currents = time_slice.constraints.pf_current
                    n_pf_currents = len(pf_currents)

                    constr_pf_meas[i, :n_pf_currents] = [current.measured for current in pf_currents]
                    constr_pf_recon[i, :n_pf_currents] = [current.reconstructed for current in pf_currents]
                    constr_pf_source[i, :n_pf_currents] = [str(current.source) for current in pf_currents]

            if need_passive_constraints and n6 > 0:
                constr_pas_meas = np.zeros((nt, n6))
                constr_pas_recon = np.zeros((nt, n6))
                constr_pas_source = np.zeros((nt, n6), dtype=object)

                for i, time_slice in enumerate(self.ids.time_slice):
                    pf_passive_currents = time_slice.constraints.pf_passive_current
                    n_pf_passive = len(pf_passive_currents)

                    constr_pas_meas[i, :n_pf_passive] = [current.measured for current in pf_passive_currents]
                    constr_pas_recon[i, :n_pf_passive] = [current.reconstructed for current in pf_passive_currents]
                    constr_pas_source[i, :n_pf_passive] = [current.source for current in pf_passive_currents]

            if need_bpol_constraints and n7 > 0:
                constr_bpol_meas = np.zeros((nt, n7))
                constr_bpol_recon = np.zeros((nt, n7))
                constr_bpol_source = np.zeros((nt, n7), dtype=object)

                for i, time_slice in enumerate(self.ids.time_slice):
                    bpol_probes = time_slice.constraints.bpol_probe
                    n_bpol_probes = len(bpol_probes)

                    constr_bpol_meas[i, :n_bpol_probes] = [probe.measured for probe in bpol_probes]
                    constr_bpol_recon[i, :n_bpol_probes] = [probe.reconstructed for probe in bpol_probes]
                    constr_bpol_source[i, :n_bpol_probes] = [probe.source for probe in bpol_probes]

            if need_fluxloop_constraints and n8 > 0:
                constr_fluxloop_meas = np.zeros((nt, n8))
                constr_fluxloop_recon = np.zeros((nt, n8))
                constr_fluxloop_source = np.zeros((nt, n8), dtype=object)

                for i, time_slice in enumerate(self.ids.time_slice):
                    flux_loops = time_slice.constraints.flux_loop
                    n_flux_loops = len(flux_loops)

                    constr_fluxloop_meas[i, :n_flux_loops] = [loop.measured for loop in flux_loops]
                    constr_fluxloop_recon[i, :n_flux_loops] = [loop.reconstructed for loop in flux_loops]
                    constr_fluxloop_source[i, :n_flux_loops] = [loop.source for loop in flux_loops]

            constraints = {
                "ip_meas": constr_ip_meas,
                "ip_recon": constr_ip_recon,
                "ip_source": constr_ip_source,
                "pf_meas": constr_pf_meas,
                "pf_recon": constr_pf_recon,
                "pf_source": constr_pf_source,
                "pas_meas": constr_pas_meas,
                "pas_recon": constr_pas_recon,
                "pas_source": constr_pas_source,
                "bpol_meas": constr_bpol_meas,
                "bpol_recon": constr_bpol_recon,
                "bpol_source": constr_bpol_source,
                "fluxloop_meas": constr_fluxloop_meas,
                "fluxloop_recon": constr_fluxloop_recon,
                "fluxloop_source": constr_fluxloop_source,
            }

        if "ip" in selection and ip is not None:
            data["ip"] = ip
        if "q0" in selection and q0 is not None:
            data["q0"] = q0
        if "beta" in selection and beta is not None:
            data["beta"] = beta
        if "rmag" in selection and rmag is not None:
            data["rmag"] = rmag
        if "zmag" in selection and zmag is not None:
            data["zmag"] = zmag
        if "psi_axis" in selection and psi_axis is not None:
            data["psi_axis"] = psi_axis
        if "psi_boundary" in selection and psi_boundary is not None:
            data["psi_boundary"] = psi_boundary
        if "num_iterations" in selection and num_iterations is not None:
            data["num_iterations"] = num_iterations
        if "iteration_error" in selection and iteration_error is not None:
            data["iteration_error"] = iteration_error
        if "psi1D" in selection and psi1D is not None:
            data["psi1D"] = psi1D
        if "qpsi1D" in selection and qpsi1D is not None:
            data["qpsi1D"] = qpsi1D
        if "press1D" in selection and press1D is not None:
            data["press1D"] = press1D
        if "j_tor1D" in selection and j_tor1D is not None:
            data["j_tor1D"] = j_tor1D
        if "rin1D" in selection and rin1D is not None:
            data["rin1D"] = rin1D
        if "rout1D" in selection and rout1D is not None:
            data["rout1D"] = rout1D
        if "psi2D" in selection and psi2D is not None:
            data["psi2D"] = psi2D
        if "jtor2D" in selection and jtor2D is not None:
            data["jtor2D"] = jtor2D
        if "r2D" in selection and r2D is not None:
            data["r2D"] = r2D
        if "z2D" in selection and z2D is not None:
            data["z2D"] = z2D
        if "rb" in selection and rb is not None:
            data["rb"] = rb
        if "zb" in selection and zb is not None:
            data["zb"] = zb
        if "r" in selection and r is not None:
            data["r"] = r
        if "z" in selection and z is not None:
            data["z"] = z

        if (
            "constraints" in selection
            or any(
                item in selection
                for item in [
                    "ip_constraints",
                    "pf_constraints",
                    "passive_constraints",
                    "bpol_constraints",
                    "fluxloop_constraints",
                ]
            )
        ) and constraints is not None:
            if "constraints" in selection:
                data["constraints"] = constraints
            else:
                selected_constraints = {}
                if "ip_constraints" in selection:
                    selected_constraints.update(
                        {
                            "ip_meas": constraints["ip_meas"],
                            "ip_recon": constraints["ip_recon"],
                            "ip_source": constraints["ip_source"],
                        }
                    )
                if "pf_constraints" in selection:
                    selected_constraints.update(
                        {
                            "pf_meas": constraints["pf_meas"],
                            "pf_recon": constraints["pf_recon"],
                            "pf_source": constraints["pf_source"],
                        }
                    )
                if "passive_constraints" in selection:
                    selected_constraints.update(
                        {
                            "pas_meas": constraints["pas_meas"],
                            "pas_recon": constraints["pas_recon"],
                            "pas_source": constraints["pas_source"],
                        }
                    )
                if "bpol_constraints" in selection:
                    selected_constraints.update(
                        {
                            "bpol_meas": constraints["bpol_meas"],
                            "bpol_recon": constraints["bpol_recon"],
                            "bpol_source": constraints["bpol_source"],
                        }
                    )
                if "fluxloop_constraints" in selection:
                    selected_constraints.update(
                        {
                            "fluxloop_meas": constraints["fluxloop_meas"],
                            "fluxloop_recon": constraints["fluxloop_recon"],
                            "fluxloop_source": constraints["fluxloop_source"],
                        }
                    )
                data["constraints"] = selected_constraints

        return data

    def get_contour(
        self,
        psi_axis,
        psi_boundary,
        time,
        time_index1,
        psi_axis2=None,
        psi_boundary2=None,
        time2=None,
        psi2D1=None,
        psi2D2=None,
    ):
        n = 10

        # Check if psi_axis/boundary are fill values and calculate from psi2D if available
        is_fill_1 = abs(psi_axis[time_index1]) > 1e30 or abs(psi_boundary[time_index1]) > 1e30
        if is_fill_1 and psi2D1 is not None and len(psi2D1) > time_index1:
            logger.info("psi_axis/boundary are fill values for equilibrium 1, calculating from psi2D data")
            psi_axis_calc = np.min(psi2D1[time_index1])
            psi_boundary_calc = np.max(psi2D1[time_index1])
        else:
            psi_axis_calc = psi_axis[time_index1]
            psi_boundary_calc = psi_boundary[time_index1]

        dp = (psi_boundary_calc - psi_axis_calc) / n
        if dp == 0.0:
            c = np.array([psi_axis_calc])
        else:
            c = np.arange(psi_axis_calc, psi_axis_calc + 2 * n * dp, dp)
            is_decreasing = np.all(np.diff(c) < 0)
            if is_decreasing:
                c = c[::-1]

        if psi_axis2 is not None:
            time_index2 = np.argmin(abs(time2 - time[time_index1]))

            # Check if psi_axis2/boundary2 are fill values and calculate from psi2D2 if available
            is_fill_2 = abs(psi_axis2[time_index2]) > 1e30 or abs(psi_boundary2[time_index2]) > 1e30
            if is_fill_2 and psi2D2 is not None and len(psi2D2) > time_index2:
                logger.info("psi_axis/boundary are fill values for equilibrium 2, calculating from psi2D data")
                psi_axis2_calc = np.min(psi2D2[time_index2])
                psi_boundary2_calc = np.max(psi2D2[time_index2])
            else:
                psi_axis2_calc = psi_axis2[time_index2]
                psi_boundary2_calc = psi_boundary2[time_index2]

            dp = (psi_boundary2_calc - psi_axis2_calc) / n
            if dp == 0.0:
                ce = np.array([psi_axis2_calc])
            else:
                ce = np.arange(psi_axis2_calc, psi_axis2_calc + 2 * n * dp, dp)
                is_decreasing = np.all(np.diff(ce) < 0)
                if is_decreasing:
                    ce = ce[::-1]
        else:
            ce = None

        return c, ce

    def get_constraints_info(self, label, constraints, constraintsE, time, time_index1, timeE):
        labels = ["$I_p$", "pf-currents", "passive-currents", "$B_{pol}$ probes", "flux loops"]
        constraint_available = [True] * len(labels)

        # Debug logging
        logger.debug(f"Checking constraints for label: {label}")
        logger.debug(
            f"Constraints dict keys: {constraints.keys() if constraints and hasattr(constraints, 'keys') else 'N/A'}"
        )

        # Check if either measurement or reconstruction data is available for each constraint type
        has_ip = ("ip_meas" in constraints and constraints["ip_meas"] is not None) or (
            "ip_recon" in constraints and constraints["ip_recon"] is not None
        )
        has_pf = ("pf_meas" in constraints and constraints["pf_meas"] is not None) or (
            "pf_recon" in constraints and constraints["pf_recon"] is not None
        )
        has_pas = ("pas_meas" in constraints and constraints["pas_meas"] is not None) or (
            "pas_recon" in constraints and constraints["pas_recon"] is not None
        )
        has_bpol = ("bpol_meas" in constraints and constraints["bpol_meas"] is not None) or (
            "bpol_recon" in constraints and constraints["bpol_recon"] is not None
        )
        has_flux = ("fluxloop_meas" in constraints and constraints["fluxloop_meas"] is not None) or (
            "fluxloop_recon" in constraints and constraints["fluxloop_recon"] is not None
        )

        constraint_available = [has_ip, has_pf, has_pas, has_bpol, has_flux]

        logger.debug(
            f"Constraint availability: IP={has_ip}, PF={has_pf}, PAS={has_pas}, BPOL={has_bpol}, FLUX={has_flux}"
        )
        for index, item in enumerate(labels):
            if label == item:
                break
        if not constraint_available[index]:
            logger.warning(f"Constraint '{label}' is not available in the data")
            return
        constraintSelected = label
        y1 = None
        y2 = None
        y3 = None
        y4 = None
        text = ""
        if constraintSelected == "$I_p$":
            scaleFactor = 1e6
            text = "[MA]"
            try:
                y1 = constraints["ip_meas"][time_index1, :] if constraints["ip_meas"] is not None else None
                if constraints["ip_meas"] is None:
                    logger.info("Warning: first ['ip_meas'] data is not present")
                y2 = constraints["ip_recon"][time_index1, :] if constraints["ip_recon"] is not None else None
                if constraints["ip_recon"] is None:
                    logger.info("Warning: first ['ip_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
            try:
                time_index2 = np.argmin(abs(timeE - time[time_index1]))
                y3 = constraintsE["ip_meas"][time_index2, :] if constraintsE["ip_meas"] is not None else None
                if constraintsE["ip_meas"] is None:
                    logger.info("Warning: second ['ip_meas'] data is not present")
                y4 = constraintsE["ip_recon"][time_index2, :] if constraintsE["ip_recon"] is not None else None
                if constraintsE["ip_recon"] is None:
                    logger.info("Warning: second ['ip_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
        elif constraintSelected == "pf-currents":
            text = "[kA]"
            scaleFactor = 1e3
            try:
                y1 = constraints["pf_meas"][time_index1, :] if constraints["pf_meas"] is not None else None
                if constraints["pf_meas"] is None:
                    logger.info("Warning: first ['pf_meas'] data is not present")
                y2 = constraints["pf_recon"][time_index1, :] if constraints["pf_recon"] is not None else None
                if constraints["pf_recon"] is None:
                    logger.info("Warning: first ['pf_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
            try:
                if timeE is not None:
                    time_index2 = np.argmin(abs(timeE - time[time_index1]))
                    y3 = constraintsE["pf_meas"][time_index2, :] if constraintsE["pf_meas"] is not None else None
                    if constraintsE["pf_meas"] is None:
                        logger.info("Warning: second ['pf_meas'] data is not present")
                    y4 = constraintsE["pf_recon"][time_index2, :] if constraintsE["pf_recon"] is not None else None
                    if constraintsE["pf_recon"] is None:
                        logger.info("Warning: second ['pf_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
        elif constraintSelected == "passive-currents":
            text = "[kA]"
            scaleFactor = 1e3
            try:
                y1 = constraints["pas_meas"][time_index1, :] if constraints["pas_meas"] is not None else None
                if constraints["pas_meas"] is None:
                    logger.info("Warning: first ['pas_meas'] data is not present")
                y2 = constraints["pas_recon"][time_index1, :] if constraints["pas_recon"] is not None else None
                if constraints["pas_recon"] is None:
                    logger.info("Warning: first ['pas_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
            try:
                time_index2 = np.argmin(abs(timeE - time[time_index1]))
                y3 = constraintsE["pas_meas"][time_index2, :] if constraintsE["pas_meas"] is not None else None
                if constraintsE["pas_meas"] is None:
                    logger.info("Warning: second ['pas_meas'] data is not present")
                y4 = constraintsE["pas_recon"][time_index2, :] if constraintsE["pas_recon"] is not None else None
                if constraintsE["pas_recon"] is None:
                    logger.info("Warning: second ['pas_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
        elif constraintSelected == "$B_{pol}$ probes":
            text = "[mT]"
            scaleFactor = 1e-3
            try:
                y1 = constraints["bpol_meas"][time_index1, :] if constraints["bpol_meas"] is not None else None
                if constraints["bpol_meas"] is None:
                    logger.info("Warning: first ['bpol_meas'] data is not present")
                y2 = constraints["bpol_recon"][time_index1, :] if constraints["bpol_recon"] is not None else None
                if constraints["bpol_recon"] is None:
                    logger.info("Warning: firs ['bpol_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
            try:
                time_index2 = np.argmin(abs(timeE - time[time_index1]))
                y3 = constraintsE["bpol_meas"][time_index2, :] if constraintsE["bpol_meas"] is not None else None
                if constraintsE["bpol_meas"] is None:
                    logger.info("Warning: second ['bpol_meas'] data is not present")
                y4 = constraintsE["bpol_recon"][time_index2, :] if constraintsE["bpol_recon"] is not None else None
                if constraintsE["bpol_recon"] is None:
                    logger.info("Warning: second ['bpol_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
        elif constraintSelected == "flux loops":
            text = "[Wb]"
            scaleFactor = 1e0
            try:
                y1 = constraints["fluxloop_meas"][time_index1, :] if constraints["fluxloop_meas"] is not None else None
                if constraints["fluxloop_meas"] is None:
                    logger.info("Warning: first ['fluxloop_meas'] data is not present")
                y2 = (
                    constraints["fluxloop_recon"][time_index1, :] if constraints["fluxloop_recon"] is not None else None
                )
                if constraints["fluxloop_recon"] is None:
                    logger.info("Warning: first ['fluxloop_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
            try:
                time_index2 = np.argmin(abs(timeE - time[time_index1]))
                y3 = (
                    constraintsE["fluxloop_meas"][time_index2, :] if constraintsE["fluxloop_meas"] is not None else None
                )
                if constraintsE["fluxloop_meas"] is None:
                    logger.info("Warning: second ['fluxloop_meas'] data is not present")
                y4 = (
                    constraintsE["fluxloop_recon"][time_index2, :]
                    if constraintsE["fluxloop_recon"] is not None
                    else None
                )
                if constraintsE["fluxloop_recon"] is None:
                    logger.info("Warning: second ['fluxloop_recon'] data is not present")
            except Exception as e:
                logger.error(f"Exception occurred detailed description : {e}")
        return y1, y2, y3, y4, constraintSelected, text, scaleFactor
