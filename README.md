# pyTarget
iSCSI target for Python 2.7

This is a fork of original pyTarget project from SourceForge
https://sourceforge.net/projects/pytarget/


## Additional features compared to original:
- Ability to use physical disks as data source
- Ability to use volumes (with emulated GPT) as data source

## Prerequisites
- Python 2.7.10

### Windows only
- Install `pywin32` module, e.g. `C:\Python27\python -m pip install pywin32`
- To access physical disks and volumes, pyTarget must be run as admin