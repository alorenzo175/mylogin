import os
import re
import shutil
import sys


try:
    from setuptools import setup, Command
except ImportError:
    raise RuntimeError('setuptools is required')

def read_file(*paths):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, *paths)) as f:
        return f.read()

PACKAGE = 'mylogin'

if sys.version_info[:2] < (2, 7):
    sys.exit('%s requires Python 2.7 or higher.' % PACKAGE)

SHORT_DESC = 'MyLogin package for reading .mylogin.cnf files'
VERSIONFILE= PACKAGE+"/_version.py"
AUTHOR = "Tony Lorenzo"
AUTHOR_EMAIL = "alorenzo175@users.noreply.github.com"
URL = 'https://github.com/alorenzo175/mylogin'
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    VERSION = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))



setup(
    name=PACKAGE,
    version=VERSION,
    description=SHORT_DESC,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=[PACKAGE],
    zip_safe=False)
