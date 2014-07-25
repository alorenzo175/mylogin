# Copyright (c) 2014 Tony Lorenzo
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
A simple module that can get login information from a .mylogin.cnf file made
by `mysql_config_editor`
"""
import mylogin.ip_parser as ip_parser

def get_login_info(login_path, host=None, port=None, socket=None):
    """ Get the user and password from a .mylogin.cnf file """
    host = host or u'localhost'
    port = port or 3306
    if socket is not None:
        info_dict = ip_parser.parse_connection('{lp}:{sock}'.format(
            lp=login_path, sock=socket))
    else:
        info_dict = ip_parser.parse_connection('{lp}:{host}:{port}'.format(
            lp=login_path, host=host, port=port))

    return info_dict
