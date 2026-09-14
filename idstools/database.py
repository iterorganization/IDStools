import logging
import os
from datetime import datetime
from glob import glob
from pathlib import Path

try:
    import imaspy as imas
except ImportError:
    import imas
import yaml

from idstools.utils.utility_functions import add_query_to_uri

logger = logging.getLogger(f"module.{__name__}")


class DBMaster:
    ALL_BACKENDS = "mdsplus", "hdf5"

    @staticmethod
    def get_user_dir(user: str = None):
        """
        The function `get_user_dir` returns the database directory path for a given user or the current user's directory
        path if no user is specified.

        Args:
            user (str): The `user` parameter is a string that represents the username of the user for whom the
                directory path is being retrieved. If the `user` parameter is not provided or is `None`, it will
                default to the current logged-in user obtained using `os.getlogin()`.

        Returns:
            a file path. If the user is not specified or is "public", it returns the file path to the
            "public/imasdb/" directory in the user's home directory. If the user is not "public", itreturns the
            file path to the "shared/imasdb/" directory in the IMAS_HOME directory.
        """
        if not user:
            user = os.getlogin()
        if user != "public":
            return f'{os.path.expanduser(f"~{user}")}/public/imasdb/'
        imas_home_dir = os.environ["IMAS_HOME"]
        if imas_home_dir is None:
            raise FileNotFoundError("File path in the environment variable IMAS_HOME is not defined.")
        return f"{imas_home_dir}/shared/imasdb/"

    @staticmethod
    def get_database_dir(database: str, user: str = None):
        """
        The function `get_database_dir` returns the directory path for a given database, and raises an error
        if the path does not exist.

        Args:
            database (str): The `database` parameter is a string that represents the name of the database
                file or directory.
            user (str): The `user` parameter is an optional parameter that represents the user for whom the
                database directory is being retrieved.

        Returns:
            the directory path of the specified database if it exists. If the database does not exist, it
            raises a FileNotFoundError. If the database parameter is None, it returns None.
        """
        user_dir = DBMaster.get_user_dir(user)

        if database is not None:
            user_database_dir = user_dir + database
            if os.path.exists(user_database_dir):
                return user_database_dir
            else:
                raise FileNotFoundError(
                    "The path provided does not exist or has no such database file or directory. \
                        Please check spelling."
                )
        return None

    @staticmethod
    def get_version_dir(version: str, database: str, user: str = None):
        """
        The function `get_version_dir` returns the directory path for a specific version of a database,
        given the version, database name, and optional user.

        Args:
            version (str): The version parameter is a string that represents the version of the database.
            database (str): The `database` parameter is a string that represents the name of the database.
            user (str): The `user` parameter is an optional parameter

        Returns:
            the directory path for the specified version of a database. If the version directory exists,
            it returns the path. If the version directory does not exist, it raises a FileNotFoundError.
            If the version parameter is None, it returns None.
        """
        database_dir = DBMaster.get_database_dir(database, user)
        if version is not None:
            version_dir = f"{database_dir}/{version}"
            if os.path.exists(version_dir):
                return version_dir
        return None

    @staticmethod
    def get_databases(user: str = None) -> list:
        """
        The function `get_databases` returns a sorted list of databases in a user's directory.

        Args:
            user (str): The `user` parameter is a string that represents the username of the user
                for whom the databases are being retrieved.

        Returns:
            a list of databases.
        """
        user_dir = DBMaster.get_user_dir(user)
        databases = [
            _database for _database in os.listdir(user_dir) if os.path.isdir(os.path.join(user_dir, _database))
        ]
        return sorted(databases)

    @staticmethod
    def get_versions(database: str, user: str = None) -> list:
        """
        The function `get_versions` returns a sorted list of versions in a given database directory.

        Args:
            database (str): A string representing the name of the database.
            user (str): The `user` parameter is an optional parameter

        Returns:
            a sorted list of versions.
        """
        database_dir = DBMaster.get_database_dir(database, user)
        versions = [
            _version for _version in os.listdir(database_dir) if os.path.isdir(os.path.join(database_dir, _version))
        ]
        return sorted(versions)

    @staticmethod
    def get_databases_with_versions(user: str = None) -> list:
        """
        The function `get_databases_with_versions` returns a list of tuples, where each tuple contains
        the  name of a database and a list of its versions, for a given user.

        Args:
            user (str): The `user` parameter is a string that represents the username or identifier of
                the  user for whom the databases and their versions are being retrieved. It is an optional
                parameter and can be set to `None` if not applicable.

        Returns:
            a list of tuples. Each tuple contains the name of a database and a list of versions associated
            with that database. The list is sorted by the database names.
        """
        user_dir = DBMaster.get_user_dir(user)
        databases_dict = {}
        for _database in os.listdir(user_dir):
            if not os.path.isdir(os.path.join(user_dir, _database)):
                continue
            _database_versions = DBMaster.get_versions(_database, user)
            databases_dict[_database] = _database_versions
        return [(database, databases_dict[database]) for database in sorted(databases_dict.keys())]

    @staticmethod
    def get_versions_with_databases(user: str = None) -> list:
        """
        The function `get_versions_with_databases` returns a list of tuples, where each tuple contains a version
        number and a list of databases associated with that version.

        Args:
            user (str): The `user` parameter is an optional string
        Returns:
            a list of tuples. Each tuple contains a version number and a list of databases that have that version.
        The list is sorted in ascending order based on the version numbers.
        """
        database_with_versions_dict = DBMaster.get_databases_with_versions(user=user)

        database_dict = {}
        for database, versions in database_with_versions_dict:
            for _version in versions:
                if _version not in database_dict:
                    database_dict[_version] = []
                database_dict[_version].append(database)
        return [(version, database_dict[version]) for version in sorted(database_dict.keys())]

    @staticmethod
    def get_hdf5_pulses(
        user: str = None, database: str = None, version: str = None, status=None, as_dictionary=False
    ) -> list:
        """
        The function `get_hdf5_pulses` retrieves a list of pulses from HDF5 master files. It needs to specify
        full path till version.

        Args:
            user (str): The `user` parameter is a string that represents the user for whom the MDSPlus
                pulses are being retrieved.
            database (str): The `database` parameter is a string that represents the name of the database.
                It is used to specify the directory where the MDSplus pulses are stored.
            version (str): The `version` parameter is used to specify the version of the MDSplus database.
                It is a string that represents the version number.
            as_dictionary (bool): The `as_dictionary` parameter is a boolean flag that determines the format
                of the returned pulses. If `as_dictionary` is set to `True`, the pulses will be returned as a
                dictionary where the keys are the pulse numbers and the values are lists of runs associated
                with each pulse.Defaults to False

        Returns:
            a list of tuples. Each tuple contains the following elements, The tuple includes the pulse number,
            run number, HDF5_BACKEND backend, database, user, version, and data file path.
        """
        pulses = {} if as_dictionary else []
        version_dir = DBMaster.get_version_dir(version, database, user)
        if version_dir is None:
            return pulses
        scenario_yaml_dir = os.path.join(version_dir, "0")

        hdf5_master_file_paths = glob(f"{version_dir}/**/*master.h5", recursive=True)
        for hdf5_master_file_path in hdf5_master_file_paths:
            run = hdf5_master_file_path.split("/")[-2]
            if not run.isdigit():
                print(f"warning:run number is not an integer {run} {hdf5_master_file_path}")
                continue
            run = int(run)
            pulse = hdf5_master_file_path.split("/")[-3]
            if not pulse.isdigit():
                print(f"warning:pulse number is not an integer {pulse}/{run} {hdf5_master_file_path}")
                continue
            pulse = int(pulse)

            file_time = datetime.fromtimestamp(os.path.getmtime(hdf5_master_file_path)).replace(microsecond=0)
            if status is not None:
                yaml_file = f"ids_{pulse}{str(run).zfill(4)}.yaml"
                yaml_file_path = os.path.join(scenario_yaml_dir, yaml_file)
                status_from_yaml = ""
                if os.path.exists(yaml_file_path):
                    status_from_yaml = DBMaster.get_pulse_status(yaml_file_path)
                    if status_from_yaml == "":
                        print(f"warning:could not find status info in scenario file {pulse}/{run} {yaml_file_path}")
                else:
                    print(f"warning:scenario summary file does not exists for {pulse}/{run} {yaml_file_path}")
                if status != status_from_yaml:
                    continue
            if as_dictionary:
                if pulse not in pulses:
                    pulses[pulse] = []
                pulses[pulse].append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.HDF5_BACKEND,
                        database,
                        user,
                        version,
                        hdf5_master_file_path,
                        file_time,
                    )
                )
            else:
                pulses.append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.HDF5_BACKEND,
                        database,
                        user,
                        version,
                        hdf5_master_file_path,
                        file_time,
                    )
                )
        return pulses

    @staticmethod
    def get_hdf5_pulses_from_folder(folder: str = None, as_dictionary=False) -> list:

        pulses = {} if as_dictionary else []
        hdf5_master_file_paths = glob(f"{folder}/**/*master.h5", recursive=True)
        for hdf5_master_file_path in hdf5_master_file_paths:
            run = hdf5_master_file_path.split("/")[-2]
            if run.isdigit():
                run = int(run)
            else:
                run = 0
            pulse = hdf5_master_file_path.split("/")[-3]
            if pulse.isdigit():
                pulse = int(pulse)
            else:
                pulse = 0

            file_time = datetime.fromtimestamp(os.path.getmtime(hdf5_master_file_path)).replace(microsecond=0)
            if as_dictionary:
                if hdf5_master_file_path not in pulses:
                    pulses[hdf5_master_file_path] = []
                pulses[hdf5_master_file_path].append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.HDF5_BACKEND,
                        hdf5_master_file_path,
                        file_time,
                    )
                )
            else:
                pulses.append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.HDF5_BACKEND,
                        hdf5_master_file_path,
                        file_time,
                    )
                )
        return pulses

    @staticmethod
    def get_mds_plus_pulses(
        user: str = None,
        database: str = None,
        version: str = None,
        status: str = None,
        as_dictionary=False,
    ) -> list:
        """
        The function `get_mds_plus_pulses` retrieves a list of MDSPlus pulses based on the provided user, database,
        version, and status parameters.

        Args:
            user (str): The `user` parameter is a string that represents the user for whom the MDSPlus
                pulses are being retrieved.
            database (str): The `database` parameter is a string that represents the name of the database.
                It is used to specify the directory where the MDSplus pulses are stored.
            version (str): The `version` parameter is used to specify the version of the MDSplus database.
                It is a string that represents the version number.
            status (str): The "status" parameter is used to filter the pulses based on their status. If a
                status is provided, only pulses with that status will be included in the result. If no status
                is provided, all pulses will be included.
            as_dictionary (bool): The `as_dictionary` parameter is a boolean flag that determines the format
                of the returned pulses. If `as_dictionary` is set to `True`, the pulses will be returned as a
                dictionary where the keys are the pulse numbers and the values are lists of runs associated
                with each pulse.Defaults to False

        Returns:
            a list of pulses.
        """
        pulses = {} if as_dictionary else []
        mdsplus_dir = DBMaster.get_version_dir(version, database, user)
        if mdsplus_dir is None:
            return pulses
        scenario_yaml_dir = os.path.join(mdsplus_dir, "0")

        datafile_paths = glob(f"{mdsplus_dir}/**/*.datafile", recursive=True)

        for data_file_path in datafile_paths:
            root = os.path.dirname(data_file_path)
            datafile = os.path.basename(data_file_path)
            run_list = (root[len(mdsplus_dir) + 1 :]).split("/")
            if len(run_list) == 1:  # AL4 layout
                num_start_pos = datafile.find("_") + 1
                num_end_pos = datafile.rfind(".")
                num = int(datafile[num_start_pos:num_end_pos])
                pulse = num // 10000
                if not run_list[0].isdigit():
                    print(f"warning:run number is not an integer {run_list[0]} {data_file_path}")
                    continue
                run = int(run_list[0]) * 10000 + (num % 10000)

            else:  # AL5 layout
                if datafile != "ids_001.datafile":
                    print(f"warning:ids_001.datafile does not exists {data_file_path}")
                    continue
                if os.path.islink(data_file_path):
                    continue
                run = root.split("/")[-1]
                if not run.isdigit():
                    print(f"warning:run number is not an integer {run} {data_file_path}")
                    continue
                run = int(run)
                pulse = root.split("/")[-2]
                if not pulse.isdigit():
                    print(f"warning:pulse number is not an integer {pulse}/{run} {data_file_path}")
                    continue
                pulse = int(pulse)

            if status is not None:
                yaml_file = f"ids_{pulse}{str(run).zfill(4)}.yaml"
                yaml_file_path = os.path.join(scenario_yaml_dir, yaml_file)
                status_from_yaml = ""
                if os.path.exists(yaml_file_path):
                    status_from_yaml = DBMaster.get_pulse_status(yaml_file_path)
                    if status_from_yaml == "":
                        print(f"warning:could not find status info in scenario file {pulse}/{run} {yaml_file_path}")
                else:
                    print(f"warning:scenario summary file does not exists for {pulse}/{run} {yaml_file_path}")
                if status != status_from_yaml:
                    continue

            file_time = datetime.fromtimestamp(os.path.getmtime(data_file_path)).replace(microsecond=0)

            if as_dictionary:
                if pulse not in pulses:
                    pulses[pulse] = []
                is_run_available = any(x[1] == run for x in pulses[pulse])
                if not is_run_available:
                    pulses[pulse].append(
                        (
                            pulse,
                            run,
                            imas.ids_defs.MDSPLUS_BACKEND,
                            database,
                            user,
                            version,
                            data_file_path,
                            file_time,
                        )
                    )
            else:
                pulses.append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.MDSPLUS_BACKEND,
                        database,
                        user,
                        version,
                        data_file_path,
                        file_time,
                    )
                )
        return pulses

    @staticmethod
    def get_mds_plus_pulses_from_folder(
        folder: str = None,
        as_dictionary=False,
    ) -> list:
        pulses = {} if as_dictionary else []

        datafile_paths = glob(f"{folder}/**/*.datafile", recursive=True)

        for data_file_path in datafile_paths:
            root = os.path.dirname(data_file_path)
            datafile = os.path.basename(data_file_path)
            run_list = (root[len(folder) + 1 :]).split("/")
            if len(run_list) == 1 and run_list[0] != "":  # AL4 layout
                num_start_pos = datafile.find("_") + 1
                num_end_pos = datafile.rfind(".")
                num = int(datafile[num_start_pos:num_end_pos])
                pulse = num // 10000
                run = 0
                if run_list[0].isdigit():
                    run = int(run_list[0]) * 10000 + (num % 10000)

            else:  # AL5 layout
                if datafile != "ids_001.datafile":
                    continue
                run = root.split("/")[-1]
                if not run.isdigit():
                    run = int(run)
                else:
                    run = 0
                pulse = root.split("/")[-2]
                if not pulse.isdigit():
                    pulse = int(pulse)
                else:
                    pulse = 0
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(data_file_path)).replace(microsecond=0)
            except FileNotFoundError:
                print(f"warning:invalid file {data_file_path}")
                continue

            if as_dictionary:
                if data_file_path not in pulses:
                    pulses[data_file_path] = []
                is_run_available = any(x[1] == run for x in pulses[data_file_path])
                if not is_run_available:
                    pulses[data_file_path].append(
                        (
                            pulse,
                            run,
                            imas.ids_defs.MDSPLUS_BACKEND,
                            data_file_path,
                            file_time,
                        )
                    )
            else:
                pulses.append(
                    (
                        pulse,
                        run,
                        imas.ids_defs.MDSPLUS_BACKEND,
                        data_file_path,
                        file_time,
                    )
                )
        return pulses

    @staticmethod
    def get_pulse_status(yaml_file_path) -> str:
        """
        The function `get_pulse_status` reads a YAML file from a given path and returns the value of the
        "status" key in the file's metadata.

        Args:
            yaml_file_path: The `path` parameter is a string that represents the file path to a YAML file.

        Returns:
            the value of the "status" key from the metadata dictionary.
        """
        _yaml_file_path = Path(yaml_file_path)

        status = ""
        with open(_yaml_file_path, "r") as file_handle:
            lines = file_handle.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("status:"):
                    start_index = max(0, i - 1)
                    end_index = min(len(lines), i + 2)
                    context = lines[start_index:end_index]
                    combined_context = "".join(context)
                    metadata = yaml.load(combined_context, Loader=yaml.Loader)
                    if isinstance(metadata, dict):
                        status = metadata["status"]
        return status

    @staticmethod
    def get_database_files(user=None, database=None, version=None, backends=None):
        """
        The function `get_database_files` retrieves a list of database files based on the specified user,
        database, version, and backends.

        Args:
            user: The ``user`` parameter is used to specify the user for whom the database files are being
                retrieved. If no user is specified, it defaults to ``None``.
            database: The ``database`` parameter is used to specify the name of the database.
            version: The ``version`` parameter is used to specify a specific version of the database.
            backends: The ``backends`` parameter is a list of strings that specifies the database backends to
                retrieve files from. The possible values for ``backends`` are ``hdf5`` and ``mdsplus``. If ``backends``
                is not provided, it defaults to ``DBMaster.ALL_BACKENDS``

        Returns:
            The function ``get_database_files`` returns a list of tuples. Each tuple contains the name of a database,
            followed by a list of tuples. Each inner tuple contains a version number, followed by a list of tuples.
            Each innermost tuple contains the name of a backend (either ``hdf5`` or ``mdsplus``), followed by a
            dictionary of database files.
        """
        result = []

        if not backends:
            backends = DBMaster.ALL_BACKENDS

        databases = [database] if database else DBMaster.get_databases(user)
        for database in databases:
            database_files = []
            versions = [version] if version else DBMaster.get_versions(database, user)
            for _version in versions:
                pulses = []
                for backend in backends:
                    if backend == "hdf5":
                        dbs = DBMaster.get_hdf5_pulses(user, database, _version, as_dictionary=True)
                    elif backend == "mdsplus":
                        dbs = DBMaster.get_mds_plus_pulses(user, database, _version, as_dictionary=True)
                    else:
                        raise NotImplementedError(f"Unsupported backend: {backend}")
                    if dbs:
                        pulses.append((backend, dbs))
                if pulses:
                    database_files.append((_version, pulses))
            if database_files:
                result.append((database, database_files))
        return result

    @staticmethod
    def get_database_files_from_folder(folder=None, backends=None):
        """
        Retrieve database files from a folder based on specified backends.

        Parameters
        ----------
        folder : str, optional
            The folder path from which to retrieve database files.
        backends : list, optional
            A list of strings specifying the database backends to retrieve files from.
            The possible values for backends are 'hdf5' and 'mdsplus'. If backends
            is not provided, it defaults to DBMaster.ALL_BACKENDS

        Returns
        -------
        list
            A list of tuples. Each tuple contains the backend name (either 'hdf5' or 'mdsplus'),
            followed by a dictionary of database files.
        """
        if not backends:
            backends = DBMaster.ALL_BACKENDS

        pulses = []
        for backend in backends:
            if backend == "hdf5":
                dbs = DBMaster.get_hdf5_pulses_from_folder(folder, as_dictionary=True)
            elif backend == "mdsplus":
                dbs = DBMaster.get_mds_plus_pulses_from_folder(folder, as_dictionary=True)
            else:
                raise NotImplementedError(f"Unsupported backend: {backend}")
            if dbs:
                pulses.append((backend, dbs))
        return pulses

    @staticmethod
    def get_hdf5_physical_file(user, database, version, pulse, run):
        """
        The function `get_hdf5_physical_file` returns the path to an HDF5 file based on the user, database, version,
        pulse, and run.

        Args:
            user: The "user" parameter represents the name of the user who is accessing the HDF5 physical file.
            database: The "database" parameter refers to the name of the database where the HDF5 files are stored.
            version: The "version" parameter represents the version of the database.
            pulse: The "pulse" parameter represents the pulse number. It is a numerical value that identifies a
                specific pulse in a dataset.
            run: The "run" parameter represents the run number.

        Returns:
            the path to an HDF5 physical file.
        """
        hdf5dir = os.path.join(DBMaster.get_user_dir(user), database, version, "hdf5")
        return os.path.join(hdf5dir, f"ids_{str(pulse)}_{str(run)}.hd5")

    @staticmethod
    def get_mdsplus_physical_files(user, database, version, pulse, run):
        """
        The function `get_mdsplus_physical_files` returns the MDS+ database filenames for a given IMAS
        database.

        Args:
            user: The "user" parameter is the username of the user accessing the IMAS database.
            database: The `database` parameter refers to the name of the IMAS database.
            version: The "version" parameter represents the version of the IMAS database.
            pulse: The parameter "pulse" represents the pulse number in the IMAS database.
            run: The "run" parameter is the run number.

        Returns:
            The function `get_mdsplus_physical_files` returns a tuple of three strings. The first string is the
            filename with the extension ".characteristics", the second string is the filename with the extension
            ".datafile", and the third string is the filename with the extension ".tree".
        """
        mdsplusdir = os.path.join(DBMaster.get_user_dir(user), database, version)
        # filename is ids_<shot><run> where run is last four digits of run number,
        # right-aligned (filled with zeros).
        # Examples: 1
        run_string = str(run % 10000)
        if pulse == 0:
            mdsplus_file_name = os.path.join(mdsplusdir, str(int(run / 10000)), f"ids_{run_string.zfill(3)}")
        else:
            mdsplus_file_name = os.path.join(
                mdsplusdir,
                str(int(run / 10000)),
                f"ids_{str(pulse)}{run_string.zfill(4)}",
            )
        return (
            f"{mdsplus_file_name}.characteristics",
            f"{mdsplus_file_name}.datafile",
            f"{mdsplus_file_name}.tree",
        )

    @staticmethod
    def get_physical_files(user, database, version, pulse, run, backend):
        """
        The function `get_physical_files` returns the physical files storing a database based on the
        specified backend.

        Args:
            user: The user parameter represents the user who is requesting the physical files.
            database: The "database" parameter refers to the name or identifier of the database for which you
                want to retrieve the physical files.
            version: The version parameter represents the version of the database. It is used to retrieve the
                physical files associated with a specific version of the database.
            pulse: The "pulse" parameter refers to a specific pulse or shot number in a database. It is used to
                identify a particular data acquisition event or experiment.
            run: The "run" parameter is used to specify the run number or identifier for the database. It is
                likely used to retrieve the physical files associated with a specific run of the database.
            backend: The "backend" parameter refers to the type of database backend being used. It can have
                two possible values: "mdsplus" or "hdf5".

        Returns:
            The function `get_physical_files` returns the physical file path storing the specified database.
        """
        """Return files storing this database."""
        if backend == "mdsplus":
            return DBMaster.get_mdsplus_physical_files(user, database, version, pulse, run)
        elif backend == "hdf5":
            return DBMaster.get_hdf5_physical_file(user, database, version, pulse, run)
        else:
            raise NotImplementedError(f"Unsupported backend: {backend}")

    @classmethod
    def get_dd_version(cls):
        factory = imas.ids_factory.IDSFactory()
        return factory.dd_version

    @classmethod
    def create_connection(cls, imasargs, target_dd_version=None):
        if "mode" not in imasargs.__dict__:
            imasargs.mode = "w"
        connection = None
        if imasargs.uri != "" and imasargs.uri is not None:
            connection = imas.DBEntry(imasargs.uri, imasargs.mode, dd_version=target_dd_version)
        return connection

    @classmethod
    def get_connection(cls, imasargs):
        connection = None
        if imasargs.uri != "" and imasargs.uri is not None:
            uri = add_query_to_uri(
                imasargs.uri,
                backend="uda",
                query="cache_mode=none",
            )
            if "mode" in imasargs.__dict__:
                connection = imas.DBEntry(uri, imasargs.mode)
            else:
                try:
                    connection = imas.DBEntry(uri, "r")
                except Exception as e:
                    print(e)
        return connection

    @staticmethod
    def pulse_list2_dict(pulselist):
        """Utility function that returns a dict from a list of pairs (pulse,run)

        Parameters
        ----------
        pulselist: list of tuples
            List of tuples (pulse,run)

        Returns
        -------
        dict key=pulse:value=[runs]
        """
        pulsedict = {}
        for pulse, run in pulselist:
            pulsedict.setdefault(pulse, []).append(run)
        return pulsedict

    @staticmethod
    def mds_list_pulse_run(locpath, with_status=None, as_dict=False):
        """Function that lists Pulse and Run numbers from a given database, in MDSPLUS

        Parameters
        ----------
        locpath: str or Path
            Path in which the database files are stored
        with_status: str
            If set, will list only pulses with given status (in associated yaml file, e.g. 'obsolete', 'active')

        Returns
        -------
        list of tuple (pulse,run)
        """

        locpath = Path(locpath).expanduser()
        if not locpath.exists():
            raise FileNotFoundError(
                "The path provided does not exist or has no such database file or directory. Please check spelling."
            )
        pulses = []
        # folder = Path(locpath).glob('**/*.datafile') # --> does not work with
        # linked subfolders (https://bugs.python.org/issue33428)
        folder = glob(str(locpath) + "/**/*.datafile", recursive=True)
        for entry in folder:
            if (with_status is None) or (with_status == DBMaster.get_pulse_status(Path(entry).with_suffix(".yaml"))):

                file = entry.split("/")[-1].split("_")[1].split(".")[0]
                if len(file) <= 4:
                    pulse = int(entry.split("/")[-3])
                    run = int(entry.split("/")[-2])
                else:
                    pulse = int(file[0:-4])
                    run = int(file[-4:])
                # run = int(file[-4:]) + 10000 * int(entry.split("/")[-2])
                pulses.append((pulse, run))

        pulses_set = set(pulses)
        return list(pulses_set)

    @staticmethod
    def hdf5_list_pulse_run(locpath):
        """Function that lists Pulse and Run numbers from a given database, in HDF5

        Parameter
        ---------
        locpath: str or Path
            Path in which the database files are stored

        Returns
        -------
        list of tuple (pulse,run)
        """

        locpath = Path(locpath).expanduser()
        if not locpath.exists():
            raise FileNotFoundError(
                "The path provided does not exist or has no such database file or directory. Please check spelling."
            )
        pulses = []
        # folder = Path(locpath).glob('**/*master.h5')
        folder = glob(str(locpath) + "/**/*master.h5", recursive=True)

        for entry in folder:
            _pulse = pulse = str(entry).split("/")[-3]
            _run = run = str(entry).split("/")[-2]
            if _pulse.isdigit():
                pulse = int(str(entry).split("/")[-3])
            if _run.isdigit():
                run = int(str(entry).split("/")[-2])
            pulses.append((pulse, run))
        return pulses

    @staticmethod
    def get_db_Path(user, database, version):
        """Function that returns a pathlib Path to desired database, depending on the user, database and
        version names.

        Parameters
        ---------
        user: str
            Status of user: either public or local. A public user should just be left as public, whereas a
            local user should write their proper identifier

        database: str
            Name of database where the data is harbored

        version: str
            String of number of data version

        Returns
        -------
        pathlib.Path
        """

        if user == "public":
            locpath = Path(os.environ["IMAS_HOME"] + "/shared/imasdb/" + database + "/" + version)
        else:
            locpath = Path(os.path.expanduser("~" + user) + "/public/imasdb/" + database + "/" + version)
        return locpath


def read_scenario(
    scenario_file_path: str,
    in_ids_list: list = None,
    out_ids_list: list = None,
    test_mode: bool = False,
    **test_args,
):
    """
    This function reads a scenario file and takes in optional input and output IDs lists, as well as a  test
    mode flag and additional test arguments.

    Args:
        scenario_file_path (str): The file path of the scenario file that contains the test cases.
        in_ids_list (list): A list of input IDS names that should be read from the scenario file.
        out_ids_list (list): A list of output IDS names  It is used to specify the list of output IDs that
            the function should read from the scenario file. If this parameter is not provided, the function
            will read all output IDs from the scenario file.
        test_mode (bool): A boolean flag indicating whether the function is being called in test mode or not.
            If test_mode is True, the function will execute in a way that is suitable for testing purposes.
            Defaults to False
    """
    test_args_list = list(test_args.values())

    in_ids_dict = {}
    out_ids_dict = {}
    if in_ids_list is None:
        in_ids_list = []

    if out_ids_list is None:
        out_ids_list = []
    with open(scenario_file_path, "r") as scenario_file:
        config = yaml.load(scenario_file, Loader=yaml.Loader)

    # Read the equilibrium and core_profiles IDSs from the input datafile
    connection_in = imas.DBEntry(
        imas.ids_defs.MDSPLUS_BACKEND,
        config["input_database"],
        config["shot"],
        config["run_in"],
        config["input_user_or_path"],
    )
    connection_in.open()
    for ids_name in in_ids_list:
        if test_mode:
            ids = connection_in.get_slice(ids_name, test_args_list)
        else:
            ids = connection_in.get(ids_name)
        in_ids_dict[ids_name] = ids

    connection_in.close()

    # Read the out IDS from the output datafile
    connection_out = imas.DBEntry(
        imas.ids_defs.MDSPLUS_BACKEND,
        config["output_database"],
        config["shot"],
        config["run_out"],
        (os.getenv("USER") if config["output_user_or_path"] == "default" else config["output_user_or_path"]),
    )
    # print(config["output_database"])
    # print(config["shot"])
    # print(config["run_out"])
    # print(config["output_user_or_path"])
    connection_out.open()
    for ids_name in out_ids_list:
        if test_mode:
            ids = connection_out.get_slice(ids_name, test_args_list)
        else:
            ids = connection_out.get(ids_name)
        out_ids_dict[ids_name] = ids
    connection_out.close()
    import argparse

    inputargs = argparse.Namespace()
    inputargs.backend = imas.ids_defs.MDSPLUS_BACKEND
    inputargs.pulse = config["shot"]
    inputargs.run = config["run_in"]
    inputargs.user = config["input_user_or_path"]
    inputargs.database = config["input_database"]
    inputargs.version = 3
    inputargs.uri = None

    return in_ids_dict, out_ids_dict, inputargs


def read_scenario_with_args(
    imasargs,
    in_ids_list: list = None,
    out_ids_list: list = None,
    test_mode: bool = False,
    **test_args,
):
    """
    This function reads a scenario file and takes in optional input and output IDs lists, as well as a
    test mode flag and additional test arguments.

    Args:
        imasargs (str): The file path of the scenario file that contains the test cases.
        in_ids_list (list): A list of input IDS names that should be read from the scenario file.
        out_ids_list (list): A list of output IDS names  It is used to specify the list of output IDs that the
            function should read from the scenario file. If this parameter is not provided, the function will read
            all output IDs from the scenario file.
        test_mode (bool): A boolean flag indicating whether the function is being called in test mode or not.
            If test_mode is True, the function will execute in a way that is suitable for testing purposes.
            Defaults to False
    """
    test_args_list = list(test_args.values())

    in_ids_dict = {}
    out_ids_dict = {}
    if in_ids_list is None:
        in_ids_list = []

    if out_ids_list is None:
        out_ids_list = []
    connection = DBMaster.get_connection(imasargs)

    if connection is None:
        return None
    for ids_name in in_ids_list:
        if test_mode:
            ids = connection.get_slice(ids_name, test_args_list)
        else:
            ids = connection.get(ids_name, autoconvert=False)
        in_ids_dict[ids_name] = ids

    for ids_name in out_ids_list:
        if test_mode:
            ids = connection.get_slice(ids_name, test_args_list)
        else:
            ids = connection.get(ids_name, autoconvert=False)
        out_ids_dict[ids_name] = ids
    connection.close()

    return in_ids_dict, out_ids_dict
