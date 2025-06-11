# ![icon](icon.png) AzerothCore Server Manager

## Installation

**Requirements:**
- Windows
- Python 3.0

**Compile:**
1. `python -m pip install pyinstaller`
2. `python -m pip install psutil`
3. `python -m PyInstaller --onefile --windowed --icon=assets/manager.ico --add-data "assets;assets" manager.py`
4. Find it in `D:\azerothcore-server-manager\dist`

## Features
![manager-home](assets/manager-home.png)

- Start/Stop your servers
- Keep 
- Worldserver auto restart on crash
- Restart the Worldserver safely
- Send commands to the WorldServer console directly

![manager-command](assets/manager-command.png)
