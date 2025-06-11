# ![icon](assets/manager.png) AzerothCore Server Manager

## Features
![manager-home](assets/manager-home.png)

- Start/Stop your servers
- Keep 
- Worldserver auto restart on crash
- Restart the Worldserver safely
- Send commands to the WorldServer console directly

![manager-command](assets/manager-command.png)

## Compile

**Requirements:**
- Python 3.0

**Installation:**
1. `python -m pip install pyinstaller`
2. `python -m pip install psutil`
3. `python -m PyInstaller --onefile --windowed --icon=assets/manager.ico --add-data "assets;assets" manager.py`
4. Find it in `D:\azerothcore-server-manager\dist`