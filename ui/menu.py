import tkinter as tk
import webbrowser
from ui.info import InfoWindow
from ui.settings import SettingsWindow

class Menu:
    def __init__(self, root):
        self.root = root
        self.infowindow = InfoWindow(self.root)
        self.settingswindow = SettingsWindow(self.root)

    def create_menu_bar(self, root):
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        # Add a "File" menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.settingswindow.open_settings_window)
        file_menu.add_command(label="Exit", command=root.destroy)

        # Add a "Help" menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Report a bug", command=lambda: webbrowser.open("https://github.com/Kitzunu/azerothcore-server-manager/issues"))
        help_menu.add_command(label="Join Discord", command=lambda: webbrowser.open("https://discord.com/invite/UE6NkHfC"))
        help_menu.add_command(label="About", command=self.infowindow.open_info_window)