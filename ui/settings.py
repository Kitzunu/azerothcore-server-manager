import sys
import os
import tkinter as tk
from tkinter import filedialog
from config.settings import SettingsManager

class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self.settings = SettingsManager()

    def open_settings_window(self):
        self.settings.load()
        s = self.settings # Short reference

        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")

        # Get the correct path to the icon
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "assets", "manager.ico")
        settings_win.iconbitmap(icon_path)

        def browse(entry):
            file_path = filedialog.askopenfilename()
            if file_path:
                entry.delete(0, tk.END)
                entry.insert(0, file_path)

        tk.Label(settings_win, text="Worldserver.exe path:", anchor="w", justify="left").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        world_entry = tk.Entry(settings_win, width=50)
        world_entry.insert(0, s.get('Paths', 'worldserver'))
        world_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(world_entry)).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Authserver.exe path:", anchor="w", justify="left").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        auth_entry = tk.Entry(settings_win, width=50)
        auth_entry.insert(0, s.get('Paths', 'authserver'))
        auth_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(auth_entry)).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Server.log path:", anchor="w", justify="left").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        world_log_entry = tk.Entry(settings_win, width=50)
        world_log_entry.insert(0, s.get('Paths', 'world_log_file'))
        world_log_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(world_log_entry)).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Auth.log path:", anchor="w", justify="left").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        auth_log_entry = tk.Entry(settings_win, width=50)
        auth_log_entry.insert(0, s.get('Paths', 'auth_log_file'))
        auth_log_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(auth_log_entry)).grid(row=3, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Restart Worldserver on crash: (1/0)", anchor="w", justify="left").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, s.getboolean('General', 'restart_worldserver_on_crash'))
        restart_var.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Host:", anchor="w", justify="left").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        database_host = tk.Entry(settings_win, width=50)
        database_host.insert(0, s.get('Database', 'database_host'))
        database_host.grid(row=5, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Port:", anchor="w", justify="left").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        database_port = tk.Entry(settings_win, width=50)
        database_port.insert(0, s.get('Database', 'database_port'))
        database_port.grid(row=6, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database User:", anchor="w", justify="left").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        database_user = tk.Entry(settings_win, width=50)
        database_user.insert(0, s.get('Database', 'database_user'))
        database_user.grid(row=7, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Password:", anchor="w", justify="left").grid(row=8, column=0, padx=5, pady=5, sticky="w")
        database_password = tk.Entry(settings_win, width=50)
        database_password.insert(0, s.get('Database', 'database_password'))
        database_password.grid(row=8, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database World:", anchor="w", justify="left").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        database_world = tk.Entry(settings_win, width=50)
        database_world.insert(0, s.get('Database', 'database_world'))
        database_world.grid(row=9, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Characters:", anchor="w", justify="left").grid(row=10, column=0, padx=5, pady=5, sticky="w")
        database_characters = tk.Entry(settings_win, width=50)
        database_characters.insert(0, s.get('Database', 'database_characters'))
        database_characters.grid(row=10, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Auth:", anchor="w", justify="left").grid(row=11, column=0, padx=5, pady=5, sticky="w")
        database_auth = tk.Entry(settings_win, width=50)
        database_auth.insert(0, s.get('Database', 'database_auth'))
        database_auth.grid(row=11, column=1, padx=5, pady=5)

        def save():
            s.WORLD_PATH = world_entry.get()
            s.AUTH_PATH = auth_entry.get()
            s.WORLD_LOG_FILE = world_log_entry.get()
            s.AUTH_LOG_FILE = auth_log_entry.get()
            s.RESTART_WORLDSERVER_ON_CRASH = restart_var.get()
            s.DATABASE_HOST = database_host.get()
            s.DATABASE_PORT = database_port.get()
            s.DATABASE_USER = database_user.get()
            s.DATABASE_PASSWORD = database_password.get()
            s.DATABASE_WORLD = database_world.get()
            s.DATABASE_CHARACTERS = database_characters.get()
            s.DATABASE_AUTH = database_auth.get()
            s.save_settings()
            settings_win.destroy()
            self.logger.manager("🔴 Settings saved.\n")

        tk.Button(settings_win, text="Save", command=save).grid(row=12, column=1, pady=10)
