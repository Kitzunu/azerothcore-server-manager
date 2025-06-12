# ![icon](icon.png) AzerothCore Server Manager

![manager-home](assets/manager-home.png)

## Installation

**Requirements:**
- Windows
- Python 3.0

**Compile:**
1. `python -m pip install pyinstaller`
2. `python -m pip install psutil`
3. `python -m pip install mysql-connector-python`
4. `python -m PyInstaller --onefile --windowed --icon=assets/manager.ico --add-data "assets;assets" manager.py`
5. Find it in `D:\azerothcore-server-manager\dist`

## Features

- Start/Stop your servers
- Worldserver auto restart on crash
- Restart the Worldserver safely
- Send commands to the WorldServer console directly
- Show player online count, gm online count
- Show open tickets count

![manager-command](assets/manager-command.png)

## Credit

- Kitzunu
- ChatGPT