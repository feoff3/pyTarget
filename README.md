# pyTarget
iSCSI target for Python 2.7

This is a fork of original pyTarget project from SourceForge
https://sourceforge.net/projects/pytarget/


## Additional features compared to original:
- Ability to use physical disks as data source
- Ability to auto-detect and grow disk capacity
- Ability to use volumes (with emulated GPT) as data source
- 2TB+ disks support
- Customize disk physical and logical sector size

## Prerequisites
- Python 2.7.10

### Windows only
- Install `pywin32` module by running cmd.exe as admin and typing `C:\Python27\python -m pip install pywin32`
- To access physical disks and volumes, pyTarget must be run as admin

#### Connect to a local physical disk
1. Open cmd.exe as admin, start iscsi initiator by running 
- `sc config msiscsi start= auto`
- `net start msiscsi`
2. Get iscsi intiator address e.g. `iqn.1991-05.com.microsoft:vlad-test-2019` by:
- `echo iqn | iscsicli | findstr [iqn`
3. Locate physical disk size in bytes and path in form of `\\.\PhysicalDriveX` with `wmic diskdrive get Manufacturer, DeviceId, Model, Index, Size`
4. Open `pytarget/src/config.xml` and insert the following line inside of `<target>` tag:
- `<host name="IQN" target_pwd="" initiator_pwd="> <lun id="0" type="0" path="\\.\PhysicalDrive2" capacity="6442450944" media="0x1000" lsector="512" psector="4096"/> </host>`
- replace `IQN` in `name` attribute with with one you got from step earlier
- replace `\\.\PhysicalDrive2` in `path` with windows drive path
- for fixed capacity, replace `capacity` value with size in sectors, for that divide size in bytes by 512; for dynamic capacity set the value to "0" for auto-detect and auto-expand
- fix 'psector' value if you want to override physical sector size reported by iscsi target

Example, in case we want to use disk #3:
```
C:\Users\feoff\Desktop\pytarget>echo iqn | iscsicli | findstr [iqn
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit

C:\Users\feoff\Desktop\pytarget>wmic diskdrive get Manufacturer, DeviceId, Model, Index, Size
DeviceID            Index  Manufacturer            Model                   Size
\\.\PHYSICALDRIVE0  0      (Standard disk drives)  Microsoft Virtual Disk  136366917120
\\.\PHYSICALDRIVE1  1      (Standard disk drives)  Microsoft Virtual Disk  7509680640
\\.\PHYSICALDRIVE2  2      (Standard disk drives)  Microsoft Virtual Disk  4293596160
\\.\PHYSICALDRIVE3  3      (Standard disk drives)  Microsoft Virtual Disk  34356994560
```

Then the corresponding entry in config.xml will look like
```
...
    <target name="iqn.2006-11.1.python.iscsi.target-1" ip="127.0.0.1" port="3260" portal="1">
    
    <host name="iqn.1991-05.com.microsoft:vlad-test-2019" target_pwd="" initiator_pwd=""> <lun id="0" type="0" path="\\.\PHYSICALDRIVE3" capacity="67103505" media="0x1000"/> </host>
 
...
```

5. Start the target:
- Open `cmd.exe` and navigate to pytarget folder, `src` subfolder
- `C:\Python27\python.exe pyTarget.py`
6. Start iscsi intiator to connect to target, from new cmd.exe console (change `127.0.0.1` to target IP address if it is installed on other PC in the network):
- `iscsicli QAddTargetPortal 127.0.0.1`
- `iscsicli qlogintarget iqn.2006-11.1.python.iscsi.target-1`
- Check the disk is connected by `iscsicli reporttargetmappings`

7. To end the session (and disconnect the disk):
- `iscsicli logouttarget <session-id>`, where <session-id>  is reported by `iscsicli reporttargetmappings`, e.g. `iscsicli logouttarget fffffa800626e018-4000013700000006`

#### Connect to a local volume
1. Open cmd.exe as admin, start iscsi initiator by running 
- `sc config msiscsi start= auto`
- `net start msiscsi`
2. Get iscsi intiator address e.g. `iqn.1991-05.com.microsoft:vlad-test-2019` by:
- `echo iqn | iscsicli | findstr [iqn`
3. Locate basic or dynamic volume guid path `\\?\Volume{GUID}` as returned by `mountvol X: /L`, replace X: with the target volume letter
4. Open `pytarget/src/config.xml` and insert the following line inside of `<target>` tag:
- `<host name="IQN" target_pwd="" initiator_pwd="> <lun id="0" type="0" path="\\?\Volume{GUID}" capacity="6442450944" media="0x2000" lsector="512" psector="4096"/> </host>`
- replace `IQN` in `name` attribute with with one you got from step earlier
- replace `\\?\Volume{GUID}` in `path` with volume guid path (no trailing slash)
- for fixed capacity, replace `capacity` value with size in sectors, for that divide size in bytes by 512; for dynamic capacity set the value to "0" for auto-detect and auto-expand
- fix 'psector' value if you want to override physical sector size reported by iscsi target

Example, in case we want to use volume F:
```
C:\Users\feoff\Desktop\pytarget>echo iqn | iscsicli | findstr [iqn
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit

C:\Users\feoff\Desktop\pytarget>mountvol F:\ /L
    \\?\Volume{9bb6d08d-6370-11ee-a534-6045bdad03c5}\
```

Then the corresponding entry in config.xml will look like
```
...
    <target name="iqn.2006-11.1.python.iscsi.target-1" ip="127.0.0.1" port="3260" portal="1">
    
    <host name="iqn.1991-05.com.microsoft:vlad-test-2019" target_pwd="" initiator_pwd=""> <lun id="0" type="0" path="\\?\Volume{9bb6d08d-6370-11ee-a534-6045bdad03c5}" capacity="0" media="0x2000"/> </host>
 
...
```

5. Start the target:
- Open `cmd.exe` and navigate to pytarget folder, `src` subfolder
- `C:\Python27\python.exe pyTarget.py`
6. Start iscsi intiator to connect to target, from new cmd.exe console (change `127.0.0.1` to target IP address if it is installed on other PC in the network):
- `iscsicli QAddTargetPortal 127.0.0.1`
- `iscsicli qlogintarget iqn.2006-11.1.python.iscsi.target-1`
- Check the disk is connected by `iscsicli reporttargetmappings`
7. To end the session (and disconnect the disk):
- `iscsicli logouttarget <session-id>`, where <session-id>  is reported by `iscsicli reporttargetmappings`, e.g. `iscsicli logouttarget fffffa800626e018-4000013700000006`


#### Connect to a local volume, emulate GPT layout
1. Open cmd.exe as admin, start iscsi initiator by running 
- `sc config msiscsi start= auto`
- `net start msiscsi`
2. Get iscsi intiator address e.g. `iqn.1991-05.com.microsoft:vlad-test-2019` by:
- `echo iqn | iscsicli | findstr [iqn`
3. Generate footer and header file, 32MB size: `fsutil file createnew C:\footer 33554432`, `fsutil file createnew C:\header 33554432`
4. Locate basic or dynamic volume guid path `\\?\Volume{GUID}` as returned by `mountvol X: /L`, replace X: with the target volume letter
5. Open `pytarget/src/config.xml` and insert the following line inside of `<target>` tag:
- `<host name="IQN" target_pwd="" initiator_pwd="> <lun id="0" type="0" path="\\?\Volume{GUID}" capacity="6442450944" media="0x4000" lsector="512" psector="4096" parms="C:\header;C:\footer"/> </host>`
- replace `IQN` in `name` attribute with with one you got from step earlier
- replace `\\?\Volume{GUID}` in `path` with volume guid path (no trailing slash)
- for fixed capacity, replace `capacity` value with size in sectors, for that divide size in bytes by 512; for dynamic capacity set the value to "0" for auto-detect and auto-expand
- fix 'psector' value if you want to override physical sector size reported by iscsi target
- in 'parms' field two preallocated files must be specified: one that will have starting sectors of emulated GPT, and one that will have the ending sectors of emulated GPT

Example, in case we want to use volume F:
```
C:\Users\feoff\Desktop\pytarget>echo iqn | iscsicli | findstr [iqn
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit
[iqn.1991-05.com.microsoft:vlad-test-2019] Enter command or ^C to exit

C:\Users\feoff\Desktop>fsutil file createnew C:\header 33554432
File C:\header is created

C:\Users\feoff\Desktop>fsutil file createnew C:\footer 33554432
File C:\footer is created

C:\Users\feoff\Desktop\pytarget>mountvol F:\ /L
    \\?\Volume{9bb6d08d-6370-11ee-a534-6045bdad03c5}\

```

Then the corresponding entry in config.xml will look like
```
...
    <target name="iqn.2006-11.1.python.iscsi.target-1" ip="127.0.0.1" port="3260" portal="1">
    
    <host name="iqn.1991-05.com.microsoft:vlad-test-2019" target_pwd="" initiator_pwd=""> <lun id="0" type="0" path="\\?\Volume{9bb6d08d-6370-11ee-a534-6045bdad03c5}" capacity="0" media="0x4000" parms="C:\header;C:\footer" psector="4096"/> </host>
 
...
```

5. (Optionally) If some of the apps are using the source volume
- TODO: describe how to change the mount points 
- Restart
- TODO: describe how to add the target to autostart (maybe to service with early loading group)

6. Start the target:
- Open `cmd.exe` and navigate to pytarget folder, `src` subfolder
- `C:\Python27\python.exe pyTarget.py`
- Read 'main dev size: ' value in console (it will show the size of partition to create in bytes)

8. Start iscsi intiator to connect to target, from new cmd.exe console (change `127.0.0.1` to target IP address if it is installed on other PC in the network):
- `iscsicli QAddTargetPortal 127.0.0.1`
- `iscsicli qlogintarget iqn.2006-11.1.python.iscsi.target-1`
- Check the disk is connected by `iscsicli reporttargetmappings`

9. initialize the connected disk with GPT data:
- Download (gdisk)[https://sourceforge.net/projects/gptfdisk/] 
- run gdisk\gdisk64, for disk number that is connected by iscsi
- type 'n' to create new partition
- specify '32M' for partition offset
- Divide "main dev size value" by 1024 to get value in KB, specify it for partition size like '+NNNK' , e.g. '+8351744K'
- for other partition parameters use defaults
- type 'w' to write partition table to disk
- After that a partition with data from original volume should appear
10. To end the session (and disconnect the disk):
- `iscsicli logouttarget <session-id>`, where <session-id>  is reported by `iscsicli reporttargetmappings`, e.g. `iscsicli logouttarget fffffa800626e018-4000013700000006`

