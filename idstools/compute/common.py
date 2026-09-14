"""
This is a common module which has mathematical or physics functions

"""

import logging
from typing import Any, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("module")


def get_compat_attr(node: Any, *names: str) -> Optional[Any]:
    """
    Return the first attribute among `names` that exists on `node`.

    This is a Data Dictionary version compatibility helper: some quantities were
    renamed between DD3 and DD4 (e.g. ``j_tor`` -> ``j_phi``). Passing both names,
    in preferred order, returns whichever one is actually present on the IDS node.

    Args:
        node (Any): The IDS node (e.g. a `profiles_1d`, `profiles_2d[i]` or `ggd[i]`
            structure) to look up the attribute on.
        *names (str): One or more candidate attribute names, checked in order.

    Returns:
        Optional[Any]: The value of the first attribute found, or None if none of
            `names` exist on `node`.

    Example:
        >>> j_tor = get_compat_attr(time_slice.profiles_1d, "j_tor", "j_phi")
    """
    for name in names:
        if hasattr(node, name):
            return getattr(node, name)
    return None


def find_nearest(a, a0):
    """
    Find the element in an n-dimensional array closest to a scalar value.

    Args:
        a (np.ndarray): Input array of any shape or dimension.
        a0 (float): The scalar value to find the nearest element to.

    Returns:
        tuple: A tuple containing:
            - The value of the element in array `a` closest to `a0`
            - The flat index of that element
    """
    idx = abs(a - a0).argmin()
    return a.flat[idx], idx


def get_nearest_time(time_array: np.ndarray, requested_time: float) -> Tuple[int, float]:
    """
    The function `get_nearest_time` takes an array of time values and a requested time, and returns the index
    and value of the nearest time in the array to the requested time.

    Args:
        time_array (np.ndarray): The `time_array` parameter is a numpy array containing a list of time values.
        requested_time (float): The `requestedTime` parameter is the time value that you want to find the
            nearest value to in the `time_array`.

    Returns:
        The function `get_nearest_time` returns a tuple containing the time index and time value.
    """
    ntime = len(time_array)
    if ntime >= 1:
        if requested_time >= 0:
            idx = int(abs(time_array - requested_time).argmin())
            [time_value, time_index] = time_array.flat[idx], idx
        else:
            time_index = ntime // 2
            time_value = time_array[time_index]
        requested_time = time_value
        if ntime > 1:
            logger.info(f"Time  = {time_value:.3f} s in range [{time_array[0]:.2f},{time_array[ntime - 1]}] s")
            logger.info(f"Index = {time_index}")
            logger.info(
                f"Averaged resolution = {(time_array[ntime - 1] - time_array[0]) / (ntime - 1)} s",
            )
        else:
            logger.info(f"Time  = {time_value:.3f} s")
    else:
        time_value = time_array[0] if len(time_array) > 0 else 0
        time_index = 0
    return time_index, time_value


def get_closest_of_given_value_from_array(array: np.ndarray, value: float) -> Union[None, tuple]:
    """
    Find the index of the element in the array that is closest to the given value using the minimum absolute
    difference.

    Args:
        array (np.ndarray): A NumPy array of numbers.
        value (float): The value to which we want to find the nearest element in the array.

    Returns:
        The function `get_closest_of_given_value_from_array` returns a tuple containing the index of
        the element in the input `array` that
        is closest to the input `value`, and the value of that element. If the input `array` is `None` or empty,
        the function returns `None`.
    """
    if array is None:
        return None
    if len(array) == 0:
        return None
    index = abs(array - value).argmin()
    return index, array[index]


def get_middle_element_from_array(array: np.ndarray) -> Union[None, tuple]:
    """
    The "get_middle_element_from_array" function returns the index and value of the middle element in a
    given numpy array.

    Args:
        array (np.ndarray): A NumPy array for which we want to find the middle element.

    Returns:
        The function `get_middle_element_from_array` takes a numpy array as input and returns a tuple
        containing the index and value
        of the middle element of the array. If the input array is None or empty, the function returns None.
    """
    if array is None:
        return None
    if len(array) == 0:
        return None
    length = len(array)
    index = length // 2
    value = array[index]
    return index, value


# TODO rename variable and refactor code in smaller reusable methods
def xyz2cyl(rvec):
    """
    The function converts a set of 3D Cartesian coordinates to cylindrical coordinates.

    Args:
        rvec: rvec is a numpy array containing the coordinates of points in 3D space in the Cartesian
            coordinate system (x, y, z). The function xyz2cyl converts these coordinates to cylindrical
            coordinates (r, phi, z) and returns them as a numpy array with the same shape as the `rvec`

    Returns:
        The function `xyz2cyl` returns a numpy array `rcyl` which contains the cylindrical coordinates
        (radius, azimuthal angle, and height) of the input vector `rvec` which is in Cartesian coordinates.

    .. todo: need to refactor naming of the variables
    """
    rvec_shape = rvec.shape
    rcyl = np.reshape(rvec, (-1, 3))
    r = np.sqrt(rcyl[:, 0] ** 2 + rcyl[:, 1] ** 2)
    phi = np.arctan2(rcyl[:, 1], rcyl[:, 0], dtype=np.double)
    ind_phi = np.where(phi < 0.0)[0]
    if ind_phi.shape[0] > 0:
        phi[ind_phi] = phi[ind_phi] + 2 * np.pi
    rcyl[:, 0] = r
    rcyl[:, 1] = phi
    rcyl = np.reshape(rcyl, rvec_shape)
    return rcyl


# TODO rename variable
def cyl2xyz(rcyl):
    """
    The function cyl2xyz converts cylindrical coordinates to Cartesian coordinates.

    Args:
        rcyl: rcyl is a numpy array containing cylindrical coordinates (r, theta, z) of points in 3D space.
            The function cyl2xyz converts these cylindrical coordinates to Cartesian coordinates (x, y, z) and
            returns a numpy array of the same shape as rcyl.

    Returns:
        The function `cyl2xyz` returns a numpy array with the same shape as the input `rcyl` array, but with
        the cylindrical coordinates converted to Cartesian coordinates.
    """
    rcyl_shape = rcyl.shape
    rvec = np.reshape(rcyl, (-1, 3))
    x = rvec[:, 0] * np.cos(rvec[:, 1])
    rvec[:, 1] = rvec[:, 0] * np.sin(rvec[:, 1])
    rvec[:, 0] = x
    rvec = np.reshape(rvec, rcyl_shape)
    return rvec


def find_minima(y):
    """
    Find the indices of local minima in a 1D array.

    A point is considered a local minimum if it is lower than its neighbors
    at distances t = len(y)//50 and immediate neighbors.

    Args:
        y (np.ndarray or list): 1D array of values.

    Returns:
        list: List of indices where local minima occur in the input array.
    """
    # mindex = sig.argrelextrema(y,np.less)
    mindex = []
    t = len(y) // 50
    for i in range(t, len(y) - t):
        if y[i - t] > y[i - 1] > y[i] < y[i + 1] < y[i + t]:
            mindex.append(i)
    return mindex


def find_maxima(y):
    """
    Find the indices of local maxima in a 1D array.

    A point is considered a local maximum if it is higher than its neighbors
    at distances t = len(y)//50 and immediate neighbors.

    Args:
        y (np.ndarray or list): 1D array of values.

    Returns:
        list: List of indices where local maxima occur in the input array.
    """
    # maxdex = sig.argrelextrema(y,np.greater)
    maxdex = []
    t = len(y) // 50
    for i in range(t, len(y) - t):
        if y[i - t] < y[i - 1] < y[i] > y[i + 1] > y[i + t]:
            maxdex.append(i)
    return maxdex


def findfwhm(x, y, maxind, lowbnd, uppbnd):
    """
    Calculate the Full Width at Half Maximum (FWHM) of a peak in a dataset.

    The FWHM is the width of the curve at half the maximum height of a peak.
    This function finds the x-axis span between the two points at half the peak height.

    Args:
        x (np.ndarray): X-axis values (independent variable).
        y (np.ndarray): Y-axis values (dependent variable/signal).
        maxind (int): Index of the maximum value (peak) in the array.
        lowbnd (int): Lower boundary index for the peak region.
        uppbnd (int): Upper boundary index for the peak region.

    Returns:
        float: The Full Width at Half Maximum value (difference in x between
            left and right points at half max height).
    """
    npyleft = np.array(y[lowbnd:maxind])
    npyright = np.array(y[maxind:uppbnd])
    lindex = lowbnd + find_nearest(npyleft, y[maxind] / 2)[1]
    rindex = maxind + find_nearest(npyright, y[maxind] / 2)[1]
    fwhm = x[rindex] - x[lindex]
    return fwhm


# TODO rename variable and refactor code in smaller reusable methods
def line_polygon_intersection(  # input
    line_p,  # arbitrary point on line (3D) [*,3]
    line_dir,  # direction of line  (3D)
    polygon_data,  # input polygon as 2D-array
    # output
    # n_xp,         # number of intersections
    # xp_data,      # countour intersection
    # (max 2, sorted by distance)
    # structured array, see below
    # keyword parameter
    close=True,
):
    """
    This function calculates the intersection points between a line and a polygon.

    Args:
        line_p: A numpy array representing the starting point of the line segment(s) to be intersected
            with the polygon. It has shape (n,3) where n is the number of line segments and each row
            represents the x, y, z coordinates of the starting point of the line segment.
        line_dir: The direction vector(s) of the line(s) for which intersection with the polygon is
            being calculated. It is a numpy array of shape (n,3) where n is the number of lines and each
            row represents the direction vector of a line.
            polygon_data: The coordinates of the vertices of a polygon in 3D space.
        close: A boolean parameter that determines whether the polygon is closed or not. If set to
            True (default), the polygon is assumed to be closed, otherwise, it is assumed to be open.
            Defaults to True

    Returns:
        two arrays: n_xp and xp_data.

    .. todo: need to refactor this code and the documentation
    """
    # routine to provide points of intersection between contour polygon(2D)
    # and specified line (3D)
    # toroidal symmetry assumed
    # eg (diagnostics line of sight) intersection (vessel contour)

    # data format / coordinate systems
    # line_p [*,3] : x,y,z 3D-cartesian
    # polygon_data (*,2) : R,z 2D-poloidal plane
    inshape = line_p.shape
    line_p = np.reshape(line_p, (-1, 3))
    line_dir = np.reshape(line_dir, (-1, 3))

    # input dimensions
    line_p_dim = len(line_p)
    # output arrays
    n_xp = np.zeros(line_p_dim, dtype=np.int_)
    xp_dt = np.dtype(
        [
            ("icorner", np.int_),
            ("lambda_ray", np.double),
            ("lambda_pol", np.double),
            ("r_hit", np.double, 3),
            ("r_cyl", np.double, 3),
            ("k_dot_n", np.double),
            ("n_c", np.double, 3),
        ]
    )
    xp_data = np.zeros((line_p_dim, 2), dtype=xp_dt)

    # edge structure of polygon
    # careful this implies that the polygone is open
    # otherwise one has to repeat the first point at the end
    # or set the keyword close=True (default)
    n_polygon = len(polygon_data)
    if close:
        n_edges = n_polygon
        cp_edges = np.vstack([polygon_data, polygon_data[0, :]])
    else:
        n_edges = n_polygon - 1
        cp_edges = polygon_data  # since no writing to cp_edges, copy not necessary

    #   loop line_p
    for i_line_p in range(line_p_dim):
        eg = line_dir[i_line_p, :].copy()  # old : r
        eg = eg / np.sqrt(np.sum(eg**2))  # normalize eg
        rg = line_p[i_line_p, :]  # old : x0
        # loop polygon edges
        s_arr = np.ones((2 * n_edges, 11), dtype=np.double) * -1
        rg_r2 = rg[0] ** 2 + rg[1] ** 2  # useful for cc, old x01_x02
        eg_r2 = eg[0] ** 2 + eg[1] ** 2
        egz2 = eg[2] ** 2
        rgegxy = rg[0] * eg[0] + rg[1] * eg[1]
        for i_s in range(n_edges):
            dzrg1 = rg[2] - cp_edges[i_s, 1]
            dz21 = cp_edges[i_s + 1, 1] - cp_edges[i_s, 1]
            dz212 = dz21**2
            d_r21 = cp_edges[i_s + 1, 0] - cp_edges[i_s, 0]
            d_r212 = d_r21**2
            d_rz21 = d_r21 * dz21
            # coefficients of quadratic equation
            aa = dz212 * eg_r2 - d_r212 * egz2
            bb = 2 * (dz212 * rgegxy - d_r212 * eg[2] * dzrg1 - eg[2] * cp_edges[i_s, 0] * d_rz21)
            cc = dz212 * (rg_r2 - cp_edges[i_s, 0] ** 2) - d_r212 * (dzrg1**2) - 2 * cp_edges[i_s, 0] * d_rz21 * dzrg1
            if aa**2 < 1.0e-12:  # assume aa is zero
                if dz212 * egz2 < 1.0e-10:
                    # error: segment is horizontal plate and line is horizontal
                    s_arr[2 * i_s, 1] = -2
                    s_arr[2 * i_s + 1, 1] = -2
                if d_r212 * eg_r2 < 1.0e-10:
                    # error: segment is vertical cylinder and line is vertical
                    s_arr[2 * i_s, 1] = -3
                    s_arr[2 * i_s + 1, 1] = -3
                else:
                    # [egR,egz] (direction of line) parallel to
                    # [dr21, dz21] polygone segment
                    # the plane normal to  [egx,egy,egz] x [egy,-egx,0] through rg
                    # cuts the cone in a parabola : only one solution
                    # s_arr[:,1] : lambda_pol *(r2-r1) = [rR,rz] - r1
                    s_arr[2 * i_s, 1] = -cc / bb  # lambda_ray * eg +rg = r
                    if s_arr[2 * i_s, 1] >= 0.0:
                        rvec = s_arr[2 * i_s, 1] * eg + rg
                        # must lie on cone: radial component rR
                        r_r = np.sqrt(rvec[0] ** 2 + rvec[1] ** 2)
                        dr_r1 = r_r - cp_edges[i_s, 0]
                        drz1 = rvec[2] - cp_edges[i_s, 1]
                        # note that mathematically we are dealing with a double cone
                        # with a singularity somewhere on the z-axis
                        # first we check if our solution lies on the same side
                        # of the cone
                        # as our polygone segment by calculating the cross product
                        # (r2-r1)x(r-r1)
                        # if small enough,
                        # i.e. |dR21*drz1-dz21*drR1|/(dR212+dz212) < 1E-6
                        # we calculate lambda_pol by the normalized dot product
                        # (r2-r1)dot(r-r1)/(r2-r1)^2
                        if np.abs(d_r21 * drz1 - dz21 * dr_r1) / (d_r212 + dz212) < 1.0e-6:
                            s_arr[2 * i_s, 0] = (dr_r1 * d_r21 + drz1 * dz21) / (d_r212 + dz212)
                        # this is lambda_pol, must be between 0 and 1
                        # if segment is relevant
                        if s_arr[2 * i_s, 0] >= 0.0 and s_arr[2 * i_s, 0] < 1.0:
                            # later it is helpful if 0 < lambda_pol < |r2-r1|
                            s_arr[2 * i_s, 0] = s_arr[2 * i_s, 0] * np.sqrt(d_r212 + dz212)
                            r_phi = np.arctan2(rvec[1], rvec[0], dtype=np.double)
                            if r_phi < 0:
                                r_phi = r_phi + 2 * np.pi  # 0 <= rPhi < 2pi
                            # normal on cone segment at rvex
                            n_c = np.array(
                                [dz21 * np.cos(r_phi), dz21 * np.sin(r_phi), -d_r21],
                                dtype=np.double,
                            )
                            n_c = n_c / np.sqrt(np.sum(n_c**2))  # normalize n_c
                            s_arr[2 * i_s, 2] = np.dot(eg, n_c)
                            if s_arr[2 * i_s, 2] < 0:
                                n_c = -n_c
                                s_arr[2 * i_s, 2] = -s_arr[2 * i_s, 2]
                            s_arr[2 * i_s, 3:6] = rvec
                            s_arr[2 * i_s, 6] = r_r
                            s_arr[2 * i_s, 7] = r_phi
                            s_arr[2 * i_s, 8:11] = n_c
                    s_arr[2 * i_s + 1, 1] = -4
            else:
                det = bb**2 - 4 * aa * cc
                if det >= 0.0:
                    # calculate lambda_ray
                    s_arr[2 * i_s, 1] = (-bb + np.sqrt(det)) / (2.0 * aa)
                    s_arr[2 * i_s + 1, 1] = (-bb - np.sqrt(det)) / (2.0 * aa)
                    # if lambda_ray >= 0, calculate lambda_pol
                    if s_arr[2 * i_s, 1] >= 0.0:
                        rvec = s_arr[2 * i_s, 1] * eg + rg
                        # print(rvec)
                        r_r = np.sqrt(rvec[0] ** 2 + rvec[1] ** 2)
                        dr_r1 = r_r - cp_edges[i_s, 0]
                        drz1 = rvec[2] - cp_edges[i_s, 1]
                        # note that mathematically we are dealing with a double cone
                        # with a singularity somewhere on the z-axis
                        # first we check if our solution lies on the same side
                        # of the cone
                        # as our polygone segment by calculating the cross product
                        # (r2-r1)x(r-r1)
                        # if small enough, i.e.
                        # |dR21*drz1-dz21*drR1|/(dR212+dz212) < 1E-6
                        # we calculate lambda_pol by the normalized dot product
                        # (r2-r1)dot(r-r1)/(r2-r1)^2
                        if np.abs(d_r21 * drz1 - dz21 * dr_r1) / (d_r212 + dz212) < 1.0e-6:
                            s_arr[2 * i_s, 0] = (dr_r1 * d_r21 + drz1 * dz21) / (d_r212 + dz212)
                        # this is lambda_pol, must be between 0 and 1 if relevant
                        if s_arr[2 * i_s, 0] >= 0.0 and s_arr[2 * i_s, 0] < 1.0:
                            # later it is helpful if 0 < lambda_pol < |r2-r1|
                            s_arr[2 * i_s, 0] = s_arr[2 * i_s, 0] * np.sqrt(d_r212 + dz212)
                            r_phi = np.arctan2(rvec[1], rvec[0], dtype=np.double)
                            if r_phi < 0:
                                r_phi = r_phi + 2 * np.pi
                            # normal on cone segment at rvex
                            n_c = np.array(
                                [dz21 * np.cos(r_phi), dz21 * np.sin(r_phi), -d_r21],
                                dtype=np.double,
                            )
                            n_c = n_c / np.sqrt(np.sum(n_c**2))  # normalize n_c
                            s_arr[2 * i_s, 2] = np.dot(eg, n_c)
                            if s_arr[2 * i_s, 2] < 0:
                                n_c = -n_c
                                s_arr[2 * i_s, 2] = -s_arr[2 * i_s, 2]
                            s_arr[2 * i_s, 3:6] = rvec
                            s_arr[2 * i_s, 6] = r_r
                            s_arr[2 * i_s, 7] = r_phi
                            s_arr[2 * i_s, 8:11] = n_c
                    if s_arr[2 * i_s + 1, 1] >= 0.0:
                        rvec = s_arr[2 * i_s + 1, 1] * eg + rg
                        r_r = np.sqrt(rvec[0] ** 2 + rvec[1] ** 2)
                        dr_r1 = r_r - cp_edges[i_s, 0]
                        drz1 = rvec[2] - cp_edges[i_s, 1]
                        # note that mathematically we are dealing with a double cone
                        # with a singularity somewhere on the z-axis
                        # first we check if our solution lies on the same side
                        # of the cone
                        # as our polygone segment by calculating the cross product
                        # (r2-r1)x(r-r1)
                        # if small enough,
                        # i.e. |dR21*drz1-dz21*drR1|/(dR212+dz212) < 1E-6
                        # we calculate lambda_pol by the normalized dot product
                        # (r2-r1)dot(r-r1)/(r2-r1)^2
                        if np.abs(d_r21 * drz1 - dz21 * dr_r1) / (d_r212 + dz212) < 1.0e-6:
                            s_arr[2 * i_s + 1, 0] = (dr_r1 * d_r21 + drz1 * dz21) / (d_r212 + dz212)
                        if s_arr[2 * i_s + 1, 0] >= 0.0 and s_arr[2 * i_s + 1, 0] < 1.0:
                            # later it is helpful if 0 < lambda_pol < |r2-r1|
                            s_arr[2 * i_s + 1, 0] = s_arr[2 * i_s + 1, 0] * np.sqrt(d_r212 + dz212)
                            r_phi = np.arctan2(rvec[1], rvec[0], dtype=np.double)
                            if r_phi < 0:
                                r_phi = r_phi + 2 * np.pi
                            # normal on cone segment at rvec
                            n_c = np.array(
                                [dz21 * np.cos(r_phi), dz21 * np.sin(r_phi), -d_r21],
                                dtype=np.double,
                            )
                            n_c = n_c / np.sqrt(np.sum(n_c**2))  # normalize n_c
                            s_arr[2 * i_s + 1, 2] = np.dot(eg, n_c)
                            if s_arr[2 * i_s + 1, 2] < 0:
                                n_c = -n_c
                                s_arr[2 * i_s + 1, 2] = -s_arr[2 * i_s + 1, 2]
                            s_arr[2 * i_s + 1, 3:6] = rvec
                            s_arr[2 * i_s + 1, 6] = r_r
                            s_arr[2 * i_s + 1, 7] = r_phi
                            s_arr[2 * i_s + 1, 8:11] = n_c
        # endfor ; end loop polygon edges
        # find 'useful' lambda_pol values, in that case n_c was calculated and
        # s_arr[:,2] = |n_c|
        # otherwise s_arr[:,2] is -1 as preset
        ind_xp = np.where(s_arr[:, 2] >= 0.0)[0]
        nxp = len(ind_xp)
        # nxp sometimes above two: choose two lowest values
        # (depends on shape of polygon)
        ixp1 = np.int_(-1)
        ixp2 = np.int_(-1)
        if nxp == 1:
            ixp1 = ind_xp[0]
        if nxp >= 2:
            isort_xp = np.argsort(s_arr[ind_xp, 1])
            ixp1 = ind_xp[isort_xp[0]]
            ixp2 = ind_xp[isort_xp[1]]
        # endif
        # write output
        n_xp[i_line_p] = nxp
        if nxp > 0:
            xp_data[i_line_p, 0]["lambda_ray"] = s_arr[ixp1, 1]
            xp_data[i_line_p, 0]["lambda_pol"] = s_arr[ixp1, 0]
            xp_data[i_line_p, 0]["r_hit"] = s_arr[ixp1, 3:6]
            xp_data[i_line_p, 0]["r_cyl"] = [
                s_arr[ixp1, 6],
                s_arr[ixp1, 7],
                s_arr[ixp1, 5],
            ]
            xp_data[i_line_p, 0]["k_dot_n"] = s_arr[ixp1, 2]
            xp_data[i_line_p, 0]["n_c"] = s_arr[ixp1, 8:11]
            xp_data[i_line_p, 0]["icorner"] = ixp1 // 2
        if nxp > 1:
            xp_data[i_line_p, 1]["lambda_ray"] = s_arr[ixp2, 1]
            xp_data[i_line_p, 1]["lambda_pol"] = s_arr[ixp2, 0]
            xp_data[i_line_p, 1]["r_hit"] = s_arr[ixp2, 3:6]
            xp_data[i_line_p, 1]["r_cyl"] = [
                s_arr[ixp2, 6],
                s_arr[ixp2, 7],
                s_arr[ixp2, 5],
            ]
            xp_data[i_line_p, 1]["k_dot_n"] = s_arr[ixp2, 2]
            xp_data[i_line_p, 1]["n_c"] = s_arr[ixp2, 8:11]
            xp_data[i_line_p, 1]["icorner"] = ixp2 // 2
    # endfor  end loop line_p

    line_p = np.reshape(line_p, inshape)
    line_dir = np.reshape(line_dir, inshape)
    nxpshape = inshape[0 : len(inshape) - 1]
    n_xp = np.reshape(n_xp, nxpshape)
    xp_data = np.reshape(xp_data, nxpshape + tuple([2]))
    return n_xp, xp_data


def calcw(wt, rt, lambda_ray, freq=np.double(170.0e9)):
    """
    The function calculates the width of a laser beam based on its initial width, curvature radius, length
    along the ray, and frequency.

    Args:
        wt: width at the start point of the ray in meters
        rt: Curvature radius at start point in meters. If rt is negative, the beam will pass through the focus,
            and if it is positive, the beam will purely diverge. The focus is located at lambda_ray =-rt
        lambda_ray: length along the ray in meters
        freq: wave frequency in Hz (not rad/s)

    Returns:
        the value of the beam width w at a given length along the ray, calculated based on the input parameters of
        width and curvature radius at the start point, the length along the ray, and the frequency of the wave.

    Note:
        calculates beam width for given w,Rcur and length along ray (lambda_ray)

        - wt, rt width and curvature radius at start point in m
        - rt < 0 : beam will pass focus, >0 : purely diverging
        - the focus is at lambda_ray = -rt
        - lambda_ray length along ray in m
        - freq: wave frequency im Hz (not rad/s)
    """
    c = np.double(2.998e8)  # speed of light in vacuum in m/s
    # assume vacuum conditionas at edge of plasma
    sr = np.pi * wt**2 / (c / freq)
    w = wt * np.sqrt((1.0 + lambda_ray / rt) ** 2 + (lambda_ray / sr) ** 2)
    return w


# TODO rename variable and refactor code in smaller reusable methods remove unused code
def ell_on_wall(xpout, w1, w2, gamma, e_k, wall2d):
    """
    This function calculates the center and generating vectors of an ellipse on a 2D polygon given
    certain input parameters.

    Args:
        xpout: an array of data type xp_dt, as defined in the routine line_polygon_intersection
        w1: width of the beam at cross section
        w2: The width of the beam at the cross section.
        gamma: rotation of the ellipse
        e_k: unit vector direction of ray
        wall2d: R,z values of a polygon representing a wall in 2D space

    Returns:
        four arrays: g1l, g2l, rl, and sl.

    Note:
        calculates ellipses on wall segment
        input
        - xpout   array of data type xp_dt  (as defined in routine line_polygon_intersection)
        - w1,w2   widths of beam at cross section (calculated with calcw)
        - gamma   rotation of the ellipse
        - e_k     unit vector direction of ray
        - wall2d  R,z values of Polygone  output
        - rl      center of the Ellipse (R*Phi [m], l(ength along polygone) [m]
        - g1l,g2l generating vectors of the ellips (not orthogonal)
        - Ellipse rl + g1l*cos(t) + g2l*sin(t)
        - xpout,w1,w2,gamma are assumed to have the same shape
        - e_k has the same shape but is a 3d vector
        - rl,g1l,g2l same shape, 2d vectors

    .. todo:need to refactor code, renaming and documentation
    """

    # First we collapse to 1-D vectors
    xp_shape = xpout.shape
    xpout = np.reshape(xpout, (-1))
    w1 = np.reshape(w1, (-1))
    w2 = np.reshape(w2, (-1))
    gamma = np.reshape(gamma, (-1))
    e_k = np.reshape(e_k, (-1, 3))
    # next we need to summ the lengths of the wall segments
    lwall = np.zeros((len(wall2d)), dtype=np.double)
    for i in range(len(wall2d)):
        if i == 0:
            lwall[i] = 0.0
        else:
            lwall[i] = lwall[i - 1] + np.sqrt(
                (wall2d[i, 0] - wall2d[i - 1, 0]) ** 2 + (wall2d[i, 1] - wall2d[i - 1, 1]) ** 2
            )

    rl = np.zeros((len(e_k), 2), dtype=np.double)
    sl = np.zeros((len(e_k)), dtype=np.double)
    g1l = np.zeros((len(e_k), 2), dtype=np.double)
    g2l = np.zeros((len(e_k), 2), dtype=np.double)
    eh = np.zeros((3), dtype=np.double)
    for i in range(e_k.shape[0]):
        # we find the horizontal and vertical axis perp tp e_k
        if np.abs(e_k[i, 2]) > 0.999999:
            # horizontal axis not well defined if e_k || [0,0,1]
            # use toroidal axis instead
            eh[0] = 1.0
            eh[1] = xpout["r_cyl"][i, 1] + np.pi / 2.0
            eh[2] = 0.0
            eh = cyl2xyz(eh)
        else:
            eh = np.cross(np.array([0.0, 0.0, 1.0], dtype=np.double), e_k[i, :])
        # normalize eh
        eh = eh / np.sqrt(np.sum(eh**2))
        ev = np.cross(e_k[i, :], eh)
        ev = ev / np.sqrt(np.sum(ev**2))
        #        print(eh,ev,e_k[i,:])
        # parallel projection of elipsis on wall segment with surface normal n_c
        peh = eh - np.dot(eh, xpout["n_c"][i, :]) / xpout["k_dot_n"][i] * e_k[i, :]
        pev = ev - np.dot(ev, xpout["n_c"][i, :]) / xpout["k_dot_n"][i] * e_k[i, :]
        # g1, g2 define ellipsis on local tangent plane to segment
        g1 = w1[i] * (np.cos(gamma[i]) * peh + np.sin(gamma[i]) * pev)
        g2 = w2[i] * (-np.sin(gamma[i]) * peh + np.cos(gamma[i]) * pev)
        # begin test purposes only, tests ok
        #        print('test g1,g2')
        #        tg2t=2.*np.dot(g1,g2)/(np.sum(g1**2)-np.sum(g2**2))
        # print(xpout[i]['icorner'],np.dot(ga,gb),np.sum(ga**2),np.sum(gb**2),(np.sum(ga**2)-np.sum(gb**2)))
        # print(i,tg2t)
        #        t1=0.5*np.arctan(tg2t,dtype=np.double)
        #        t2=t1+np.pi/2.
        # print(i,t1,t2)
        #        a1=g1* np.cos(t1)+ g2* np.sin(t1)
        #        a2=g1* np.cos(t2)+ g2* np.sin(t2)
        #        sa1=np.sqrt(np.sum(a1**2))
        #        sa2=np.sqrt(np.sum(a2**2))
        #        print(i,w1[i],w2[i],sa1,sa2,sa1*sa2*xpout['k_dot_n'][i],w1[i]*w2[i])
        #        print(np.dot(xpout['n_c'][i,:],peh),np.dot(xpout['n_c'][i,:],pev))
        # tests ok
        #        x-direction on tangential plane
        ephi = cyl2xyz(np.array([1.0, xpout["r_cyl"][i, 1] + np.pi / 2.0, 0.0], dtype=np.double))
        #        y-direction on tangential plane in direction of wall2d[i+1]-wall2d[i]
        if xpout["icorner"][i] < len(wall2d) - 1:
            el = wall2d[xpout["icorner"][i] + 1, :] - wall2d[xpout["icorner"][i], :]
        else:
            el = wall2d[0, :] - wall2d[xpout["icorner"][i], :]
        el = el / np.sqrt(np.sum(el**2))
        el3 = cyl2xyz(np.array([el[0], xpout["r_cyl"][i, 1], el[1]], dtype=np.double))
        g1l[i, 0] = np.dot(g1, ephi)
        g1l[i, 1] = np.dot(g1, el3)
        g2l[i, 0] = np.dot(g2, ephi)
        g2l[i, 1] = np.dot(g2, el3)
        # begin test purposes only, tests ok
        #        print('test g1l,g2l')
        #        tg2t=2.*np.dot(g1l[i],g2l[i])/(np.sum(g1l[i]**2)-np.sum(g2l[i]**2))
        # print(xpout[i]['icorner'],np.dot(ga,gb),np.sum(ga**2),np.sum(gb**2),(np.sum(ga**2)-np.sum(gb**2)))
        # print(i,tg2t)
        #        t1=0.5*np.arctan(tg2t,dtype=np.double)
        #        t2=t1+np.pi/2.
        # print(i,t1,t2)
        #        a1=g1l[i]* np.cos(t1)+ g2l[i]* np.sin(t1)
        #        a2=g1l[i]* np.cos(t2)+ g2l[i]* np.sin(t2)
        #        sa1=np.sqrt(np.sum(a1**2))
        #        sa2=np.sqrt(np.sum(a2**2))
        #        print(i,w1[i],w2[i],sa1,sa2,sa1*sa2*xpout['k_dot_n'][i],w1[i]*w2[i])
        #        print(np.dot(xpout['n_c'][i,:],peh),np.dot(xpout['n_c'][i,:],pev))
        # tests ok
        # now rl: first determine sector
        sl[i] = xpout["r_cyl"][i, 1] // (np.pi / 9.0)
        # dPhi with respect to midlle of sector
        d_phi = xpout["r_cyl"][i, 1] - (sl[i] + 0.5) * (np.pi / 9.0)
        # x - length scale relative to middle of sector
        rl[i, 0] = d_phi * xpout["r_cyl"][i, 0]
        # y-length: length along polygone
        rl[i, 1] = lwall[xpout["icorner"][i]] + xpout["lambda_pol"][i]
    # Reshape input and output vectors to initial shape
    xpout = np.reshape(xpout, xp_shape)
    w1 = np.reshape(w1, xp_shape)
    w2 = np.reshape(w2, xp_shape)
    gamma = np.reshape(gamma, xp_shape)
    sl = np.reshape(sl, xp_shape)
    e_k = np.reshape(e_k, xp_shape + tuple([3]))
    rl = np.reshape(rl, xp_shape + tuple([2]))
    g1l = np.reshape(g1l, xp_shape + tuple([2]))
    g2l = np.reshape(g2l, xp_shape + tuple([2]))
    return g1l, g2l, rl, sl


# ============================================================================
# Coil Conductor Outline Functions
# ============================================================================


def get_conductor_outline(conductor, skip=1):
    """
    Extract inner and outer contour coordinates for coil conductor cross-sections.

    This function computes the inner and outer boundary coordinates of a coil
    conductor by analyzing the cross-section geometry and applying the maximum
    normal offset from the conductor centerline using a three-point algorithm
    that uses middle points from three consecutive points.

    This function works with conductors from IDS that use the coil_conductor
    structure reference (e.g., tf, coils_non_axisymmetric).

    Parameters
    ----------
    conductor : object
        A conductor object containing elements and cross_section data from the
        IMAS coil data structure (structure reference: coil_conductor).
    skip : int, optional
        Sampling rate for points. If skip=1 (default), use all points.
        If skip=10, use every 10th point for faster computation.
        Useful for visualization when high precision is not required.

    Returns
    -------
    dict
        A dictionary with the following structure::

            {
                'inner': {'r': list, 'z': list},
                'outer': {'r': list, 'z': list}
            }

        where:

        - 'inner' contains the inner boundary coordinates (R, Z)
        - 'outer' contains the outer boundary coordinates (R, Z)

    Notes
    -----
    - Only processes elements with type 1 (line segment)
    - Only handles cross-sections with geometry_type == 1 (polygon outline)
    - Selects middle points of non-collinear triplets
    - Uses the maximum normal coordinate to determine conductor thickness
    - Returns empty lists if no valid cross-section data is found
    - Higher skip values reduce computation time but lower outline resolution
    """
    elements = conductor.elements
    cross_section = conductor.cross_section

    # Initialize return dictionary
    outline_dict = {"inner": {"r": [], "z": []}, "outer": {"r": [], "z": []}}

    # Calculate coil center coordinates
    x_center = np.average(elements.start_points.r)
    y_center = np.average(elements.start_points.z)

    return _get_conductor_outline_three_point(elements, cross_section, x_center, y_center, outline_dict, skip)


def _conductor_tn_to_xy(t, n, x_start, y_start, x_end, y_end, x_center, y_center):
    """
    Convert local (T, N) coordinates to Cartesian (x, y) for a general
    planar coil segment.

    The local frame is defined as:
      - T : unit tangent vector from (x_start, y_start) to (x_end, y_end)
      - N : unit normal vector, perpendicular to T, chosen so that it points
            more towards the coil center (x_center, y_center).

    That is, among the two possible normals ±N, we pick the one whose
    dot product with the vector from the reference point to the center is
    non-negative.

    Parameters
    ----------
    t, n : float or ndarray
        Local coordinates along T (tangent) and N (normal).
    x_start, y_start : float or ndarray
        Cartesian coordinates of the start point of the coil segment.
    x_end, y_end : float or ndarray
        Cartesian coordinates of the end point of the coil segment.
    x_center, y_center : float or ndarray
        Cartesian coordinates of (an approximate) coil center used to
        resolve the sign ambiguity of N.

    Returns
    -------
    x, y : float or ndarray
        Cartesian coordinates corresponding to the given (t, n) in the
        local (T, N) frame at the start point.

    Notes
    -----
    - T is always tangent to the segment from start to end.
    - N is perpendicular to T and chosen to point towards the center.
    - All inputs are converted to NumPy arrays and broadcast according
      to NumPy's broadcasting rules.
    - If the start and end points coincide, a ValueError is raised.
    - The local frame origin is at the start point.
    """

    # Convert to arrays for broadcasting
    t = np.asarray(t)
    n = np.asarray(n)
    x_start = np.asarray(x_start)
    y_start = np.asarray(y_start)
    x_end = np.asarray(x_end)
    y_end = np.asarray(y_end)
    x_center = np.asarray(x_center)
    y_center = np.asarray(y_center)

    # Determine reference point (always use start point)
    x_ref = x_start
    y_ref = y_start

    # Tangent direction T: from start to end
    dx = x_end - x_start
    dy = y_end - y_start
    seg_len = np.hypot(dx, dy)

    if np.any(seg_len == 0.0):
        raise ValueError("Start and end points coincide; tangent undefined.")

    Tx = dx / seg_len
    Ty = dy / seg_len

    # Two candidate normals, perpendicular to T
    # N1: rotate T by +90 degrees (CCW)
    Nx1 = -Ty
    Ny1 = Tx
    # N2 = -N1 would be the opposite side

    # Vector from reference point to center
    cx = x_center - x_ref
    cy = y_center - y_ref

    # Decide which normal points more towards the center
    # If dot((cx, cy), N1) >= 0, use N1; otherwise use -N1
    dot1 = cx * Nx1 + cy * Ny1
    use_N1 = dot1 >= 0

    Nx = np.where(use_N1, Nx1, -Nx1)
    Ny = np.where(use_N1, Ny1, -Ny1)

    # Map local (t, n) -> global (x, y) from reference point
    x = x_ref + t * Tx + n * Nx
    y = y_ref + t * Ty + n * Ny

    return x, y


def _conductor_tn_to_xy_three_points(x1, y1, x2, y2, x3, y3, n, x_center, y_center):
    """
    Convert local (T, N) coordinates to Cartesian (x, y) for a coil segment
    defined by three points, where T is computed from 1st and 3rd points
    and the reference position is the 2nd (middle) point.

    Parameters
    ----------
    x1, y1 : float or ndarray
        Cartesian coordinates of the first point.
    x2, y2 : float or ndarray
        Cartesian coordinates of the second point (reference/middle point).
    x3, y3 : float or ndarray
        Cartesian coordinates of the third point.
    n : float or ndarray
        Normal coordinate (distance from centerline).
    x_center, y_center : float or ndarray
        Cartesian coordinates of (an approximate) coil center used to
        resolve the sign ambiguity of N.

    Returns
    -------
    x_offset, y_offset : float or ndarray
        Cartesian coordinates corresponding to the given normal offset
        from the middle point (x2, y2).

    Notes
    -----
    - T is computed as unit vector from point 1 to point 3
    - N is perpendicular to T and chosen to point towards the center
    - Reference point for coordinate transformation is the middle point
    - If points 1 and 3 coincide, a ValueError is raised
    """
    # Convert to arrays for broadcasting
    x1 = np.asarray(x1)
    y1 = np.asarray(y1)
    x2 = np.asarray(x2)
    y2 = np.asarray(y2)
    x3 = np.asarray(x3)
    y3 = np.asarray(y3)
    n = np.asarray(n)
    x_center = np.asarray(x_center)
    y_center = np.asarray(y_center)

    # Tangent direction T: from point 1 to point 3
    dx = x3 - x1
    dy = y3 - y1
    seg_len = np.hypot(dx, dy)

    if np.any(seg_len == 0.0):
        raise ValueError("Points 1 and 3 coincide; tangent is undefined.")

    Tx = dx / seg_len
    Ty = dy / seg_len

    # Two candidate normals, perpendicular to T
    # N1: rotate T by +90 degrees (CCW)
    Nx1 = -Ty
    Ny1 = Tx

    # Vector from middle point (x2, y2) to center
    cx = x_center - x2
    cy = y_center - y2

    # Decide which normal points more towards the center
    # If dot((cx, cy), N1) >= 0, use N1; otherwise use -N1
    dot1 = cx * Nx1 + cy * Ny1
    use_N1 = dot1 >= 0

    Nx = np.where(use_N1, Nx1, -Nx1)
    Ny = np.where(use_N1, Ny1, -Ny1)

    # Map normal offset from middle point (x2, y2)
    x_offset = x2 + n * Nx
    y_offset = y2 + n * Ny

    return x_offset, y_offset


def _are_points_collinear(x1, y1, x2, y2, x3, y3, tolerance=1e-9):
    """
    Check if three points are collinear (lie on the same line).

    Uses the cross product method: if the cross product of vectors
    (P2-P1) and (P3-P1) is close to zero, the points are collinear.

    Parameters
    ----------
    x1, y1 : float
        Coordinates of the first point.
    x2, y2 : float
        Coordinates of the second point.
    x3, y3 : float
        Coordinates of the third point.
    tolerance : float, optional
        Tolerance for considering points as collinear. Default is 1e-9.

    Returns
    -------
    bool
        True if the three points are collinear within the given tolerance,
        False otherwise.

    Notes
    -----
    - Uses cross product magnitude compared to tolerance
    - Accounts for the scale of the coordinates by normalizing
    """
    # Vectors from point 1 to points 2 and 3
    dx1 = x2 - x1
    dy1 = y2 - y1
    dx2 = x3 - x1
    dy2 = y3 - y1

    # Cross product magnitude
    cross_product = abs(dx1 * dy2 - dy1 * dx2)

    # Scale tolerance by the magnitude of the vectors
    scale = max(abs(dx1), abs(dy1), abs(dx2), abs(dy2), 1.0)

    return cross_product < tolerance * scale


def _get_conductor_outline_three_point(elements, cross_section, x_center, y_center, outline_dict, skip=1):
    """
    Three-point algorithm for conductor outline extraction.
    Selects middle points from non-collinear triplets.

    Parameters
    ----------
    skip : int, optional
        Sampling rate for points. If skip=1, use all points.
        If skip=10, use every 10th point.
    """
    # Collect all valid centerline points first
    centerline_points = []
    valid_cross_sections = []

    for ielement in range(len(elements.types)):
        # Skip points based on sampling rate
        if ielement % skip != 0:
            continue

        if elements.types[ielement] == 1:  # line segment
            if len(cross_section) == 1:
                cs_index = 0
            elif len(cross_section) > 1:
                cs_index = ielement
            else:
                continue

            cs = cross_section[cs_index]
            centerline_points.append((elements.start_points.r[ielement], elements.start_points.z[ielement]))
            valid_cross_sections.append(cs)

    if len(centerline_points) < 3:
        return outline_dict

    # Get thickness information from first cross-section
    cs = valid_cross_sections[0]
    if cs.geometry_type.index == 1:  # polygon outline
        n_inner = np.max(cs.outline.normal)
        n_outer = np.min(cs.outline.normal)
    else:
        n_inner = abs(cs.width / 2.0)
        n_outer = -n_inner

    inner_r_points = []
    inner_z_points = []
    outer_r_points = []
    outer_z_points = []

    # Process triplets of consecutive points (wraparound for closed loop)
    # Phase 1: Process all collinear triplets first
    processed_points = set()  # Track which points have been processed

    for i in range(len(centerline_points)):
        # Handle wraparound indices for closed loop geometry
        prev_idx = (i - 1) % len(centerline_points)
        curr_idx = i
        next_idx = (i + 1) % len(centerline_points)

        x1, y1 = centerline_points[prev_idx]  # previous point
        x2, y2 = centerline_points[curr_idx]  # current point (middle)
        x3, y3 = centerline_points[next_idx]  # next point

        # Check if points are collinear
        if _are_points_collinear(x1, y1, x2, y2, x3, y3, tolerance=1e-6):
            # Points are collinear, add inner/outer points for all three
            # For collinear points, use tangent direction from first to third

            # Add points for first point (x1, y1)
            xi1, yi1 = _conductor_tn_to_xy(0.0, n_inner, x1, y1, x3, y3, x_center, y_center)
            xo1, yo1 = _conductor_tn_to_xy(0.0, n_outer, x1, y1, x3, y3, x_center, y_center)
            inner_r_points.append(xi1)
            inner_z_points.append(yi1)
            outer_r_points.append(xo1)
            outer_z_points.append(yo1)

            # Add points for middle point (x2, y2)
            xi2, yi2 = _conductor_tn_to_xy(0.0, n_inner, x2, y2, x3, y3, x_center, y_center)
            xo2, yo2 = _conductor_tn_to_xy(0.0, n_outer, x2, y2, x3, y3, x_center, y_center)
            inner_r_points.append(xi2)
            inner_z_points.append(yi2)
            outer_r_points.append(xo2)
            outer_z_points.append(yo2)

            # Add points for third point (x3, y3)
            xi3, yi3 = _conductor_tn_to_xy(0.0, n_inner, x3, y3, x1, y1, x_center, y_center)
            xo3, yo3 = _conductor_tn_to_xy(0.0, n_outer, x3, y3, x1, y1, x_center, y_center)
            inner_r_points.append(xi3)
            inner_z_points.append(yi3)
            outer_r_points.append(xo3)
            outer_z_points.append(yo3)

            # Mark all three points as processed
            processed_points.add(prev_idx)
            processed_points.add(curr_idx)
            processed_points.add(next_idx)

    # Phase 2: Process non-collinear triplets, skip already processed points
    for i in range(len(centerline_points)):
        # Skip if current point was already processed in Phase 1
        if i in processed_points:
            continue

        # Handle wraparound indices for closed loop geometry
        prev_idx = (i - 1) % len(centerline_points)
        curr_idx = i
        next_idx = (i + 1) % len(centerline_points)

        x1, y1 = centerline_points[prev_idx]  # previous point
        x2, y2 = centerline_points[curr_idx]  # current point (middle)
        x3, y3 = centerline_points[next_idx]  # next point

        # Check if points are collinear (should be false since processed)
        if not _are_points_collinear(x1, y1, x2, y2, x3, y3, tolerance=1e-6):
            # Points are not collinear, use three-point algorithm
            xi, yi = _conductor_tn_to_xy_three_points(x1, y1, x2, y2, x3, y3, n_inner, x_center, y_center)
            xo, yo = _conductor_tn_to_xy_three_points(x1, y1, x2, y2, x3, y3, n_outer, x_center, y_center)

            inner_r_points.append(xi)
            inner_z_points.append(yi)
            outer_r_points.append(xo)
            outer_z_points.append(yo)

    # Sort and remove duplicates for inner and outer contours
    inner_r_sorted, inner_z_sorted = _sort_and_deduplicate_contour(inner_r_points, inner_z_points)
    outer_r_sorted, outer_z_sorted = _sort_and_deduplicate_contour(outer_r_points, outer_z_points)

    # Store the results
    outline_dict["inner"]["r"] = inner_r_sorted
    outline_dict["inner"]["z"] = inner_z_sorted
    outline_dict["outer"]["r"] = outer_r_sorted
    outline_dict["outer"]["z"] = outer_z_sorted

    return outline_dict


def _sort_and_deduplicate_contour(r_points, z_points, tolerance=1e-9):
    """
    Sort contour points in counter-clockwise order and remove duplicates.

    This function takes a list of R, Z coordinates, removes duplicate points
    within tolerance, and sorts the remaining points in counter-clockwise
    order around their centroid.

    Parameters
    ----------
    r_points : list or ndarray
        R-coordinates of the contour points.
    z_points : list or ndarray
        Z-coordinates of the contour points.
    tolerance : float, optional
        Distance tolerance for considering points as duplicates.
        Default is 1e-9.

    Returns
    -------
    r_sorted : list
        R-coordinates sorted in counter-clockwise order with duplicates
        removed.
    z_sorted : list
        Z-coordinates sorted in counter-clockwise order with duplicates
        removed.

    Notes
    -----
    - Uses centroid as reference point for angular sorting
    - Counter-clockwise ordering is based on angle from centroid
    - Duplicate points within tolerance are removed (keeps first occurrence)
    - Returns empty lists if no valid points remain after processing
    """
    if len(r_points) == 0:
        return [], []

    # Convert to numpy arrays
    r_points = np.array(r_points)
    z_points = np.array(z_points)

    # Remove duplicates within tolerance
    unique_r = []
    unique_z = []

    for i, (r, z) in enumerate(zip(r_points, z_points)):
        # Check if this point is too close to any existing unique point
        is_duplicate = False
        for ur, uz in zip(unique_r, unique_z):
            distance = np.sqrt((r - ur) ** 2 + (z - uz) ** 2)
            if distance < tolerance:
                is_duplicate = True
                break

        # Only add the point if it's not a duplicate
        if not is_duplicate:
            unique_r.append(r)
            unique_z.append(z)

    if len(unique_r) == 0:
        return [], []

    # Calculate centroid
    centroid_r = np.mean(unique_r)
    centroid_z = np.mean(unique_z)

    # Calculate angles from centroid to each point
    angles = []
    for r, z in zip(unique_r, unique_z):
        angle = np.arctan2(z - centroid_z, r - centroid_r)
        angles.append(angle)

    # Sort points by angle (counter-clockwise order)
    sorted_indices = np.argsort(angles)

    r_sorted = [unique_r[i] for i in sorted_indices]
    z_sorted = [unique_z[i] for i in sorted_indices]

    return r_sorted, z_sorted
