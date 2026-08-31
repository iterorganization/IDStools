#!/usr/bin/env python
import datetime
import glob
import logging
import os
import re
from copy import deepcopy
from pprint import pformat
from statistics import median
from typing import List, Optional, Union

try:
    import imaspy as imas
except ImportError:
    import imas
import numpy as np
from fortranformat import FortranRecordReader

from idstools import GIT_REV, __version__
from idstools.cocos import COCOS, IDS_COCOS, compute_COCOS

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------


class GEQDSK:
    """
    GEQDSK module for IMAS

    [1] L.L. Lao, "G EQDSK FORMAT", https://w3.pppl.gov/ntcc/TORAY/G_EQDSK.pdf
    [2] O. Sauter and S.Yu. Medvedev, "Tokamak Coordinate Conventions : COCOS",
    Comput. Physics Commun. 184 (2013) 293
    """

    def __init__(self, fpath, ipsign_out, b0sign_out, cocos_in):
        """
        Read GEQDSK file and set COCOS transformation coefficients

        Parameters
        ----------
        fpath: str
            Path to GEQDSK file
        ipsign_out: int
            Desired sign(Ip) in output
        b0sign_out: int
            Desired sign(B0) in output
        cocos_in: int
            Coerce input COCOS
        """

        # 1. Register name of GEQDSK file
        self.fpath = os.path.expanduser(os.path.expandvars(fpath))
        logger.debug("GEQDSK fpath: \n%s", pformat(self.fpath, indent=2))

        # 2. Read GEQDSK file
        self.data = self._load(self.fpath)
        logger.debug("GEQDSK data: \n%s", pformat(self.data, indent=2, sort_dicts=False))

        # 3. Confer COCOS
        if cocos_in:
            self.cocos = COCOS(
                index={
                    "COCOS": cocos_in,
                    "ipsign": np.sign(self.data["CURRENT"]),
                    "b0sign": np.sign(self.data["BCENTR"]),
                }
            )
        else:
            self.cocos = self._set_cocos(self.data)

        logger.info(
            "GEQDSK COCOS: \n%s",
            pformat(self.cocos.__dict__, indent=2, sort_dicts=False),
        )

        # 4. Compute transformation coeff.
        self.coef = self.cocos.values_coefficients(
            self.cocos.COCOS,
            IDS_COCOS,
            self.data["CURRENT"],
            self.data["BCENTR"],
            ipsign_out,
            b0sign_out,
        )
        logger.info(
            "GEQDSK Transformation Coeff.: \n%s",
            pformat(self.coef, indent=2, sort_dicts=False),
        )

    def _load(self, fpath):
        """
        Read GEQDSK

        Parameters
        ----------
        fpath: str
            Path to GEQDSK file

        Returns
        -------
        dict
            Information in GEQDSK file
        """

        if not os.path.exists(fpath):
            raise FileNotFoundError(fpath)

        if os.stat(fpath).st_size == 0:
            raise IOError(f"file size is zero: {fpath}")

        try:
            fp = open(fpath, "r")
        except OSError:
            raise IOError(f"cannot open/read file: {fpath}")

        fmt00 = FortranRecordReader("6a8,3i4")
        fmt20 = FortranRecordReader("5e16.9")
        fmt22 = FortranRecordReader("2i5")

        data = {}

        #
        header = fp.readline().rstrip()
        data["TIME"] = self._extract_time(header)
        rec = fmt00.read(header)
        data["CASE"] = rec[0:6]
        if len(header) != 60:
            logger.warning(f"irregular length of header: {len(header)}")
            header = header.split()
            data["IDUM"] = int(header[-3])
            data["NW"] = nw = int(header[-2])
            data["NH"] = nh = int(header[-1])
        else:
            data["IDUM"] = int(header[48:52])
            data["NW"] = nw = int(header[52:56])
            data["NH"] = nh = int(header[56:60])

        #
        rec = np.float64(fmt20.read(fp.readline()))
        data["RDIM"] = rec[0]
        data["ZDIM"] = rec[1]
        data["RCENTR"] = rec[2]
        data["RLEFT"] = rec[3]
        data["ZMID"] = rec[4]

        #
        rec = np.float64(fmt20.read(fp.readline()))
        data["RMAXIS"] = rec[0]
        data["ZMAXIS"] = rec[1]
        data["SIMAG"] = rec[2]
        data["SIBRY"] = rec[3]
        data["BCENTR"] = rec[4]

        #
        rec = np.float64(fmt20.read(fp.readline()))
        data["CURRENT"] = rec[0]
        # data["SIMAG"] = rec[1]
        data["XDUM"] = rec[2]
        # data["RMAXIS"] = rec[3]
        data["XDUM"] = rec[4]

        #
        rec = np.float64(fmt20.read(fp.readline()))
        # data["ZMAXIS"] = rec[0]
        data["XDUM"] = rec[1]
        # data["SIBRY"] = rec[2]
        data["XDUM"] = rec[3]
        data["XDUM"] = rec[4]

        #
        data["FPOL"] = self._read1d(fp, nw, fmt20)
        data["PRES"] = self._read1d(fp, nw, fmt20)
        data["FFPRIM"] = self._read1d(fp, nw, fmt20)
        data["PPRIME"] = self._read1d(fp, nw, fmt20)
        data["PSIRZ"] = np.reshape(self._read1d(fp, nw * nh, fmt20), (nh, nw))
        data["QPSI"] = self._read1d(fp, nw, fmt20)

        #
        rec = [0, 0]
        try:
            rec = np.int32(fmt22.read(fp.readline()))
        except Exception as e:
            logger.debug(f"{e}")
        data["NBBBS"] = nbbbs = rec[0]
        data["LIMITR"] = limitr = rec[1]

        #
        if nbbbs > 0:
            bbbs = np.reshape(self._read1d(fp, 2 * nbbbs, fmt20), (nbbbs, 2))
            data["RBBBS"] = bbbs[:, 0]
            data["ZBBBS"] = bbbs[:, 1]
        else:
            data["RBBBS"] = []
            data["ZBBBS"] = []

        #
        if limitr > 0:
            lim = np.reshape(self._read1d(fp, 2 * limitr, fmt20), (limitr, 2))
            data["RLIM"] = lim[:, 0]
            data["ZLIM"] = lim[:, 1]
        else:
            data["RLIM"] = []
            data["ZLIM"] = []

        return data

    def _read1d(self, fp, nlen, fmt):
        """
        Read array with specified format in Fortran

        Parameters
        ----------
        fp: _io.TextIOWrapper
            file pointer
        nlen: int
            length of record
        fmt: FortranRecordReader

        Returns
        -------
        numpy.ndarray, dtype=numpy.float64
        """

        ret = np.zeros(nlen, dtype=np.float64)
        i = 0
        while i < nlen - 1:
            fdata = fmt.read(fp.readline())
            i2 = min(i + len(fdata), nlen)
            ret[i:i2] = fdata[: i2 - i]
            i = i2

        if i < nlen:
            fdata = fmt.read(fp.readline())
            ret[i:] = fdata[: nlen - i]

        return ret

    def _set_cocos(self, g):
        """
        Compute COCOS for GEQDSK file and Return class COCOS

        Parameters
        ----------
        g: dict
            Information of GEQDSK file

        Returns
        -------
        COCOS
            COCOS index and values
        """

        # Sign(Ip) and Sign(B0) from input
        sigma_ip = np.sign(g["CURRENT"])
        sigma_b0 = np.sign(g["BCENTR"])

        # PSIRZ divided by 2*pi [1], Table 1(a) [2]
        exp_bp = 0

        # Eq.(22) [2]
        sign_psi_edge_axis = np.sign(g["SIBRY"] - g["SIMAG"])
        sigma_bp = int(sign_psi_edge_axis * sigma_ip)

        # Right-handed cylindrical coordinate system [1], Table 1(a) [2]
        sigma_rphi_z = int(+1)

        # Eq.(22), Table 1(b) [2]
        x = np.sign(median(g["QPSI"]))
        if x > 0.0:
            sign_q = int(+1)
        elif x < 0.0:
            sign_q = int(-1)
        else:
            sign_q = int(0)  # raise ValueError in Class COCOS
        sign_q_pos = int(sign_q * sigma_ip * sigma_b0)

        # Eq.(22) [2]
        sigma_rhothetaphi = int(sign_q * sigma_ip * sigma_b0)

        # Eq.(22), Table 1(b) [2]
        x = np.sign(median(g["PPRIME"]))
        if x > 0.0:
            sign_pprime = int(+1)
        elif x < 0.0:
            sign_pprime = int(-1)
        else:
            sign_pprime = int(0)  # raise ValueError in Class COCOS
        sign_pprime_pos = int(sign_pprime * sigma_ip)

        values = {
            "exp_Bp": exp_bp,
            "sigma_Bp": sigma_bp,
            "sigma_RphiZ": sigma_rphi_z,
            "sigma_rhothetaphi": sigma_rhothetaphi,
            "sign_q_pos": sign_q_pos,
            "sign_pprime_pos": sign_pprime_pos,
            "ipsign": sigma_ip,
            "b0sign": sigma_b0,
        }

        return COCOS(values=values)

    def _extract_time(
        self,
        header_line: str,
        skip_if_unit_missing: bool = False,
    ) -> Optional[float]:
        """
        Extracts a time value from header string of GEQDSK file.

        Supported formats:
            - "260ms", "2.6e2(ms)", "150 [s]", "time=1.0", "t = 2 (s)"

        Parameters:
            header_line (str): The header line containing text.
            skip_if_unit_missing (bool): If True, skip values with no unit;
                                         if False, assume seconds.

        Returns:
            float or None: Time in seconds, or None if not found or skipped.
        """

        # Supported unit conversion map
        unit_map = {
            "s": 1e0,
            "ms": 1e-3,
            "us": 1e-6,
            "μs": 1e-6,
            "min": 6e1,
        }

        # Remove trailing integers at the end (e.g., "3 129 129")
        header_line = re.sub(r"(\d+\s+){2,}\d+$", "", header_line.strip())

        # 1. Pattern: numeric value + optional unit
        # (in any brackets, with optional spaces)
        time_regex = re.compile(
            (
                r"(?P<value>[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)"
                r"[\s]*[\(\[\{]?\s*"
                r"(?P<unit>s|ms|us|μs|min)"
                r"\s*[\)\]\}]?"
            ),
            re.IGNORECASE,
        )

        # 2. Pattern: key=value with optional brackets for unit
        # (e.g., t = 2 (s), time=1.[ms])
        key_value_regex = re.compile(
            (
                r"(?:\btime\b|\bt\b)\s*=\s*"
                r"(?P<value>[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)"
                r"(?:\s*[\(\[\{]?\s*"
                r"(?P<unit>s|ms|us|μs|min)\s*[\)\]\}]?)?"
            ),
            re.IGNORECASE,
        )

        # Step 1: Try general value+unit match
        for match in time_regex.finditer(header_line):
            value = float(match.group("value"))
            unit = match.group("unit").lower()
            factor = unit_map.get(unit)
            if factor is not None:
                return value * factor

        # Step 2: Try key=value[unit] match
        for match in key_value_regex.finditer(header_line):
            value = float(match.group("value"))
            unit = match.group("unit")
            if unit:
                factor = unit_map.get(unit.lower())
                if factor is not None:
                    return value * factor
                else:
                    logger.warning(f"Unknown unit: {unit}, skipping.")
                    return None
            else:
                if skip_if_unit_missing:
                    logger.warning(f"No unit found, t={value}; skipping.")
                    return None
                else:
                    logger.warning(f"No unit found, t={value}; assuming sec.")
                    return value

        return None


# ----------------------------------------------------------------------


def map__GEQDSK_to_ids(geqdsk, eq):
    """
    Convert GEQDSK file into IDS/equilibrium

    Parameters
    ----------
    geqdsk: GEQDSK
        Class GEQDSK
    eq: object

    Returns
    ----------
    None
    """

    def common_properties(ids):
        """ """

        ids.ids_properties.homogeneous_time = 1
        ids.ids_properties.creation_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        ids.ids_properties.provider = os.getenv("USER")

        ids.code.name = "IDStools/eqdsk2ids"
        ids.code.repository = "https://github.com/iterorganization/IDStools"
        ids.code.commit = GIT_REV
        ids.code.version = __version__
        ids.code.output_flag.resize(1)
        ids.code.output_flag[0] = 0

    # Abbrev.
    gdsk = geqdsk.data
    coef = geqdsk.coef

    # IDS_COCOS
    cocos = COCOS(index={"COCOS": IDS_COCOS, "ipsign": +1, "b0sign": +1})

    # IDS info.
    common_properties(eq)

    # Set time
    eq.time.resize(1)
    if gdsk["TIME"]:
        eq.time[0] = gdsk["TIME"]
    else:
        eq.time[0] = imas.ids_defs.EMPTY_FLOAT

    # 0D
    eq.time_slice.resize(1)
    eq.time_slice[0].global_quantities.ip = gdsk["CURRENT"] * coef["sigma_Ip_eff"]
    eq.time_slice[0].global_quantities.magnetic_axis.r = gdsk["RMAXIS"]
    eq.time_slice[0].global_quantities.magnetic_axis.z = gdsk["ZMAXIS"]
    eq.time_slice[0].global_quantities.magnetic_axis.b_field_phi = (
        gdsk["FPOL"][0] * coef["sigma_B0_eff"] / gdsk["RMAXIS"]
    )
    eq.time_slice[0].global_quantities.psi_axis = gdsk["SIMAG"] * coef["fact_psi"]
    eq.time_slice[0].global_quantities.psi_boundary = gdsk["SIBRY"] * coef["fact_psi"]

    # vacuume_toroidal_field
    eq.vacuum_toroidal_field.r0 = gdsk["RCENTR"]
    eq.vacuum_toroidal_field.b0.resize(1)
    eq.vacuum_toroidal_field.b0[0] = gdsk["BCENTR"] * coef["sigma_B0_eff"]

    # 1D
    nw = gdsk["NW"]
    nh = gdsk["NH"]
    eq.time_slice[0].profiles_1d.dpressure_dpsi.resize(nw)
    eq.time_slice[0].profiles_1d.f_df_dpsi.resize(nw)
    eq.time_slice[0].profiles_1d.f.resize(nw)
    eq.time_slice[0].profiles_1d.pressure.resize(nw)
    eq.time_slice[0].profiles_1d.q.resize(nw)
    eq.time_slice[0].profiles_1d.psi.resize(nw)

    eq.time_slice[0].profiles_1d.dpressure_dpsi = gdsk["PPRIME"] / coef["fact_psi"]
    eq.time_slice[0].profiles_1d.f_df_dpsi = gdsk["FFPRIM"] / coef["fact_psi"]
    eq.time_slice[0].profiles_1d.f = gdsk["FPOL"] * coef["sigma_B0_eff"]
    eq.time_slice[0].profiles_1d.pressure = gdsk["PRES"]
    eq.time_slice[0].profiles_1d.q = gdsk["QPSI"] * coef["fact_q"]
    simag = gdsk["SIMAG"]
    sibry = gdsk["SIBRY"]
    for i in range(nw):
        psi_val = (1.0 - float(i) / float(nw - 1)) * (simag - sibry) + sibry
        eq.time_slice[0].profiles_1d.psi[i] = psi_val * coef["fact_psi"]

    # Boundary
    if gdsk["NBBBS"] > 0:
        eq.time_slice[0].boundary.outline.r.resize(gdsk["NBBBS"])
        eq.time_slice[0].boundary.outline.z.resize(gdsk["NBBBS"])
        eq.time_slice[0].boundary.outline.r = gdsk["RBBBS"]
        eq.time_slice[0].boundary.outline.z = gdsk["ZBBBS"]

    # 2D
    eq.time_slice[0].profiles_2d.resize(1)
    eq.time_slice[0].profiles_2d[0].grid_type.index = 1
    eq.time_slice[0].profiles_2d[0].grid.dim1.resize(nw)
    eq.time_slice[0].profiles_2d[0].grid.dim2.resize(nh)
    eq.time_slice[0].profiles_2d[0].psi.resize(nw, nh)
    eq.time_slice[0].profiles_2d[0].r.resize(nw, nh)
    eq.time_slice[0].profiles_2d[0].z.resize(nw, nh)
    eq.time_slice[0].profiles_2d[0].b_field_r.resize(nw, nh)
    eq.time_slice[0].profiles_2d[0].b_field_z.resize(nw, nh)
    for i in range(nw):
        eq.time_slice[0].profiles_2d[0].grid.dim1[i] = float(i) / float(nw - 1) * gdsk["RDIM"] + gdsk["RLEFT"]
    for j in range(nh):
        eq.time_slice[0].profiles_2d[0].grid.dim2[j] = (
            float(j) / float(nh - 1) * gdsk["ZDIM"] - 0.5 * gdsk["ZDIM"] + gdsk["ZMID"]
        )
    for j in range(nh):
        for i in range(nw):
            eq.time_slice[0].profiles_2d[0].psi[i, j] = gdsk["PSIRZ"][j, i] * coef["fact_psi"]
    for j in range(nh):
        for i in range(nw):
            eq.time_slice[0].profiles_2d[0].r[i, j] = eq.time_slice[0].profiles_2d[0].grid.dim1[i]
            eq.time_slice[0].profiles_2d[0].z[i, j] = eq.time_slice[0].profiles_2d[0].grid.dim2[j]
    # Eq. (19)
    fact = cocos.sigma_rphi_z * cocos.sigma_bp / (2.0 * np.pi) ** cocos.exp_bp
    dim1 = eq.time_slice[0].profiles_2d[0].grid.dim1
    dim2 = eq.time_slice[0].profiles_2d[0].grid.dim2
    for i in range(nw):
        psi = eq.time_slice[0].profiles_2d[0].psi[i, :]
        br = np.gradient(psi, dim2, edge_order=2) / dim1[i]
        eq.time_slice[0].profiles_2d[0].b_field_r[i, :] = br[:] * fact
    for j in range(nh):
        psi = eq.time_slice[0].profiles_2d[0].psi[:, j]
        bz = np.gradient(psi, dim1, edge_order=2) / dim1[:]
        eq.time_slice[0].profiles_2d[0].b_field_z[:, j] = bz[:] * fact * -1.0

    # Bphi computation
    eq.time_slice[0].profiles_2d[0].b_field_phi.resize(nw, nh)
    psi_1d = np.array(eq.time_slice[0].profiles_1d.psi)
    f_1d = np.array(eq.time_slice[0].profiles_1d.f)
    psi_2d = np.array(eq.time_slice[0].profiles_2d[0].psi)
    r_1d = np.array(eq.time_slice[0].profiles_2d[0].grid.dim1)
    if psi_1d[0] < psi_1d[-1]:

        def f_of_psi(p):
            return np.interp(p, psi_1d, f_1d, right=f_1d[-1])

    else:

        def f_of_psi(p):
            return np.interp(p, psi_1d[::-1], f_1d[::-1], right=f_1d[-1])

    for i in range(nw):
        eq.time_slice[0].profiles_2d[0].b_field_phi[i, :] = f_of_psi(psi_2d[i, :]) / r_1d[i]

    logger.debug("IDS/equilibrium: \n%s", pformat(eq, indent=2, sort_dicts=False))


# ----------------------------------------------------------------------


def merge_equilibrium(eq1, eq2, sort_by_time=True):
    """
    Concatenate two IMAS IDS/equilibrium objects (eq1 appended after eq2),
    with an option to sort the resulting time slices by time.

    Parameters
    ----------
    eq1 : object
        The equilibrium IDS to append.
    eq2 : object
        The base equilibrium IDS.
    sort_by_time : bool, optional
        If True, the resulting IDS will be sorted by time (default: True).

    Returns
    -------
    eq : object
        New IDS/equilibrium instance with combined (and optionally sorted)
        content.
    """

    if eq1 is None or eq2 is None:
        raise ValueError("Both eq1 and eq2 must be valid IDS/equilibrium objects.")

    # Prepare new equilibrium IDS
    eq = imas.IDSFactory().equilibrium()

    n1 = len(eq1.time)
    n2 = len(eq2.time)
    n_total = n1 + n2

    eq.time.resize(n_total)
    eq.time_slice.resize(n_total)
    eq.vacuum_toroidal_field.b0.resize(n_total)
    eq.code.output_flag.resize(n_total)

    eq.ids_properties = deepcopy(eq1.ids_properties)
    eq.code.name = eq1.code.name
    eq.code.repository = eq1.code.repository
    eq.code.commit = eq1.code.commit
    eq.code.version = eq1.code.version

    # Copy time slices from both sources
    for i in range(n2):
        eq.time[i] = eq2.time[i]
        eq.time_slice[i] = deepcopy(eq2.time_slice[i])
        eq.vacuum_toroidal_field.b0[i] = eq2.vacuum_toroidal_field.b0[i]
        eq.code.output_flag[i] = eq2.code.output_flag[i]

    for i in range(n1):
        idx = i + n2
        eq.time[idx] = eq1.time[i]
        eq.time_slice[idx] = deepcopy(eq1.time_slice[i])
        eq.vacuum_toroidal_field.b0[idx] = eq1.vacuum_toroidal_field.b0[i]
        eq.code.output_flag[idx] = eq1.code.output_flag[i]

    if sort_by_time:
        eqw = deepcopy(eq)
        # Sort all fields by ascending time
        sorted_indices = np.argsort(eq.time[:])
        for i, j in enumerate(sorted_indices):
            eq.time[i] = eqw.time[j]
            eq.time_slice[i] = eqw.time_slice[j]
            eq.vacuum_toroidal_field.b0[i] = eqw.vacuum_toroidal_field.b0[j]
            eq.code.output_flag[i] = eqw.code.output_flag[j]

    return eq


# ----------------------------------------------------------------------


def geqdsk2ids(fpath, ipsign=0, b0sign=0, cocos_in=None):
    """
    Functional Interface of GEQDSK Converter (geqdsk2ids)

    Parameters
    ----------
    fpath: str
        Path to GEQDSK file
    ipsign: int=0, optional
        Desired sign(Ip) in output
    b0sign: int=0, optional
        Desired sign(B0) in output
    cocos_in: int=None, optional
        Coerce input COCOS

    Returns
    -------
    eq: ``imas_*_ual_*``.equilibrium.equilibrium ('*' corresponds to IMAS/UAL ver.)
        IDS/equilibrium
    """

    # Read GEQDSK file
    logger.info("loading GEQDSK file ...")
    geqdsk = GEQDSK(fpath, ipsign, b0sign, cocos_in)

    # Map GEQDSK to IDS/equilibrium
    logger.info("mapping GEQDSK to IDS/equilibrium ...")
    eq = imas.ids_factory.IDSFactory().equilibrium()
    map__GEQDSK_to_ids(geqdsk, eq)

    # Compute COCOS in output IDS/equilibrium
    cocos = compute_COCOS(eq)
    logger.info("COCOS values in output IDS/equilibrium: \n%s", pformat(cocos, indent=2))

    # Check if COCOS is equal to IDS_COCOS
    if cocos["COCOS"] != IDS_COCOS:
        logger.warning("COCOS Target= {}, Output= {}, Input= {}".format(IDS_COCOS, cocos["COCOS"], geqdsk.cocos.COCOS))
        raise SystemExit("Input COCOS is inconsistent between GEQDSK file and COCOS with the option '--cocos_in'.")

    return eq


# ----------------------------------------------------------------------


def _expand_file_patterns(pattern: str) -> List[str]:
    """
    Expand a file pattern to a list of matching files.

    Parameters
    ----------
    pattern : str
        File pattern that can be:
        - A single file path
        - A directory path
        - A glob pattern with wildcards

    Returns
    -------
    List[str]
        List of matching file paths
    """
    # Expand environment variables and user home directory
    expanded = os.path.expanduser(os.path.expandvars(pattern))

    # Check if it's an existing file
    if os.path.isfile(expanded):
        return [os.path.abspath(expanded)]

    # Check if it's an existing directory
    if os.path.isdir(expanded):
        abs_dir = os.path.abspath(expanded)
        return [
            os.path.join(abs_dir, fname)
            for fname in sorted(os.listdir(abs_dir))
            if os.path.isfile(os.path.join(abs_dir, fname))
        ]

    # Try glob expansion for patterns with wildcards
    matches = glob.glob(expanded)
    if matches:
        # Filter to only include files (not directories)
        return [os.path.abspath(match) for match in sorted(matches) if os.path.isfile(match)]

    # If no matches found, raise an error
    raise FileNotFoundError(f"No files found matching pattern: {pattern}")


def eqdsk2ids(
    gfile: Union[str, List[str], None] = None,
    afile: Optional[str] = None,
    ipsign: int = 0,
    b0sign: int = 0,
    cocos_in: Optional[int] = None,
) -> "imas.ids.equilibrium.equilibrium":
    """
    Convert one or more GEQDSK files into a merged IMAS equilibrium IDS.

    Parameters
    ----------
    gfile : str, list of str, optional
        Path(s) to GEQDSK file(s). Can be:
        - Single file path
        - Directory path (all files processed)
        - Space-separated string of multiple files/patterns
        - List of file paths
        - Glob pattern(s) with wildcards (``*``, ``?``, ``[]``)
    afile : str, optional
        Path to AEQDSK file (currently not used).
    ipsign : int, default=0
        Desired sign of plasma current (Ip) in the output.
    b0sign : int, default=0
        Desired sign of toroidal field (B0) in the output.
    cocos_in : int or None, optional
        Input COCOS convention to coerce. None means autodetect.

    Returns
    -------
    eq : imas.ids.equilibrium.equilibrium
        Combined equilibrium IDS from one or more GEQDSK files.
    """

    if not gfile:
        raise ValueError("No GEQDSK file(s) provided.")

    file_list: List[str] = []

    # Handle different input types
    if isinstance(gfile, list):
        # If it's already a list, process each element
        for item in gfile:
            file_list.extend(_expand_file_patterns(item))
    elif isinstance(gfile, str):
        # If it's a string, it could be space-separated or a single path
        if " " in gfile:
            # Split by whitespace and expand each part
            parts = gfile.split()
            for part in parts:
                file_list.extend(_expand_file_patterns(part))
        else:
            # Single string - could be file, dir, or pattern
            file_list.extend(_expand_file_patterns(gfile))
    else:
        raise TypeError("gfile must be a string or list of strings")

    if not file_list:
        raise FileNotFoundError(f"No GEQDSK files found matching: {gfile}")

    # Sort the file list for consistent processing order
    file_list = sorted(set(file_list))  # Remove duplicates and sort
    logger.info(f"Processing {len(file_list)} GEQDSK files: {file_list}")

    # Initialize empty equilibrium IDS
    eq = imas.IDSFactory().equilibrium()

    # Convert and merge each GEQDSK file
    for fpath in file_list:
        geq = geqdsk2ids(fpath, ipsign=ipsign, b0sign=b0sign, cocos_in=cocos_in)
        eq = merge_equilibrium(geq, eq, sort_by_time=True)

    return eq
