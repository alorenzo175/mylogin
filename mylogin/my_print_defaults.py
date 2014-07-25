#
# Copyright (c) 2013 Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

"""
This module provides features to read MySQL configuration files, wrapping the
tool my_print_defaults.
"""

import optparse
import os
import os.path
import re
import subprocess
import tempfile

from mylogin.exception import UtilError


_MY_PRINT_DEFAULTS_TOOL = "my_print_defaults"
_MYLOGIN_FILE = ".mylogin.cnf"


def _add_basedir(search_paths, path_str):
    """Add a basedir and all known sub directories

    This method builds a list of possible paths for a basedir for locating
    special MySQL files like mysqld (mysqld.exe), etc.

    search_paths[inout] List of paths to append
    path_str[in]        The basedir path to append
    """
    search_paths.append(path_str)
    search_paths.append(os.path.join(path_str, "sql"))       # for source trees
    search_paths.append(os.path.join(path_str, "client"))    # for source trees
    search_paths.append(os.path.join(path_str, "share"))
    search_paths.append(os.path.join(path_str, "scripts"))
    search_paths.append(os.path.join(path_str, "bin"))
    search_paths.append(os.path.join(path_str, "libexec"))
    search_paths.append(os.path.join(path_str, "mysql"))


def get_tool_path(basedir, tool, fix_ext=True, required=True,
                  defaults_paths=None, search_PATH=False):
    """Search for a MySQL tool and return the full path

    basedir[in]         The initial basedir to search (from mysql server)
    tool[in]            The name of the tool to find
    fix_ext[in]         If True (default is True), add .exe if running on
                        Windows.
    required[in]        If True (default is True), and error will be
                        generated and the utility aborted if the tool is
                        not found.
    defaults_paths[in]  Default list of paths to search for the tool.
                        By default an empty list is assumed, i.e. [].
    search_PATH[in]     Boolean value that indicates if the paths specified by
                        the PATH environment variable will be used to search
                        for the tool. By default the PATH will not be searched,
                        i.e. search_PATH=False.
    Returns (string) full path to tool
    """
    if not defaults_paths:
        defaults_paths = []
    search_paths = []

    if basedir:
        # Add specified basedir path to search paths
        _add_basedir(search_paths, basedir)
    if defaults_paths and len(defaults_paths):
        # Add specified default paths to search paths
        for path in defaults_paths:
            search_paths.append(path)
    else:
        # Add default basedir paths to search paths
        _add_basedir(search_paths, "/usr/local/mysql/")
        _add_basedir(search_paths, "/usr/sbin/")
        _add_basedir(search_paths, "/usr/share/")

    # Search in path from the PATH environment variable
    if search_PATH:
        for path in os.environ['PATH'].split(os.pathsep):
            search_paths.append(path)

    if os.name == "nt" and fix_ext:
        tool = tool + ".exe"
    # Search for the tool
    for path in search_paths:
        norm_path = os.path.normpath(path)
        if os.path.isdir(norm_path):
            toolpath = os.path.join(norm_path, tool)
            if os.path.isfile(toolpath):
                return toolpath
            else:
                if tool == "mysqld.exe":
                    toolpath = os.path.join(norm_path, "mysqld-nt.exe")
                    if os.path.isfile(toolpath):
                        return toolpath
    if required:
        raise UtilError("Cannot find location of %s." % tool)

    return None


def my_login_config_path():
    """Return the default path of the mylogin file (.mylogin.cnf).
    """
    if os.name == 'posix':
        # File located in $HOME for non-Windows systems
        return os.path.expanduser('~')
    else:
        # File located in %APPDATA%\MySQL for Windows systems
        return r'{0}\MySQL'.format(os.environ['APPDATA'])


def my_login_config_exists():
    """Check if the mylogin file (.mylogin.cnf) exists.
    """

    my_login_fullpath = os.path.normpath(my_login_config_path() + "/"
                                         + _MYLOGIN_FILE)
    return os.path.isfile(my_login_fullpath)


class MyDefaultsReader(object):
    """The MyDefaultsReader class is used to read the data stored from a MySQL
    configuration file. This class provide methods to read the options data
    stored in configurations files, using the my_print_defaults tool. To learn
    more about my_print_defaults see:
    http://dev.mysql.com/doc/en/my-print-defaults.html
    """

    def __init__(self, options=None, find_my_print_defaults_tool=True):
        """Constructor

        options[in]                 dictionary of options (e.g. basedir). Note,
                                    allows options values from optparse to be
                                    passed directly to this parameter.
        find_my_print_defaults[in]  boolean value indicating if the tool
                                    my_print_defaults should be located upon
                                    initialization of the object.
        """
        if options is None:
            options = {}
        # _config_data is a dictionary of option groups containing a dictionary
        # of the options data read from the configuration file.
        self._config_data = {}

        # Options values from optparse can be directly passed, check if it is
        # the case and handle them correctly.
        if isinstance(options, optparse.Values):
            try:
                self._basedir = options.basedir  # pylint: disable=E1103
            except AttributeError:
                # if the attribute is not found, then set it to None (default).
                self._basedir = None
            try:
                # if the attribute is not found, then set it to 0 (default).
                self._verbosity = options.verbosity  # pylint: disable=E1103
            except AttributeError:
                self._verbosity = 0
        else:
            self._basedir = options.get("basedir", None)
            self._verbosity = options.get("verbosity", 0)

        if find_my_print_defaults_tool:
            self.search_my_print_defaults_tool()
        else:
            self._tool_path = None

    @property
    def tool_path(self):
        """Sets tool_path property
        """
        return self._tool_path

    def search_my_print_defaults_tool(self, search_paths=None):
        """Search for the tool my_print_defaults.
        """
        if not search_paths:
            search_paths = []

        # Set the default search paths (i.e., default location of the
        # .mylogin.cnf file).
        default_paths = [my_login_config_path()]

        # Extend the list of path to search with the ones specified.
        if search_paths:
            default_paths.extend(search_paths)

        # Search for the tool my_print_defaults.
        try:
            self._tool_path = get_tool_path(self._basedir,
                                            _MY_PRINT_DEFAULTS_TOOL,
                                            defaults_paths=default_paths,
                                            search_PATH=True)
        except UtilError as err:
            raise UtilError("Unable to locate MySQL Client tools. "
                            "Please confirm that the path to the MySQL client "
                            "tools are included in the PATH. Error: %s"
                            % err.errmsg)

    def check_tool_version(self, major_version, minor_version):
        """Check the version of the my_print_defaults tool.

        Returns True if the version of the tool is equal or above the one that
        is specified, otherwise False.
        """
        # The path to the tool must have been previously found.
        assert self._tool_path, ("First, the required MySQL tool must be "
                                 "found. E.g., use method "
                                 "search_my_print_defaults_tool.")

        # Create a temporary file to redirect stdout
        out_file = tempfile.TemporaryFile()
        if self._verbosity > 0:
            subprocess.call([self._tool_path, "--version"], stdout=out_file)
        else:
            # Redirect stderr to null
            null_file = open(os.devnull, "w+b")
            subprocess.call([self._tool_path, "--version"], stdout=out_file,
                            stderr=null_file)
        # Read --version output
        out_file.seek(0)
        line = out_file.readline()
        out_file.close()

        # Parse the version value
        match = re.search(r'(?:Ver )(\d)\.(\d)', line)
        if match:
            major, minor = match.groups()
            if (major_version < int(major)) or \
               (major_version == int(major) and minor_version <= int(minor)):
                return True
            else:
                return False
        else:
            raise UtilError("Unable to determine tool version - %s" %
                            self._tool_path)

    def check_login_path_support(self):
        """Checks if the used my_print_defaults tool supports login-paths.
        """
        # The path to the tool must have been previously found.
        assert self._tool_path, ("First, the required MySQL tool must be "
                                 "found. E.g., use method "
                                 "search_my_print_defaults_tool.")

        # Create a temporary file to redirect stdout
        out_file = tempfile.TemporaryFile()
        if self._verbosity > 0:
            subprocess.call([self._tool_path, "--help"], stdout=out_file)
        else:
            # Redirect stderr to null
            null_file = open(os.devnull, "w+b")
            subprocess.call([self._tool_path, "--help"], stdout=out_file,
                            stderr=null_file)
        # Read --help output
        out_file.seek(0)
        help_output = str(out_file.read())
        out_file.close()

        # Check the existence of a "login-path" option
        if 'login-path' in help_output:
            return True
        else:
            return False

    def _read_group_data(self, group):
        """Read group options data using my_print_defaults tool.
        """
        # The path to the tool must have been previously found.
        assert self._tool_path, ("First, the required MySQL tool must be "
                                 "found. E.g., use method "
                                 "search_my_print_defaults_tool.")

        # Group not found; use my_print_defaults to get group data.
        out_file = tempfile.TemporaryFile()
        if self._verbosity > 0:
            subprocess.call([self._tool_path, group], stdout=out_file)
        else:
            # Redirect stderr to null
            null_file = open(os.devnull, "w+b")
            subprocess.call([self._tool_path, group], stdout=out_file,
                            stderr=null_file)

        # Read and parse group options values.
        out_file.seek(0)
        results = []

        for line in out_file.readlines():
            line = line.decode('utf-8')
            # Parse option value; ignore starting "--"
            key_value = line[2:].split("=", 1)
            if len(key_value) == 2:
                # Handle option format: --key=value and --key=
                results.append((key_value[0], key_value[1].strip()))
            elif len(key_value) == 1:
                # Handle option format: --key
                results.append((key_value[0], True))
            else:
                raise UtilError("Invalid option value format for "
                                "group %s: %s" % (group, line))
        out_file.close()

        if len(results):
            self._config_data[group] = dict(results)
        else:
            self._config_data[group] = None

        return self._config_data[group]

    def get_group_data(self, group):
        """Retrieve the data associated to the given group.
        """
        # Returns group's data locally stored, if available.
        try:
            return self._config_data[group]
        except KeyError:
            # Otherwise, get it using my_print_defaults.
            return self._read_group_data(group)

    def get_option_value(self, group, opt_name):
        """Retrieve the value associated to the given opt_name in the group.
        """
        # Get option value, if group's data is available.
        grp_options = self.get_group_data(group)
        if grp_options:
            return grp_options.get(opt_name, None)
        else:
            return None
