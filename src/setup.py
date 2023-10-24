# setup.py

from comm.version import *
from distutils.core import setup
import py2exe, os,  shutil

options = { "py2exe": { "compressed": 1,
                        "optimize": 2,
                        "bundle_files": 1,
                        # "skip_archive":1,
                        "dll_excludes": ["MSVCP90.dll"]}  
          }

config_file = ['config.xml', 'Readme.pdf', 'web\help.htm']

setup( name = MY_NAME,
       version = MY_VERSION,
       description = MY_DESCRIPTION,
       options = options,
       zipfile = None,
       data_files = config_file,
       console=[{"script": "pyTarget.py", "icon_resources": [(1, "pyTarget.ico")]}],
    )

for file in os.listdir('dependancy'):
    if not file.startswith('.'):
        shutil.copy(os.path.join('dependancy', file),
            os.path.join('dist', 'lib'))
        shutil.copy(os.path.join('dependancy', file), 'dist')