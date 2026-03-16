"""
This module

"""

import difflib
import inspect
import logging
import re
import sys
import time
import types
from typing import Union

import numpy as np
import pandas as pd
import rich
import scipy

try:
    import imaspy as imas
except ImportError:
    import imas
from packaging import version
from rich.table import Table
from rich.text import Text

logger = logging.getLogger("module")
ARRAY_EQUAL_KWARGS = "equal_nan=True" if version.parse(np.__version__) > version.parse("1.19") else ""


def parse_uri(uri: str):
    result = {}
    splitted_ids_info = uri.split("#")

    uri_part = splitted_ids_info[0]
    ids_name = ""
    ids_path = None
    occurrence = None
    if len(splitted_ids_info) == 2:
        ids_fragment = splitted_ids_info[1]
        splitted_ids_fragment = ids_fragment.split("/", 1)
        if ":" in splitted_ids_fragment[0]:
            splitted_ids_fragment = ids_fragment.split(":", 1)
            ids_name = splitted_ids_fragment[0]
            if len(splitted_ids_fragment) == 2:
                ids_path_fragment = splitted_ids_fragment[1]
                splitted_ids_path_fragment = ids_path_fragment.split("/", 1)
                occurrence = int(splitted_ids_path_fragment[0])
                if len(splitted_ids_path_fragment) == 2:
                    ids_path = splitted_ids_path_fragment[1]
        else:
            ids_name = splitted_ids_fragment[0]
            if len(splitted_ids_fragment) == 2:
                ids_path = splitted_ids_fragment[1]
    result["uri_part"] = uri_part
    result["occurrence"] = occurrence
    result["ids_name"] = ids_name
    result["ids_path"] = ids_path
    return result


def parse_slice_from_string(input_string):
    match = re.search(r"[\[\(]([-\d]*):([-\d]*):?([-\d]*)[\]\)]", input_string)

    start = end = step = None
    if match:
        start_str, end_str, step_str = match.groups()

        start = int(start_str) if start_str else None
        end = int(end_str) if end_str else None
        step = int(step_str) if step_str else None

    return slice(start, end, step)


def get_length_of_partial_field(ids, ids_path):
    partial_field = ids_path
    match = re.match(r"^(.*)\[t\]\.(.*)", ids_path)
    if match:
        partial_field = match.group(1)
    try:
        _inner_data = eval("ids." + partial_field)
        coordinate_partial = None
        coordinate_unit = ""
        if isinstance(_inner_data, imas.ids_primitive.IDSPrimitive) or isinstance(
            _inner_data, imas.ids_struct_array.IDSStructArray
        ):
            coordinate_partial = _inner_data.coordinates[0]
            if isinstance(coordinate_partial, imas.ids_primitive.IDSPrimitive):
                coordinate_unit = coordinate_partial.metadata.units
        return coordinate_partial, coordinate_unit
    except Exception as e:
        logger.error(
            f"{partial_field} path/value does not exist, hint: please check "
            f"length of an array, detailed error : {e}"
        )
        return None


def partial_get(ids, ids_path, custom_coordinate=None):
    slice_object = parse_slice_from_string(ids_path)
    ids_path_for_eval = re.sub(r"[\[\(][^()\[\]]*:[^()\[\]]*[\]\)]", "(t)", ids_path)
    ids_path_for_eval = ids_path_for_eval.replace("(", "[").replace(")", "]").replace("/", ".")
    coordinate_partial, coordinate_unit = get_length_of_partial_field(ids, ids_path_for_eval)
    data = np.array([]).reshape(
        0,
    )
    array_data = []
    start = slice_object.start if slice_object.start is not None else 0
    stop = slice_object.stop if slice_object.stop is not None else len(coordinate_partial)
    step = slice_object.step if slice_object.step is not None else 1
    data_flag = True
    data_unit = ""
    coordinate = coordinate_partial

    for t in range(start, stop, step):
        try:
            _inner_data = eval("ids." + ids_path_for_eval)
            if data_flag:
                data_flag = False
                if isinstance(_inner_data, imas.ids_primitive.IDSPrimitive):
                    data_unit = _inner_data.metadata.units
                    if custom_coordinate and custom_coordinate.sdigit():
                        _coordinate = _inner_data.coordinates[custom_coordinate]
                        if isinstance(_coordinate, imas.ids_primitive.IDSPrimitive):
                            if _coordinate.has_value is True:
                                coordinate = _coordinate
                    elif custom_coordinate and isinstance(custom_coordinate, str):
                        _coordinate = eval("ids." + custom_coordinate)
                        if isinstance(_coordinate, imas.ids_primitive.IDSPrimitive):
                            if _coordinate.has_value is True:
                                coordinate = _coordinate
                    else:
                        for _coordinate in _inner_data.coordinates:
                            if isinstance(_coordinate, imas.ids_primitive.IDSPrimitive):
                                if _coordinate.has_value is True:
                                    coordinate_unit = _coordinate.metadata.units
                                    coordinate = _coordinate
                                    break
                                else:
                                    continue
                            else:
                                coordinate = _coordinate
                                coordinate_unit = "Indices"
        except Exception as e:
            logger.error(
                f"{ids_path} path/value does not exist, hint: please check length of arrays, detailed error : {e}"
            )
            return data, coordinate, data_unit, coordinate_unit
        if isinstance(_inner_data, (imas.ids_structure.IDSStructure, imas.ids_struct_array.IDSStructArray)):
            array_data.append(_inner_data)
        elif isinstance(_inner_data, imas.ids_primitive.IDSString0D):
            array_data.append(_inner_data.value)
        else:
            if len(_inner_data.shape) == 0:
                data = np.append(data, _inner_data)
            elif len(_inner_data.shape) == 1:
                if data.size == 0:
                    data = _inner_data
                else:
                    data = np.vstack((data, _inner_data))
    if len(array_data) == 0:
        data = np.array(data)
    else:
        data = np.array(array_data)
    # if len(data) != len(coordinate):
    #     coordinate=None
    return data, coordinate, data_unit, coordinate_unit


def is_ids_field(idstype: type) -> bool:
    """
    This function checks if a given type is a possible field of an IDS.

    Args:
        idstype (type): The type of an attribute from an IDS or a substructure of an IDS.

    Returns:
        The function isIdsField returns a boolean value indicating whether the passed type is a possible
        field of an IDS or not.
    """
    return (
        idstype != types.MethodType
        and idstype != types.FunctionType
        and "Logger" not in str(idstype)
        and "HLIUtils" not in str(idstype)
    )


def get_ids_attributes(idsobj: object) -> list:
    """
    This function returns a list of attribute names for a given IDS object.

    Args:
        idsobj (object): The IDS or substructure object for which the function will return a list of attribute names.

    Returns:
        The function `get_ids_attributes` returns a list of attribute names for the given IDS object which are not
        private and are ids fields.
    """
    if "imas" in str(type(idsobj)):
        return [a[0] for a in inspect.getmembers(idsobj) if not a[0].startswith("_") and is_ids_field(type(a[1]))]
    else:
        return []


def get_ids_size(db_entry_object, ids_names=None, dd_update=False, ignore_empty=False) -> dict:
    """
    The function `get_ids_size` retrieves the size of IDS objects from a database entry and returns a dictionary
    containing the size in bytes and the time taken to read each object.

    Args:
        db_entry_object: The `db_entry_object` parameter is used to access the data in the IMAS database.
        ids_names: idsNames is a list of IDS names. If it is not provided, it defaults to None.

    Returns:
        a dictionary containing information about the size and time taken to read IDS objects from a database
        entry. The dictionary has the following structure:
    """

    if ids_names is None:
        factory = imas.ids_factory.IDSFactory()
        ids_names = factory.ids_names()
    ids_size_dict = {}
    for ids_name in ids_names:
        occurrence_list = db_entry_object.list_all_occurrences(ids_name)
        if len(occurrence_list) == 0:
            continue
        occurrences_count = max(occurrence_list)

        for o in range(occurrences_count + 1):
            try:
                if dd_update:
                    ids_object = imas.convert_ids(
                        db_entry_object.get(ids_name, occurrence=o, autoconvert=False), db_entry_object.factory.version
                    )
                else:
                    ids_object = db_entry_object.get(ids_name, occurrence=o, autoconvert=False)

                homogeneous_time = ids_object.ids_properties.homogeneous_time
                if homogeneous_time >= 0:
                    field = f"{ids_name}/{o}"
                    ids_size_dict[field] = {}
                    start_time = time.time()
                    ids_size_dict[field]["bytes"] = get_object_size(ids_object, ignore_empty)
                    ids_size_dict[field]["time"] = time.time() - start_time
                    print(
                        "Reading %0.3f MB of data for %s took %0.3f seconds"
                        % (
                            ids_size_dict[field]["bytes"] / 1024**2,
                            field,
                            ids_size_dict[field]["time"],
                        )
                    )
                    del ids_object
            except Exception as e:
                logger.warning(f"Failed to retrieve IDS '{ids_name}' with occurrence {o}: {str(e)}. Skipping this IDS.")
    return ids_size_dict


def get_all_ids_size(db_entry_object):
    """
    The function `get_all_ids_size` calculates the total size in bytes of all IDS in a given `db_entry_object`.

    Args:
        db_entry_object : The parameter `db_entry_object` is of type .

    Returns:
        the total size in bytes of all the IDS in the given `db_entry_object`.
    """
    ids_size_dict = get_ids_size(db_entry_object)
    total_bytes = np.array([ids["bytes"] for ids in ids_size_dict.values()]).sum()
    return total_bytes


def get_all_ids_get_time(db_entry_object):
    """
    The function `get_all_ids_get_time` calculates the total time for all IDS in a given `db_entry_object`.

    Args:
        db_entry_object : The parameter `db_entry_object` is of type .

    Returns:
        the total time to get all the IDSes in the given `db_entry_object`.
    """
    ids_size_dict = get_ids_size(db_entry_object)
    return np.array([ids["time"] for ids in ids_size_dict.values()]).sum()


def get_object_size(obj: object, ignore_empty=False) -> int:
    object_size = 0

    if (
        isinstance(obj, imas.ids_primitive.IDSInt0D)
        or isinstance(obj, imas.ids_primitive.IDSString0D)
        or isinstance(obj, imas.ids_primitive.IDSComplex0D)
        or isinstance(obj, imas.ids_primitive.IDSFloat0D)
        or isinstance(obj, imas.ids_primitive.IDSNumericArray)
        or isinstance(obj, imas.ids_primitive.IDSPrimitive)
        or isinstance(obj, imas.ids_primitive.IDSString1D)
    ):
        if ignore_empty and obj.has_value is False:
            return object_size
        elif isinstance(obj.value, str):
            object_size += len(obj.value.encode("utf-8"))
        elif isinstance(obj.value, np.ndarray):
            object_size += obj.value.nbytes
        elif isinstance(obj.value, int):
            object_size += 4
        elif isinstance(obj.value, float):
            object_size += 8
        elif isinstance(obj.value, complex):
            object_size += 16
        elif isinstance(obj.value, list):
            for obj_item in obj:
                object_size += get_object_size(obj_item, ignore_empty)
        else:
            object_size += sys.getsizeof(obj)
            print(f"Unkonwn {type(obj.value)}  getting size with getsizeof  ->  {obj}")
    elif isinstance(obj, imas.ids_struct_array.IDSStructArray):
        for obj_item in obj:
            object_size += get_object_size(obj_item, ignore_empty)
    elif isinstance(obj, imas.ids_structure.IDSStructure):
        for obj_value in obj:
            object_size += get_object_size(obj_value, ignore_empty)
    else:
        object_size += sys.getsizeof(obj)
        print(f"Unkonwn  {type(obj)}  getting size with getsizeof ->  {obj}")
    return object_size


def get_ids_types():
    """
    This function returns list of strings corresponding to all ids types for each IDSName object in the imas module.

    Returns:
        The function `get_ids_types()` is returning a list of values of all the `value` attributes of the `IDSName`
        objects in the `imas` module.
    """
    factory = imas.ids_factory.IDSFactory()
    return factory.ids_names()


def get_available_ids_and_occurrences(
    db_entry_object,
    time_mode=None,
    get_comment=False,
    get_version=False,
):
    """
    This function returns a list of pairs of available IDS types and their occurrences in a given DBEntry object.

    Args:
        db_entry_object: An object of the class DBEntry, which represents an open DBEntry in
            which available IDSs will be looked for.
        time_mode: The time mode of interest for the IDSs in the given DBEntry.
        get_comment: Output ids_properties.comment field for each found occurrence
        get_version: Whether to return version information

    Returns:
        a list of pairs (idstype:str,occurrence:int) with data in the given DBEntry.
    """
    occ_type_dict = {
        1: "reconstruction",
        2: "prediction_fixed",
        3: "prediction_free",
        4: "mapping",
    }
    availableidslist = []
    for idstype in get_ids_types():
        occurrence_list = db_entry_object.list_all_occurrences(idstype)
        for occ in occurrence_list:
            homogeneous_time = ""
            comment = ""
            occ_type = ""

            try:
                ids_object = db_entry_object.get(
                    idstype, occurrence=occ, lazy=True, autoconvert=False, ignore_unknown_dd_version=True
                )

                dd_version = ids_object.ids_properties.version_put.data_dictionary.value
                homogeneous_time = ids_object.ids_properties.homogeneous_time
                comment = ids_object.ids_properties.comment

                occ_type_text = ""
                if hasattr(ids_object.ids_properties, "occurrence_type"):
                    occ_type = ids_object.ids_properties.occurrence_type
                    if occ_type.index != imas.ids_defs.EMPTY_INT:
                        if occ_type.index.value in occ_type_dict.keys():
                            occ_type_text = occ_type_dict[occ_type.index.value]
                            comment += f" [occurrence type = {occ_type_text}]"
                if homogeneous_time != imas.ids_defs.EMPTY_INT and (time_mode is None or time_mode == homogeneous_time):
                    if get_comment is True:
                        availableidslist.append((idstype, occ, comment))
                    elif get_version is True:
                        availableidslist.append((idstype, occ, dd_version))
                    elif get_comment is True and get_version is True:
                        availableidslist.append(idstype, occ, comment, dd_version)
                    else:
                        availableidslist.append((idstype, occ))
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve IDS '{idstype}' with occurrence {occ}: {str(e)}. Skipping this IDS."
                )
    return availableidslist


def get_available_ids_and_times(db_entry_object) -> list:
    """
    The function `get_available_ids_and_times` retrieves available IDS names and corresponding time
    arrays from a given `db_entry_object`.

    Args:
        db_entry_object: The `db_entry_object` parameter.

    Returns:
        a list of tuples. Each tuple contains an IDS name and a corresponding time array.
    """

    result = []

    for _ids_name in get_ids_types():
        occurrence_list = db_entry_object.list_all_occurrences(_ids_name)

        if len(occurrence_list) == 0:
            continue

        for occurrence in occurrence_list:
            time_array = None
            try:

                ids_object = db_entry_object.get(
                    _ids_name, occurrence=occurrence, lazy=True, autoconvert=False, ignore_unknown_dd_version=True
                )

                homogeneous_time = ids_object.ids_properties.homogeneous_time
                if homogeneous_time == imas.ids_defs.IDS_TIME_MODE_UNKNOWN:
                    time_array = []
                if homogeneous_time == imas.ids_defs.IDS_TIME_MODE_HETEROGENEOUS:
                    time_array = [np.nan]
                if homogeneous_time == imas.ids_defs.IDS_TIME_MODE_HOMOGENEOUS:
                    if getattr(ids_object, "time", None):
                        time_array = ids_object.time.value
                if homogeneous_time == imas.ids_defs.IDS_TIME_MODE_INDEPENDENT:
                    time_array = [-np.inf]
            except Exception as e:
                logger.debug(f"{e}")
                time_array = []
                logger.info(f"ERROR! IDS {_ids_name} : Reading time array fails due to following problem : {e}")
            if occurrence != 0:
                result.append((f"{_ids_name}/{occurrence}", time_array))
            else:
                result.append((_ids_name, time_array))
    return result


def resample_indices(
    dbin: str,
    dbout: str,
    idsname: str,
    occurrence=0,
    start: int = 0,
    stop: int = None,
    step: int = 1,
    interpolation_method=imas.ids_defs.PREVIOUS_INTERP,
):
    """
    The function resample_indices takes in a database input, database output, and an idsname, and resamples the
    data based on the specified start, stop, and step values.

    Args:
        dbin (str): The parameter "dbin" is a string that represents the input database name. It is the
            database from which the data will be read.
        dbout (str): The parameter `dbout` is a string that represents the name of the output database.
            It is the database where the resampled data will be stored.
        idsname (str): The parameter "idsname" is a string that represents the ids that you want to resample.
        start (int): The start parameter is the index of the first time value to be resampled.
        stop (int): The `stop` parameter is used to specify the index at which the resampling should stop.
            If `stop` is not provided, the resampling will continue until the end of the `times` array.
        step (int): The `step` parameter determines the interval between the indices that are selected from
            the `times` array. For example, if `step` is set to 2, every second index will be selected. If `step`
            is set to 3, every third index will be selected, and so. Defaults to 1
    """
    idsobj = None
    try:
        idsobj = dbin.get(idsname, lazy=True, autoconvert=False)
        times = idsobj.time
    except Exception as e:  # noqa: F841
        logger.error(f"Error occurred while resampling data for {idsname} in the input database. {e}")
    if idsobj:
        if stop is not None and stop >= len(times):
            stop = len(times)
        if start is not None and start >= len(times):
            start = 0
        idsobj = dbin.get_sample(
            idsname,
            tmin=start,
            tmax=stop,
            dtime=times[start:stop:step],
            interpolation_method=interpolation_method,
            occurrence=occurrence,
            autoconvert=False,
        )
        dbout.put(idsobj, occurrence=occurrence)


def resample_times(
    dbin: object,
    dbout: object,
    idsname: str,
    occurrence=0,
    start: float = None,
    stop: float = None,
    step: float = None,
    interpolation_method=imas.ids_defs.PREVIOUS_INTERP,
):
    """
    Resamples time-dependent data from an input database and stores it in an output database.

    Parameters:
        dbin (object): The input database object from which data is retrieved.
        dbout (object): The output database object where resampled data is stored.
        idsname (str): The name of the IDS (Integrated Data Structure) to be resampled.
        occurrence (int, optional): The occurrence index of the IDS. Defaults to 0.
        start (float, optional): The start time for resampling. Defaults to None.
        stop (float, optional): The stop time for resampling. Defaults to None.
        step (float, optional): The time step for resampling. Defaults to None.
        interpolation_method (int, optional): The interpolation method to use for resampling.
            Defaults to `imas.ids_defs.PREVIOUS_INTERP`.

    Returns:
        None: The function does not return a value. The resampled data is stored in the output database.

    Raises:
        Exception: If an error occurs during data retrieval from the input database, it is caught and ignored.
    """
    idsobj = None
    idsobj = dbin.get_sample(
        idsname,
        tmin=start,
        tmax=stop,
        dtime=step,
        interpolation_method=interpolation_method,
        occurrence=occurrence,
        autoconvert=False,
    )
    dbout.put(idsobj, occurrence=occurrence)


def compare_ids(
    x,
    y,
    field=None,
    ignore_version=True,
    verb=True,
    name_x="first",
    name_y="second",
    output={},
):
    """
    The function compares two ids objects and returns whether they are identical or not, along with a
    dictionary of differences.

    Args:
        x: The first input ids object to compare.
        y: The second input ids object to compare.
        field: The name of the field being compared in the IDSes.
        ignore_version: A boolean parameter that determines whether to ignore the "version_put" attribute when
            comparing the two objects. If set to True, the function will ignore this attribute. Defaults to True
        verb: a boolean indicating whether to print log messages during the comparison process. Defaults to True
        output: A dictionary that stores the output of the function, which includes information about any differences
            found between the two input objects.

    Returns:
        tuple containing a boolean value indicating whether the two input objects are identical, and a dictionary
        containing information about any differences found during the comparison.
    """

    identical = True
    if hasattr(x, "__name__") and hasattr(y, "__name__"):
        if x.__name__ == y.__name__:
            if field is None:
                field = x.__name__
                logger.debug("Has __name__ in IDSes :" + x.__name__)
        else:
            if verb:
                logger.error(f"Different IDSs: {x.__name__} and {y.__name__}")
            return False
    elif hasattr(x, "_base_path") and hasattr(y, "_base_path"):
        if x._base_path == y._base_path:
            if field is None:
                field = x._base_path
                logger.debug("Has _base_path in IDSes :" + x._base_path)
        else:
            if verb:
                logger.error(f"Different structure: {x._base_path} and {y._base_path}")
            return False
    else:
        # un-expected different objects
        logger.error(f"Unexpected objects: {type(x)} and {type(y)}")
        return False

    xd = x.__dict__
    yd = y.__dict__
    for key in set(xd.keys()).union(set(yd.keys())):
        if key.startswith("_"):
            continue

        if "hli_utils" == key:
            continue

        if ignore_version and "version_put" == key:
            continue

        if key not in xd:
            if field + "." + key not in output.keys():
                output[field + "." + key] = (
                    field + "." + key,
                    field + "." + key,
                    f"not present in {name_x} ids",
                )
            else:
                logger.error("Duplicate key found")
            if verb:
                logger.info(f"{key} not present in X")
            identical = False
            continue

        if key not in yd:
            if field + "." + key not in output.keys():
                output[field + "." + key] = (
                    field + "." + key,
                    field + "." + key,
                    f"not present in {name_y} ids",
                )
            else:
                logger.error("Duplicate key found")
            if verb:
                logger.info(f"{key} not present in Y")
            identical = False
            continue

        xo = x.__dict__[key]
        yo = y.__dict__[key]
        if not isinstance(xo, type(yo)):
            if field + "." + key not in output.keys():
                output[field + "." + key] = (
                    xo,
                    yo,
                    None,
                    f"different type {name_x} type(Xo), {name_y} type(Yo) ",
                )
            else:
                logger.error("Duplicate key found")
            if verb:
                logger.warning(f"Different type for {field}.{key}")

        if hasattr(xo, "__module__") and "imas" in xo.__module__:
            # TO DO: To be removed, when private _base_path will be replaced by __name__
            if hasattr(xo, "__name__"):
                attrname = xo.__name__
            else:
                attrname = xo._base_path
            identical_result, output = compare_ids(
                xo,
                yo,
                field=f"{field}.{attrname}",
                ignore_version=ignore_version,
                verb=verb,
                name_x=name_x,
                name_y=name_y,
                output=output,
            )
            identical &= identical_result
            continue

        # treatment of struct_array and list of strings
        if type(xo).__name__ == "list":
            data_type = list
            if len(xo) != len(yo):
                # avoids printing "array" as this is internal attribute for AoS
                if key == "array":
                    f = field
                else:
                    f = f"{field}.{key}"

                if f not in output.keys():
                    output[f] = (xo, yo, data_type, "different length")
                else:
                    logger.error("Duplicate key found")
                if verb:
                    logger.info(f"{f} is of different length")
                identical = False
            else:
                for i in range(len(xo)):
                    if "structArrayElement" in type(xo[i]).__name__:
                        identical_result, output = compare_ids(
                            xo[i],
                            yo[i],
                            field=f"{field}[{i}]",
                            ignore_version=ignore_version,
                            verb=verb,
                            name_x=name_x,
                            name_y=name_y,
                            output=output,
                        )
                        identical &= identical_result
                    else:
                        # print("list of "+type(xo[i]).__name__)
                        continue
        else:
            # Check equalities of arrays first as numpy array
            if isinstance(xo, np.ndarray) and isinstance(yo, np.ndarray):
                result = np.array_equal(xo, yo, ARRAY_EQUAL_KWARGS)
                # output[field + "." + key]= (Xo, Yo, "equal")
            # and second as list
            else:
                result = xo == yo
                # output[field + "." + key]= (Xo, Yo, "equal")

            if not result:
                data_type = None
                missing = [False]
                if isinstance(xo, np.ndarray):
                    data_type = np.ndarray
                    if xo.size == 0:
                        missing = [True, name_x]
                    elif yo.size == 0:
                        missing = [True, name_y]
                else:
                    missmap = {int: -999999999, float: -9e40}
                    for t in missmap:
                        if isinstance(xo, t):
                            data_type = t
                            if xo == missmap[t]:
                                missing = [True, name_x]
                            elif yo == missmap[t]:
                                missing = [True, name_y]

                if missing[0]:
                    if field + "." + key not in output.keys():
                        output[field + "." + key] = (
                            xo,
                            yo,
                            data_type,
                            f"missing in {missing[1]}",
                        )
                    else:
                        logger.error("Duplicate key found")
                    if verb:
                        logger.info(f"{field}.{key} is missing in {missing[1]}")
                    identical = False
                else:
                    if field + "." + key not in output.keys():
                        output[field + "." + key] = (
                            xo,
                            yo,
                            data_type,
                            "different values",
                        )
                    else:
                        logger.error("Duplicate key found")
                    if verb:
                        logger.info(f"{field}.{key} has different values")
                    identical = False

    return identical, output


def get_ids_values(uri: str, idspaths: Union[str, list], dd_update=False, verbose=False):
    connection = imas.DBEntry(uri, "r")
    if isinstance(idspaths, str):
        idspaths = [idspaths]

    output = {}
    # Process each IDS path for this pulse
    for full_path, idsname, valpath in idspaths:
        try:
            output[full_path] = None
            if dd_update:
                ids = imas.convert_ids(connection.get(idsname, autoconvert=False), connection.factory.version)
            else:
                ids = connection.get(idsname, autoconvert=False, lazy=True)

            if ":" in valpath:
                node, _, _, _ = partial_get(ids, valpath)
                if node.size == 0:
                    node = None
            else:
                node = eval("ids." + valpath)
                if isinstance(node, imas.ids_primitive.IDSPrimitive) and not node.has_value:
                    node = None
                elif node.size == 0:
                    node = None
            if node is not None:
                output[full_path] = node
        except Exception as e:
            if verbose:
                logger.error(f"Exception for {full_path}: {e}", exc_info=True)

    connection.close()
    return output


def execute_query(
    query: str,
    ids_values: dict,
):
    query_names = {}
    qcounter = 1
    are_values_present = True
    output = None
    for _, ids_value in ids_values.items():
        if ids_value is None:
            are_values_present = False
            break
        _value = ids_value
        if isinstance(_value, str):
            _value = f"'{ids_value}'"
        elif isinstance(_value, imas.ids_primitive.IDSNumericArray):
            _value = _value.value
        query_names[f"x{qcounter}"] = _value
        qcounter += 1
    query_names["np"] = np
    query_names["scipy"] = scipy
    if are_values_present:
        result = eval(query, {}, query_names)
        if result is not None:
            if isinstance(result, (np.bool_, bool)):
                if result:
                    output = True
            else:
                output = result
    return output


def get_quantities_from_pulses(
    idspath: list, pulses: tuple, list_count: int = 0, verbose: bool = False, query=None, dd_update: bool = False
) -> pd.DataFrame:
    """
    The `get_quantities_from_pulses` function retrieves values from specified IDS paths for a given set of pulses and
    returns a DataFrame containing the pulse, run, and corresponding values.

    Args:
        idspath (list or str): The `idspath` parameter is either a single string or a list of strings that represent
            the paths to the IDS nodes from which the quantities will be extracted.
        pulses (tuple): The `pulses` parameter is a tuple containing information about each pulse. Each element in
            the tuple is itself a tuple with the following elements: pulse, run, backend, database, user, version, and
            file path.
        list_count (int): The `list_count` parameter is an optional parameter that specifies the number of pulses to
            retrieve values for. If `list_count` is set to 0 (default), values will be retrieved for all pulses in the
            `pulses` tuple. If `list_count` is set to a positive integer, values will be retrieved for first `listCount`
            pulses in the `pulses` tuple. Defaults to 0
        verbose (bool): print debug information
        query (str, optional): Query string to filter results. Defaults to None.
        dd_update (bool, optional): Flag to indicate whether to update data dictionary. Defaults to False.

    Returns:
        The function returns a pandas DataFrame containing the columns "URI", "FILEPATH", "FILETIME" and
        one column for each IDS path specified.
    """
    # Convert single string to list for consistent handling
    if isinstance(idspath, str):
        idspath = [idspath]

    paths_info = []
    for path in idspath:
        idsname = path.split("/")[0]
        valpath = path[1 + len(idsname) :]
        paths_info.append((path, idsname, valpath.replace("(", "[").replace(")", "]").replace("/", ".")))

    list_counter = 0
    results = []

    for pulse_tuple in pulses:
        pulse = pulse_tuple[0]
        run = pulse_tuple[1]
        backend = pulse_tuple[2]
        database = pulse_tuple[3]
        user = pulse_tuple[4]
        version = pulse_tuple[5]
        file_path = pulse_tuple[6]
        file_time = pulse_tuple[7]

        backend_string = ""
        if backend == imas.ids_defs.MDSPLUS_BACKEND:
            backend_string = "mdsplus"
        if backend == imas.ids_defs.HDF5_BACKEND:
            backend_string = "hdf5"

        uri = f"imas:{backend_string}?user={user};shot={pulse};run={run};database={database};version={version}"
        if verbose:
            print(f"fetching data from {pulse}, {run}")
        found_values = False
        pulse_data = {"URI": uri, "FILEPATH": file_path, "FILETIME": file_time}
        ids_values = get_ids_values(uri, paths_info, dd_update=dd_update, verbose=verbose)
        if ids_values:
            for _path, _value in ids_values.items():
                if _value is None:
                    if verbose:
                        print(uri, _path, "is None, skipping")
                    found_values = False
                    break
                pulse_data[_path] = _value
                if query is None:
                    found_values = True
            if query is not None:
                pulse_data[query] = execute_query(query, ids_values)

                if isinstance(pulse_data[query], (bool, np.bool_)):
                    found_values = True
                elif isinstance(pulse_data[query], np.ndarray):
                    if pulse_data[query].size > 0:
                        found_values = True
                elif pulse_data[query] is not None:
                    found_values = True
        if found_values:
            results.append(pulse_data)
            list_counter += 1

            if list_count != 0 and list_counter >= list_count:
                break
    df = pd.DataFrame(results)

    # If no results were found, create empty dataframe with appropriate columns
    if df.empty:
        columns = ["URI", "FILEPATH", "FILETIME"] + idspath
        df = pd.DataFrame(columns=columns)

    return df


def idsdiff_full(
    struct1: imas.ids_structure.IDSStructure,
    struct2: imas.ids_structure.IDSStructure,
    name1="",
    name2="",
    print_result=False,
    ignore_version=False,
):
    diff_result = []
    compare_result = False
    table_title = Text()
    if isinstance(struct1, imas.ids_toplevel.IDSStructure) and isinstance(struct1, imas.ids_toplevel.IDSStructure):
        table_title.append("First: ", style="bold blue")
        table_title.append(f"{name1} ({struct1.metadata.name}) -\n", style="blue")
        table_title.append("Second: ", style="bold magenta")
        table_title.append(f"{name2} ({struct2.metadata.name})", style="magenta")
    elif isinstance(struct1, imas.ids_structure.IDSStructure) and isinstance(struct1, imas.ids_structure.IDSStructure):
        table_title.append("First: ", style="bold blue")
        table_title.append(f"{name1} ({struct1._path}) -\n", style="blue")
        table_title.append("Second: ", style="bold magenta")
        table_title.append(f"{name2} ({struct2._path})", style="magenta")
    else:
        table_title.append("first - second")
    diff_table = Table(title=table_title)
    diff_table.add_column("first", style="blue")
    diff_table.add_column("second", style="magenta")
    for description, child1, child2 in imas.util.idsdiffgen(struct1, struct2):
        if "_path" in dir(child1):
            if ignore_version is True and "version_put" in child1._path:
                continue
        if not isinstance(child1, imas.ids_base.IDSBase) and not isinstance(child2, imas.ids_base.IDSBase):
            txt1 = f"{description}: {child1}"
            txt2 = f"{description}: {child2}"
        else:
            txt1 = "-" if child1 is None else repr(child1)
            txt2 = "-" if child2 is None else repr(child2)

        seqmat = difflib.SequenceMatcher()
        seqmat.set_seqs(txt1, txt2)

        out1 = Text()
        out2 = Text()
        prevmatch = difflib.Match(0, 0, 0)
        for match in seqmat.get_matching_blocks():
            if match.a > prevmatch.a + prevmatch.size:
                out1.append(txt1[prevmatch.a + prevmatch.size : match.a], "bold red")
            if match.b > prevmatch.b + prevmatch.size:
                out2.append(txt2[prevmatch.b + prevmatch.size : match.b], "bold green")
            out1.append(txt1[match.a : match.a + match.size])
            out2.append(txt2[match.b : match.b + match.size])
            prevmatch = match
        out1.append(txt1[match.a + match.size :], style="bold red")
        out2.append(txt2[match.b + match.size :], style="bold green")
        diff_result.append((description, child1, child2))
        diff_table.add_row(out1, out2)
        diff_table.add_section()
    text_output = None
    if diff_table.row_count:
        compare_result = False
        text_output = diff_table

    else:
        text_output = "Structures", struct1, "and", struct2, "are identical"
        compare_result = True
    if print_result:
        rich.print(text_output)
    return compare_result, diff_result, text_output


def idsdiff(
    struct1: imas.ids_structure.IDSStructure,
    struct2: imas.ids_structure.IDSStructure,
    name1="",
    name2="",
    print_result=False,
    verbose=True,
    ignore_version=False,
):
    diff_result = []
    compare_result = False
    table_title = Text()

    if isinstance(struct1, imas.ids_toplevel.IDSStructure) and isinstance(struct2, imas.ids_toplevel.IDSStructure):
        table_title.append("First: ", style="bold blue")
        table_title.append(f"{name1} ({struct1.metadata.name}) -\n", style="blue")
        table_title.append("Second: ", style="bold magenta")
        table_title.append(f"{name2} ({struct2.metadata.name})", style="magenta")
    elif isinstance(struct1, imas.ids_structure.IDSStructure) and isinstance(struct2, imas.ids_structure.IDSStructure):
        table_title.append("First: ", style="bold blue")
        table_title.append(f"{name1} ({struct1._path}) -\n", style="blue")
        table_title.append("Second: ", style="bold magenta")
        table_title.append(f"{name2} ({struct2._path})", style="magenta")
    else:
        table_title.append("first - second")
    diff_table = Table(title=table_title)
    diff_table.add_column("IDS Path")
    diff_table.add_column("Description")
    if verbose:
        diff_table.add_column("Value first", style="blue")
        diff_table.add_column("Value second", style="magenta")

    for description, child1, child2 in imas.util.idsdiffgen(struct1, struct2):
        if "_path" in dir(child1):
            if ignore_version is True and "version_put" in child1._path:
                continue
        diff_result.append((description, child1, child2))
        information = Text("different values", style="cyan")
        if child1 is None:
            information = Text("missing in first", style="red")
        if child2 is None:
            information = Text("missing in second", style="yellow")
        if isinstance(child1, imas.ids_struct_array.IDSStructArray):
            data_type1 = "STRUCT_ARRAY"
            information = Text("different length", style="magenta")
        else:
            if child1 is None:
                data_type1 = "-"
            else:
                if hasattr(child1, "data_type"):
                    data_type1 = child1.data_type
                else:
                    data_type1 = type(child1).__name__.upper()

        if isinstance(child2, imas.ids_struct_array.IDSStructArray):
            data_type2 = "STRUCT_ARRAY"
            information = Text("different length", style="magenta")
        else:
            if child2 is None:
                data_type2 = "-"
            else:
                if hasattr(child2, "data_type"):
                    data_type2 = child2.data_type
                else:
                    data_type2 = type(child2).__name__.upper()
            # data_type2 = "-" if child2 is None else child2.data_type

        if child1 is not None and hasattr(child1, "_path"):
            path = child1._path
        elif child2 is not None and hasattr(child2, "_path"):
            path = child2._path
        else:
            path = None

        if child1 is not None and hasattr(child1, "value"):
            value1 = child1.value
        else:
            value1 = child1

        if child2 is not None and hasattr(child2, "value"):
            value2 = child2.value
        else:
            value2 = child2

        if type(value1) is np.ndarray:
            value1 = str(value1[0]) + ",..."
        elif type(value1) is list:
            value1 = str(len(value1)) + " items"
        if type(value2) is np.ndarray:
            value2 = str(value2[0]) + ",..."
        elif type(value2) is list:
            value2 = str(len(value2)) + " items"
        if verbose:
            if not isinstance(child1, imas.ids_base.IDSBase) and not isinstance(child2, imas.ids_base.IDSBase):
                txt1 = f"{description}: {child1}"
                txt2 = f"{description}: {child2}"
            else:
                txt1 = "" if data_type1 == "-" else f"({data_type1}) {value1}"
                txt2 = "" if data_type2 == "-" else f"({data_type2}) {value2}"
            seqmat = difflib.SequenceMatcher()
            seqmat.set_seqs(txt1, txt2)
            out1 = Text()
            out2 = Text()
            prevmatch = difflib.Match(0, 0, 0)
            for match in seqmat.get_matching_blocks():
                if match.a > prevmatch.a + prevmatch.size:
                    out1.append(txt1[prevmatch.a + prevmatch.size : match.a], "bold red")
                if match.b > prevmatch.b + prevmatch.size:
                    out2.append(txt2[prevmatch.b + prevmatch.size : match.b], "bold green")
                out1.append(txt1[match.a : match.a + match.size])
                out2.append(txt2[match.b : match.b + match.size])
                prevmatch = match
            out1.append(txt1[match.a + match.size :], style="bold red")
            out2.append(txt2[match.b + match.size :], style="bold green")
        if path:
            if verbose:
                diff_table.add_row(path, information, out1, out2)
            else:
                diff_table.add_row(path, information)
        # diff_table.add_section()

    text_output = None

    if diff_table.row_count:
        compare_result = False
        text_output = diff_table

    else:
        text_output = f"Structures {struct1} and {struct2} are identical"
        compare_result = True
    if print_result:
        rich.print(text_output)
    return compare_result, diff_result, text_output
