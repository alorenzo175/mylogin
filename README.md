MyLogin
=======

This simple module is meant to easily get MySQL login information
from .mylogin.cnf files created using `mysql_config_editor`. 
It has been tested with Python 2.7.6 and 3.4.

This module is released under the GNU GPL v2 license
integrating modules from the 
[MySQL Utilities](http://dev.mysql.com/doc/mysql-utilities/1.4/en/index.html)
package.

To use, import the `mylogin` module and call it's `get_login_info` function.
The function requires a `login_path` arguement. `host`, `port`, and `socket`
arguments are optional and will default to the default MySQL values if not given.

```python
	
	import mylogin
	
	mylogin.get_login_info('myuser', host='localhost', port=3306)


```