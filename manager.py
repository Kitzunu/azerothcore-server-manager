import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import subprocess
import os
import threading
import time
import configparser
import winsound
import datetime
import webbrowser
import psutil
import mysql.connector
from mysql.connector import Error
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Compile
# python -m PyInstaller --onefile --windowed --icon=assets/manager.ico --add-data "assets;assets" manager.py

SETTINGS_FILE = "settings.ini"

class AzerothManager:
    def __init__(self, root):
        self.root = root
        self.root.title("AzerothCore Server Manager")

        # Get the correct path to the icon
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "assets", "manager.ico")
        self.root.iconbitmap(icon_path)

        self.config = configparser.ConfigParser()
        self.load_settings()

        self.auth_process = None
        self.world_process = None
        self.auth_log_thread = None
        self.world_log_thread = None
        self.stop_log = threading.Event()

        self.create_menu_bar(root)
        self.create_widgets()
        self.header()
        self.update_status()
        self.test_connect_mysql()

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            self.config['Paths'] = {
                'worldserver': r'D:\build\bin\RelWithDebInfo\worldserver.exe',
                'authserver': r'D:\build\bin\RelWithDebInfo\authserver.exe',
                'world_log_file': r'D:\build\bin\RelWithDebInfo\Server.log',
                'auth_log_file': r'D:\build\bin\RelWithDebInfo\Auth.log',
            }
            self.config['General'] = {
                'restart_worldserver_on_crash': True,
            }
            self.config['Database'] = {
                'database_host': '127.0.0.1',
                'database_port': '3306',
                'database_user': 'acore',
                'database_password': 'acore',
                'database_world': 'acore_world',
                'database_characters': 'acore_characters',
                'database_auth': 'acore_auth',
            }
            with open(SETTINGS_FILE, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(SETTINGS_FILE)

        self.WORLD_PATH = self.config['Paths']['worldserver']
        self.AUTH_PATH = self.config['Paths']['authserver']
        self.WORLD_LOG_FILE = self.config['Paths']['world_log_file']
        self.AUTH_LOG_FILE = self.config['Paths']['auth_log_file']
        self.RESTART_WORLDSERVER_ON_CRASH = self.config.getboolean('General', 'restart_worldserver_on_crash')
        self.DATABASE_HOST = self.config['Database']['database_host']
        self.DATABASE_PORT = self.config['Database']['database_port']
        self.DATABASE_USER = self.config['Database']['database_user']
        self.DATABASE_PASSWORD = self.config['Database']['database_password']
        self.DATABASE_WORLD = self.config['Database']['database_world']
        self.DATABASE_CHARACTERS = self.config['Database']['database_characters']
        self.DATABASE_AUTH = self.config['Database']['database_auth']

    def save_settings(self):
        self.config['Paths']['worldserver'] = self.WORLD_PATH
        self.config['Paths']['authserver'] = self.AUTH_PATH
        self.config['Paths']['world_log_file'] = self.WORLD_LOG_FILE
        self.config['Paths']['auth_log_file'] = self.AUTH_LOG_FILE
        self.config['General']['restart_worldserver_on_crash'] = self.RESTART_WORLDSERVER_ON_CRASH
        self.config['Database']['database_host'] = self.DATABASE_HOST
        self.config['Database']['database_port'] = self.DATABASE_PORT
        self.config['Database']['database_user'] = self.DATABASE_USER
        self.config['Database']['database_password'] = self.DATABASE_PASSWORD
        self.config['Database']['database_world'] = self.DATABASE_WORLD
        self.config['Database']['database_characters'] = self.DATABASE_CHARACTERS
        self.config['Database']['database_auth'] = self.DATABASE_AUTH
        with open(SETTINGS_FILE, 'w') as configfile:
            self.config.write(configfile)

    def test_connect_mysql(self):
        try:
            connection = mysql.connector.connect(
                host = self.DATABASE_HOST,
                port = self.DATABASE_PORT,
                user = self.DATABASE_USER,
                password = self.DATABASE_PASSWORD,
                database = self.DATABASE_CHARACTERS,
            )
            if connection.is_connected():
                self.log_manager("🔴 MySQL test connection successful for DB: Characters.\n")
                return connection
        except Error as e:
            self.log_manager(f"❗ MySQL connection failed: {e}\n")
            return None

    def create_menu_bar(self, root):
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        # Add a "File" menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.open_settings_window)
        file_menu.add_command(label="Exit", command=root.destroy)

        # Add a "Help" menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Report a bug", command=lambda: webbrowser.open("https://github.com/Kitzunu/azerothcore-server-manager/issues"))
        help_menu.add_command(label="Join Discord", command=lambda: webbrowser.open("https://discord.com/invite/UE6NkHfC"))

    def create_widgets(self):
        worldserver_button_frame = tk.Frame(self.root)
        worldserver_button_frame.pack(pady=5, fill='x')

        self.world_status_lbl = tk.Label(worldserver_button_frame, text="Worldserver: Unknown", fg="gray")
        self.world_status_lbl.pack(side="left", padx=5)

        self.w_start_btn = tk.Button(worldserver_button_frame, text="Start Server", command=self.start_worldserver, width=15)
        self.w_stop_btn = tk.Button(worldserver_button_frame, text="Stop Server", command=self.stop_worldserver, width=15)
        self.w_kill_btn = tk.Button(worldserver_button_frame, text="Kill Server", command=self.kill_workdserver, width=15)
        self.w_restart_btn = tk.Button(worldserver_button_frame, text="Restart Server", command=self.restart_worldserver, width=15)

        self.w_start_btn.pack(side=tk.LEFT, padx=5)
        self.w_stop_btn.pack(side=tk.LEFT, padx=5)
        self.w_kill_btn.pack(side=tk.LEFT, padx=5)
        self.w_restart_btn.pack(side=tk.LEFT, padx=5)

        # Authserver Buttons
        authserver_button_frame = tk.Frame(self.root)
        authserver_button_frame.pack(pady=5, fill='x')

        self.auth_status_lbl = tk.Label(authserver_button_frame, text="Authserver: Unknown", fg="gray")
        self.auth_status_lbl.pack(side="left", padx=5)

        self.a_start_btn = tk.Button(authserver_button_frame, text="Start Server", command=self.start_authserver, width=15)
        self.a_stop_btn = tk.Button(authserver_button_frame, text="Kill Server", command=self.kill_authserver, width=15)

        self.a_start_btn.pack(side=tk.LEFT, padx=5)
        self.a_stop_btn.pack(side=tk.LEFT, padx=5)

        # Server Stats
        serverstats_button_frame = tk.Frame(self.root)
        serverstats_button_frame.pack(pady=5, fill='x')

        self.serverstats_lbl = tk.Label(serverstats_button_frame, text="Server Stats:", fg="black")
        self.serverstats_lbl.pack(side="left", padx=5)

        self.serverstats_onlineplayers_lbl = tk.Label(serverstats_button_frame, text="Online Players: Unknown", fg="grey")
        self.serverstats_onlineplayers_lbl.pack(side="left", padx=5)

        self.serverstats_onlinegms_lbl = tk.Label(serverstats_button_frame, text="Online GMs: Unknown", fg="grey")
        self.serverstats_onlinegms_lbl.pack(side="left", padx=5)

        self.serverstats_open_tickets_lbl = tk.Label(serverstats_button_frame, text="Open Tickets: Unknown", fg="grey")
        self.serverstats_open_tickets_lbl.pack(side="left", padx=5)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_height = 20

        # Manager log tab
        self.manager_log = scrolledtext.ScrolledText(self.notebook, width=80, height=self.tab_height, state='disabled')
        self.notebook.add(self.manager_log, text="Manager Log")
        self.manager_tab_index = self.notebook.index(self.manager_log)

        # Authserver log tab
        self.auth_log = scrolledtext.ScrolledText(self.notebook, width=80, height=self.tab_height, state='disabled')
        self.notebook.add(self.auth_log, text="Authserver Log")

        # Worldserver log tab
        self.world_log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.world_log_frame, text="Worldserver Console")

        # Worldserver log tab Frame to hold the text and scrollbar
        self.world_log_text_frame = tk.Frame(self.world_log_frame)
        self.world_log_text_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        # Worldserver log tab Scrollbar
        self.world_scrollbar = tk.Scrollbar(self.world_log_text_frame)
        self.world_scrollbar.pack(side="right", fill="y")

        # Worldserver log tab World log output (Text widget)
        self.world_log_output = tk.Text(
            self.world_log_text_frame,
            wrap="word",
            height=self.tab_height,
            yscrollcommand=self.world_scrollbar.set
        )
        self.world_log_output.pack(side="left", fill="both", expand=True)
        
        # Worldserver log tab Connect scrollbar to text widget
        self.world_scrollbar.config(command=self.world_log_output.yview)

        # Worldserver log tab Frame for input + button
        self.world_input_frame = tk.Frame(self.world_log_frame)
        self.world_input_frame.pack(fill="x", padx=5, pady=5)

        # Worldserver log tab Input entry
        self.world_input = tk.Entry(self.world_input_frame)
        self.world_input.pack(side="left", fill="x", expand=True)

        placeholder = "Type a command here!"
        self.world_input.insert(0, placeholder)
        self.world_input.config(fg='grey')

        # Worldserver log tab Define focus-in and focus-out behavior
        def on_focus_in(event):
            if self.world_input.get() == placeholder:
                self.world_input.delete(0, tk.END)
                self.world_input.config(fg='black')

        def on_focus_out(event):
            if not self.world_input.get():
                self.world_input.insert(0, placeholder)
                self.world_input.config(fg='grey')

        self.world_input.bind("<FocusIn>", on_focus_in)
        self.world_input.bind("<FocusOut>", on_focus_out)

        # Worldserver log tab Send button
        self.world_send_button = tk.Button(self.world_input_frame, text="Send", command=self.send_world_input)
        self.world_send_button.pack(side="left", padx=(5, 0))
        self.world_input.bind("<Return>", lambda event: self.send_world_input())

        # Statistics tab 
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Server Stats")
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = event.widget.tab("current")["text"]
        if selected_tab == "Server Stats":
            self.show_faction_pie_chart()

    def send_world_input(self):
        command = self.world_input.get().strip()
        world_running = self.check_process("worldserver.exe")
        if command and world_running:
            try:
                self.world_process.stdin.write(command + '\n')
                self.world_process.stdin.flush()
                self.world_log_output.insert("end", f"> {command}\n")
                self.world_log_output.see("end")
                self.world_input.delete(0, 'end')
            except Exception as e:
                self.log_world(f"❗ Failed to send command: {e}\n")
        else:
            self.log_world(f"❗ Failed to send command: {e}\nWorldserver is not running or stdin is unavailable.\n")

    def header(self):
        self.log_manager("\n")
        self.log_manager("   █████╗ ███████╗███████╗██████╗  ██████╗ ████████╗██╗  ██╗\n")
        self.log_manager("  ██╔══██╗╚══███╔╝██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║  ██║\n")
        self.log_manager("  ███████║  ███╔╝ █████╗  ██████╔╝██║   ██║   ██║   ███████║\n")
        self.log_manager("  ██╔══██║ ███╔╝  ██╔══╝  ██╔══██╗██║   ██║   ██║   ██╔══██║\n")
        self.log_manager("  ██║  ██║███████╗███████╗██║  ██║╚██████╔╝   ██║   ██║  ██║\n")
        self.log_manager("  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝\n")
        self.log_manager("                                   ██████╗ ██████╗ ██████╗ ███████╗\n")
        self.log_manager("                                  ██╔════╝██╔═══██╗██╔══██╗██╔════╝\n")
        self.log_manager("                                  ██║     ██║   ██║██████╔╝█████╗\n")
        self.log_manager("                                  ██║     ██║   ██║██╔══██╗██╔══╝\n")
        self.log_manager("                                  ╚██████╗╚██████╔╝██║  ██║███████╗\n")
        self.log_manager("                                   ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝\n\n")
        self.log_manager("     https://github.com/Kitzunu/azerothcore-server-manager/\n\n")
        self.log_manager("❗ Make sure to configure the SETTINGS before running the servers. ❗\n\n")
        self.log_manager(f"> Worldserver.exe path:         {self.WORLD_PATH}\n")
        self.log_manager(f"> Authserver.exe path:          {self.AUTH_PATH}\n")
        self.log_manager(f"> Server.log path:              {self.WORLD_LOG_FILE}\n")
        self.log_manager(f"> Auth.log path:                {self.AUTH_LOG_FILE}\n")
        self.log_manager(f"> Restart Worldserver on crash: {self.RESTART_WORLDSERVER_ON_CRASH}\n")

    def log_manager(self, text):
        self._append_text(self.manager_log, text)

    def log_auth(self, text):
        self._append_text(self.auth_log, text)

    def log_world(self, text):
        self._append_text(self.world_log_output, text)

    def _append_text(self, widget, text):
        widget.config(state='normal')
        widget.insert(tk.END, text)
        widget.config(state='disabled')
        widget.see(tk.END)

    def open_settings_window(self):
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
        world_entry.insert(0, self.WORLD_PATH)
        world_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(world_entry)).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Authserver.exe path:", anchor="w", justify="left").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        auth_entry = tk.Entry(settings_win, width=50)
        auth_entry.insert(0, self.AUTH_PATH)
        auth_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(auth_entry)).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Server.log path:", anchor="w", justify="left").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        world_log_entry = tk.Entry(settings_win, width=50)
        world_log_entry.insert(0, self.WORLD_LOG_FILE)
        world_log_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(world_log_entry)).grid(row=2, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Auth.log path:", anchor="w", justify="left").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        auth_log_entry = tk.Entry(settings_win, width=50)
        auth_log_entry.insert(0, self.AUTH_LOG_FILE)
        auth_log_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Button(settings_win, text="Browse", command=lambda: browse(auth_log_entry)).grid(row=3, column=2, padx=5, pady=5)

        tk.Label(settings_win, text="Restart Worldserver on crash: (1/0)", anchor="w", justify="left").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.RESTART_WORLDSERVER_ON_CRASH)
        restart_var.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Host:", anchor="w", justify="left").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_HOST)
        restart_var.grid(row=5, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Port:", anchor="w", justify="left").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_PORT)
        restart_var.grid(row=6, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database User:", anchor="w", justify="left").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_USER)
        restart_var.grid(row=7, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Password:", anchor="w", justify="left").grid(row=8, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_PASSWORD)
        restart_var.grid(row=8, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database World:", anchor="w", justify="left").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_WORLD)
        restart_var.grid(row=9, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Characters:", anchor="w", justify="left").grid(row=10, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_CHARACTERS)
        restart_var.grid(row=10, column=1, padx=5, pady=5)

        tk.Label(settings_win, text="Database Auth:", anchor="w", justify="left").grid(row=11, column=0, padx=5, pady=5, sticky="w")
        restart_var = tk.Entry(settings_win, width=50)
        restart_var.insert(0, self.DATABASE_AUTH)
        restart_var.grid(row=11, column=1, padx=5, pady=5)

        def save():
            self.WORLD_PATH = world_entry.get()
            self.AUTH_PATH = auth_entry.get()
            self.WORLD_LOG_FILE = world_log_entry.get()
            self.AUTH_LOG_FILE = auth_log_entry.get()
            self.RESTART_WORLDSERVER_ON_CRASH = restart_var.get()
            self.save_settings()
            settings_win.destroy()
            self.log_manager("🔴 Settings saved.\n")

        tk.Button(settings_win, text="Save", command=save).grid(row=12, column=1, pady=10)

    def start_authserver(self):
        world_running = self.check_process("authserver.exe")
        if world_running:
            self.log_manager("❗ Authserver are already running.\n")
            return

        try:
            # --- Start authserver ---
            self.auth_process = subprocess.Popen(
                [self.AUTH_PATH],
                cwd=os.path.dirname(self.AUTH_PATH),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            )

            # Start threads to read authserver stdout/stderr
            threading.Thread(
                target=self.read_stream,
                args=(self.auth_process.stdout, self.log_auth),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_stream,
                args=(self.auth_process.stderr, self.log_auth),
                daemon=True
            ).start()

            self.auth_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.AUTH_LOG_FILE, self.log_auth),
                daemon=True
            )
            self.auth_log_thread.start()

            self.update_status()
            self.log_manager("🔴 Authserver started.\n")

        except Exception as e:
            self.log_manager(f"❗ Error starting Authserver: {e}\n")

    def start_worldserver(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            self.log_manager("❗ Worldserver are already running.\n")
            return

        try:
            # --- Start worldserver ---
            self.world_process = subprocess.Popen(
                [self.WORLD_PATH],
                cwd=os.path.dirname(self.WORLD_PATH),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            )

            # Start threads to read worldserver stdout/stderr
            threading.Thread(
                target=self.read_stream,
                args=(self.world_process.stdout, self.log_world),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_stream,
                args=(self.world_process.stderr, self.log_world),
                daemon=True
            ).start()

            self.stop_log.clear()
            self.world_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.WORLD_LOG_FILE, self.log_world),
                daemon=True
            )
            self.world_log_thread.start()

            threading.Thread(target=self.monitor_worldserver, daemon=True).start()

            self.update_status()
            self.update_online_players()
            self.update_online_gms()
            self.update_open_tickets()
            self.show_faction_pie_chart()
            self.log_manager("🔴 Worldserver started.\n")

        except Exception as e:
            self.log_manager(f"❗ Error starting Worldserver: {e}\n")

    def read_stream(self, stream, log_function):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    log_function(line)
        except Exception as e:
            self.log_manager(f"❗ Error reading server output: {e}\n")

    def tail_log_file(self, filepath, log_function):
        try:
            if not os.path.exists(filepath):
                self.log_manager(f"❗ Log file not found: {filepath}\n")
                return

            last_size = 0
            while not self.stop_log.is_set():
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        # Seek to last known position or EOF if new file
                        f.seek(last_size)
                        while not self.stop_log.is_set():
                            line = f.readline()
                            if line:
                                log_function(line)
                                last_size = f.tell()
                            else:
                                time.sleep(0.1)
                                # Check if file size changed externally (file rotated?)
                                current_size = os.path.getsize(filepath)
                                if current_size < last_size:
                                    # File truncated, reset position
                                    last_size = 0
                                    break  # break inner loop to reopen file
                except Exception as e:
                    self.log_manager(f"❗ Error reading log {filepath}: {e}\n")
                    time.sleep(1)

        except Exception as e:
            self.log_manager(f"❗ General error tailing log file {filepath}: {e}\n")

    def kill_authserver(self):
        if self.auth_process:
            self.auth_process.terminate()
            self.auth_process = None
        
        self.log_manager("🔴 Authserver killed.\n")
        self.update_status()

    def stop_worldserver(self):
        self.stop_log.set()

        if self.world_process:
            self.world_process.stdin.write("server exit" + '\n')
            self.world_process.stdin.flush()
            self.world_process = None

        self.log_manager("🔴 Worldserver stopped.\n")
        self.update_status()

    def kill_workdserver(self):
        if self.world_process:
            self.world_process.terminate()
            self.world_process = None
        
        self.log_manager("🔴 Worldserver killed.\n")
        self.update_status()

    def restart_worldserver(self):
        world_running = self.check_process("worldserver.exe")
       
        # Create popup window
        restart_popup = tk.Toplevel(self.root)
        restart_popup.title("Restart Server")

        # Get the correct path to the icon
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "assets", "manager.ico")
        restart_popup.iconbitmap(icon_path)

        if not world_running:
            tk.Label(restart_popup, text="❗ ERROR: Worldserver is offline.", fg="red", font=("Arial", 8)).grid(row=0, column=0, columnspan=2)
        else:
            tk.Label(restart_popup, text="Delay:").grid(row=0, column=0, padx=5, pady=5)
            delay_entry = tk.Entry(restart_popup)
            delay_entry.grid(row=0, column=1, padx=5, pady=5)
            tk.Label(restart_popup, text="#delay: use a timestring like \"1h15m30s\".", fg="gray", font=("Arial", 8)).grid(row=1, column=0, columnspan=2)

            tk.Label(restart_popup, text="Exit Code:").grid(row=2, column=0, padx=5, pady=5)
            exitcode_entry = tk.Entry(restart_popup)
            exitcode_entry.grid(row=2, column=1, padx=5, pady=5)
            exitcode_entry.insert(0, "2")
            tk.Label(restart_popup, text="If you use custom exitcodes you can change it.\n0 = Shutdown\n1 = Crash/Error\n2 = Restart", fg="gray", font=("Arial", 8)).grid(row=3, column=0, columnspan=2)

            self.delay_str = ""
            def submit():
                delay = delay_entry.get()
                exit_code = exitcode_entry.get()
                if delay and exit_code:
                    cmd = f"server restart {delay} {exit_code}\n"
                    self.world_process.stdin.write(cmd)
                    self.world_process.stdin.flush()
                    self.delay_str = delay
                    restart_popup.destroy()
                else:
                    tk.messagebox.showwarning("Input error", "Please fill both fields")

            submit_btn = tk.Button(restart_popup, text="Submit", command=submit)
            submit_btn.grid(row=4, column=0, columnspan=2, pady=10)

            restart_popup.grab_set()
            self.root.wait_window(restart_popup)
            self.log_manager(f"🔴 Worldserver will restart in {self.delay_str}...\n")

    def monitor_worldserver(self):
        exit_code = self.world_process.wait()
        self.log_manager(f"🔴 Worldserver exited with code: {exit_code}\n")
        self.update_status()
        if exit_code == 2: # restart
            self.log_manager("🔴 Restarting Worldserver...\n")
            self.start_worldserver()
        if exit_code == 1: # crash/error
            self.play_alert()
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            self.log_manager(f"❗ Worldserver crash at {timestamp}.\n")
            if self.RESTART_WORLDSERVER_ON_CRASH == 1:
                self.log_manager("🔴 Restarting Worldserver...\n")
                self.start_worldserver()

    def update_status(self):
        world_running = self.check_process("worldserver.exe")
        auth_running = self.check_process("authserver.exe")

        self.world_status_lbl.config(
            text=f"Worldserver: {'Running' if world_running else 'Stopped'}",
            fg="green" if world_running else "red"
        )

        self.auth_status_lbl.config(
            text=f"Authserver: {'Running' if auth_running else 'Stopped'}",
            fg="green" if auth_running else "red"
        )

        self.root.after(3000, self.update_status)

    def update_online_players(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            try:
                conn = mysql.connector.connect(
                    host = self.DATABASE_HOST,
                    port = self.DATABASE_PORT,
                    user = self.DATABASE_USER,
                    password = self.DATABASE_PASSWORD,
                    database = self.DATABASE_CHARACTERS,
                )
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM characters WHERE online = 1;")
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                self.serverstats_onlineplayers_lbl.config(
                    text=f"Online Players: {result[0]}",
                    fg="black"
                )
            except mysql.connector.Error as err:
                self.log_manager(f"❗ update_online_players: MySQL error: {err}\n")
        else:
            self.serverstats_onlineplayers_lbl.config(
                    text=f"Online Players: 0",
                    fg="grey"
                )
        
        if world_running:
            # Schedule check every 10s
            self.root.after(10000, self.update_online_players)

    def update_online_gms(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            try:
                conn = mysql.connector.connect(
                    host = self.DATABASE_HOST,
                    port = self.DATABASE_PORT,
                    user = self.DATABASE_USER,
                    password = self.DATABASE_PASSWORD,
                    database = self.DATABASE_CHARACTERS,
                )
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {self.DATABASE_CHARACTERS}.characters c
                    JOIN {self.DATABASE_AUTH}.account_access a ON c.account = a.id
                    WHERE c.online = 1 AND a.gmlevel > 0;
                """)
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                self.serverstats_onlinegms_lbl.config(
                    text=f"Online GMs: {result[0]}",
                    fg="black"
                )
            except mysql.connector.Error as err:
                self.log_manager(f"❗ update_online_gms: MySQL error: {err}\n")
        else:
            self.serverstats_onlinegms_lbl.config(
                    text=f"Online GMs: 0",
                    fg="grey"
                )
        
        if world_running:
            # Schedule check every 10s
            self.root.after(10000, self.update_online_gms)     

    def update_open_tickets(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            try:
                conn = mysql.connector.connect(
                    host = self.DATABASE_HOST,
                    port = self.DATABASE_PORT,
                    user = self.DATABASE_USER,
                    password = self.DATABASE_PASSWORD,
                    database = self.DATABASE_CHARACTERS,
                )
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM gm_ticket WHERE type = 0;")
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                self.serverstats_open_tickets_lbl.config(
                    text=f"Open Tickets: {result[0]}",
                    fg="black"
                )
            except mysql.connector.Error as err:
                self.log_manager(f"❗ update_open_tickets: MySQL error: {err}\n")
        else:
            self.serverstats_open_tickets_lbl.config(
                    text=f"Open Tickets: 0",
                    fg="grey"
                )
        
        if world_running:
            # Schedule check every 60s
            self.root.after(60000, self.update_open_tickets)

    def show_faction_pie_chart(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            for widget in self.stats_frame.winfo_children():
                widget.destroy()

            try:
                conn = mysql.connector.connect(
                    host=self.DATABASE_HOST,
                    port=self.DATABASE_PORT,
                    user=self.DATABASE_USER,
                    password=self.DATABASE_PASSWORD,
                    database=self.DATABASE_CHARACTERS,
                )
                cursor = conn.cursor()
                cursor.execute("SELECT race, COUNT(*) FROM characters WHERE online = 1 GROUP BY race")
                data = cursor.fetchall()
                cursor.close()
                conn.close()

                alliance_races = {1, 3, 4, 7, 11, 22}
                horde_races = {2, 5, 6, 8, 10, 9}
                alliance_count = sum(count for race, count in data if race in alliance_races)
                horde_count = sum(count for race, count in data if race in horde_races)
                total = alliance_count + horde_count
                if total == 0:
                    return

                labels = ['Alliance', 'Horde']
                sizes = [alliance_count, horde_count]
                colors = ['#0070ff', '#c41f3b']

                def autopct_format(pct, all_vals):
                    absolute = int(round(pct/100.*sum(all_vals)))
                    return f"{pct:.0f}%\n({absolute})"

                fig, ax = plt.subplots(figsize=(2.5,2.5))
                ax.pie(sizes, labels=labels, autopct=lambda pct: autopct_format(pct, sizes), colors=colors, startangle=90)
                ax.axis('equal')
                ax.set_title("Faction Distribution (Online Players)", fontsize=10, pad=3, fontweight='bold')
                fig.tight_layout()

                canvas = FigureCanvasTkAgg(fig, master=self.stats_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(expand=True, fill='both')

            except mysql.connector.Error as err:
                self.log_manager(f"❗ show_faction_pie_chart: MySQL error: {err}\n")

        if world_running:
            # Schedule check every 10s
            self.root.after(10000, self.show_faction_pie_chart)

    def check_process(self, name):
        return any(proc.info['name'] == name for proc in psutil.process_iter(['name']))

    def play_alert(self):
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)

if __name__ == "__main__":#
    root = tk.Tk()
    app = AzerothManager(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_log.set(), root.destroy()))
    root.mainloop()
