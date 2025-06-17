import sys
import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import os
import threading
import time
import winsound
import datetime
import psutil
import mysql.connector
from mysql.connector import Error
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from config.settings import SettingsManager
from core.logger import Logger
from ui.menu import Menu

# Compile
# python -m PyInstaller --onefile --windowed --icon=assets/manager.ico --add-data "assets;assets" manager.py

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

        self.settings = SettingsManager()
        self.settings.load_settings()
        self.menu = Menu(self.root)

        self.auth_process = None
        self.world_process = None
        self.auth_log_thread = None
        self.world_log_thread = None
        self.stop_log = threading.Event()

        self.menu.create_menu_bar(self.root)
        self.create_widgets()
        self.header()
        self.update_status()
        self.test_connect_mysql()

    def test_connect_mysql(self):
        try:
            connection = mysql.connector.connect(
                host = self.settings.DATABASE_HOST,
                port = self.settings.DATABASE_PORT,
                user = self.settings.DATABASE_USER,
                password = self.settings.DATABASE_PASSWORD,
                database = self.settings.DATABASE_CHARACTERS,
            )
            if connection.is_connected():
                self.logger.manager("🔴 MySQL test connection successful for DB: Characters.\n")
                return connection
        except Error as e:
            self.logger.manager(f"❗ MySQL connection failed: {e}\n")
            return None

    def get_server_resource_usage(self):
        usage_info = {
            "world": {"cpu": 0.0, "mem": 0.0},
            "auth": {"cpu": 0.0, "mem": 0.0},
        }

        if self.world_process and self.world_process.poll() is None:
            try:
                world_ps = psutil.Process(self.world_process.pid)

                # Prime CPU reading
                world_ps.cpu_percent(interval=None)
                time.sleep(1)  # Measure CPU over 1 second
                world_cpu_usage = world_ps.cpu_percent(interval=None)

                # Normalize CPU usage by number of cores
                world_num_cpus = psutil.cpu_count()
                world_normalized_cpu = world_cpu_usage / world_num_cpus

                world_mem_usage = world_ps.memory_info().rss / (1024 ** 2)  # in MB

                # Update your data safely (use a thread-safe structure if needed)
                usage_info["world"]["cpu"] = round(world_normalized_cpu, 2)
                usage_info["world"]["mem"] = round(world_mem_usage, 2)
            except Exception as e:
                self.logger.manager(f"❗ Error fetching worldserver stats: {e}\n")

        if self.auth_process and self.auth_process.poll() is None:
            try:
                auth_ps = psutil.Process(self.auth_process.pid)
                # Prime CPU reading
                auth_ps.cpu_percent(interval=None)
                time.sleep(1)  # Measure CPU over 1 second
                auth_cpu_usage = auth_ps.cpu_percent(interval=None)

                # Normalize CPU usage by number of cores
                auth_num_cpus = psutil.cpu_count()
                auth_normalized_cpu = auth_cpu_usage / auth_num_cpus

                auth_mem_usage = auth_ps.memory_info().rss / (1024 ** 2)  # in MB

                # Update your data safely (use a thread-safe structure if needed)
                usage_info["auth"]["cpu"] = round(auth_normalized_cpu, 2)
                usage_info["auth"]["mem"] = round(auth_mem_usage, 2)
            except Exception as e:
                self.logger.manager(f"❗ Error fetching authserver stats: {e}\n")

        return usage_info

    def update_resource_display(self):
        usage = self.get_server_resource_usage()
        text = (
            f"Worldserver: CPU {usage['world']['cpu']:.1f}% | RAM {usage['world']['mem']:.1f} MB   Authserver: CPU {usage['auth']['cpu']:.1f}% | RAM {usage['auth']['mem']:.1f} MB"
        )
        self.resource_lbl.config(text=text, fg='black')
        self.root.after(3000, self.update_resource_display)  # Refresh every 3 sec

    def send_world_command(self, command):
        if self.world_process and self.world_process.poll() is None:
            try:
                self.world_process.stdin.write((command + '\n').encode())
                self.world_process.stdin.flush()
                self.logger.world(f"[Input] {command}\n")
            except Exception as e:
                self.logger.manager(f"❗ Failed to send command: {e}\n")
        else:
            self.logger.manager("❗ worldserver is not running.\n")

    def create_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        gmlevel = self.gmlevel_entry.get()

        if not username or not password:
            self.logger.manager("⚠️ Username and password cannot be empty.\n")
            return

        command = f"account create {username} {password}"
        self.send_world_command(command)

        if gmlevel >= 1:
            command = f"account set gmlevel {username} {gmlevel} -1"
            self.send_world_command(command)

    def ban_account(self):
        username = self.ban_username_entry.get()
        duration = self.ban_duration_entry.get()
        reason = self.ban_reason_entry.get()

        if not username or not duration or not reason:
            self.logger.manager("⚠️ Fill in all ban fields.\n")
            return

        command = f'ban account {username} {duration} "{reason}"'
        self.send_world_command(command)

    def unban_account(self):
        username = self.ban_username_entry.get()

        if not username:
            self.logger.manager("⚠️ Username required to unban.\n")
            return

        command = f'unban account {username}'
        self.send_world_command(command)

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

        # Server Resources
        server_resource_frame = tk.Frame(self.root)
        server_resource_frame.pack(pady=5, fill='x')

        self.resource_title_lbl = tk.Label(server_resource_frame, text="Server Resources:", fg="black")
        self.resource_title_lbl.pack(side="left", padx=5)

        self.resource_lbl = tk.Label(server_resource_frame, text=
                                     "Worldserver: CPU | RAM Authserver: CPU | RAM ",
                                     fg="grey")
        self.resource_lbl.pack(side='left', padx=5)

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

        # Wrapper Main Frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Manager log tab
        self.manager_log = scrolledtext.ScrolledText(self.notebook, state='disabled')
        self.notebook.add(self.manager_log, text="Manager Log")

        # Authserver log tab
        self.auth_log = scrolledtext.ScrolledText(self.notebook, state='disabled')
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

        # Create loggers
        self.logger = Logger(
            manager_widget=self.manager_log,
            auth_widget=self.auth_log,
            world_widget=self.world_log_output
        )

        # Statistics tab 
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Server Stats")
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Account Tools
        account_tools_frame = tk.LabelFrame(main_frame, text="Account Tools", padx=10, pady=10)
        account_tools_frame.pack(pady=10)

        # Create Account
        create_account_frame = tk.LabelFrame(account_tools_frame, text = "Create Account")
        create_account_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(create_account_frame, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(create_account_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(create_account_frame, text="Password:").grid(row=1, column=0, sticky="e")
        self.password_entry = tk.Entry(create_account_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        tk.Label(create_account_frame, text="GM Level:").grid(row=2, column=0, sticky="e")
        self.gmlevel_entry = tk.Entry(create_account_frame)
        self.gmlevel_entry.grid(row=2, column=1)

        create_account_btn = tk.Frame(create_account_frame)
        create_account_btn.grid(row=3, column=0, columnspan=2, pady=5)

        tk.Button(create_account_btn, text="Create Account", command=self.create_account).pack(side=tk.LEFT, padx=5)

        # Ban/Unban
        ban_frame = tk.LabelFrame(account_tools_frame, text="Ban / Unban")
        ban_frame.pack(pady=10)

        tk.Label(ban_frame, text="Username:").grid(row=0, column=0, sticky="e")
        self.ban_username_entry = tk.Entry(ban_frame)
        self.ban_username_entry.grid(row=0, column=1)

        tk.Label(ban_frame, text="Duration (1d7h5m):").grid(row=1, column=0, sticky="e")
        self.ban_duration_entry = tk.Entry(ban_frame)
        self.ban_duration_entry.grid(row=1, column=1)

        tk.Label(ban_frame, text="Reason:").grid(row=2, column=0, sticky="e")
        self.ban_reason_entry = tk.Entry(ban_frame)
        self.ban_reason_entry.grid(row=2, column=1)

        ban_buttons = tk.Frame(ban_frame)
        ban_buttons.grid(row=3, column=0, columnspan=2, pady=5)

        tk.Button(ban_buttons, text="Ban", command=self.ban_account).pack(side=tk.LEFT, padx=5)
        tk.Button(ban_buttons, text="Unban", command=self.unban_account).pack(side=tk.LEFT, padx=5)

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
                self.logger.world(f"❗ Failed to send command: {e}\n")
        else:
            self.logger.world(f"❗ Failed to send command: {e}\nWorldserver is not running or stdin is unavailable.\n")

    def header(self):
        self.logger.manager("\n")
        self.logger.manager("   █████╗ ███████╗███████╗██████╗  ██████╗ ████████╗██╗  ██╗\n")
        self.logger.manager("  ██╔══██╗╚══███╔╝██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║  ██║\n")
        self.logger.manager("  ███████║  ███╔╝ █████╗  ██████╔╝██║   ██║   ██║   ███████║\n")
        self.logger.manager("  ██╔══██║ ███╔╝  ██╔══╝  ██╔══██╗██║   ██║   ██║   ██╔══██║\n")
        self.logger.manager("  ██║  ██║███████╗███████╗██║  ██║╚██████╔╝   ██║   ██║  ██║\n")
        self.logger.manager("  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝\n")
        self.logger.manager("                                   ██████╗ ██████╗ ██████╗ ███████╗\n")
        self.logger.manager("                                  ██╔════╝██╔═══██╗██╔══██╗██╔════╝\n")
        self.logger.manager("                                  ██║     ██║   ██║██████╔╝█████╗\n")
        self.logger.manager("                                  ██║     ██║   ██║██╔══██╗██╔══╝\n")
        self.logger.manager("                                  ╚██████╗╚██████╔╝██║  ██║███████╗\n")
        self.logger.manager("                                   ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝\n\n")
        self.logger.manager("   https://github.com/Kitzunu/azerothcore-server-manager/\n\n")
        self.logger.manager("❗ Make sure to configure the SETTINGS before running the servers. ❗\n\n")
        self.logger.manager(f"➕ Restart Worldserver on crash: {self.settings.RESTART_WORLDSERVER_ON_CRASH}\n")

    def start_authserver(self):
        world_running = self.check_process("authserver.exe")
        if world_running:
            self.logger.manager("❗ Authserver are already running.\n")
            return

        try:
            # --- Start authserver ---
            self.auth_process = subprocess.Popen(
                [self.settings.AUTH_PATH],
                cwd=os.path.dirname(self.settings.AUTH_PATH),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            )

            # Start threads to read authserver stdout/stderr
            threading.Thread(
                target=self.read_stream,
                args=(self.auth_process.stdout, self.logger.auth),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_stream,
                args=(self.auth_process.stderr, self.logger.auth),
                daemon=True
            ).start()

            self.auth_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.settings.AUTH_LOG_FILE, self.logger.auth),
                daemon=True
            )
            self.auth_log_thread.start()

            self.update_status()
            self.logger.manager("🔴 Authserver started.\n")

        except Exception as e:
            self.logger.manager(f"❗ Error starting Authserver: {e}\n")

    def start_worldserver(self):
        world_running = self.check_process("worldserver.exe")
        if world_running:
            self.logger.manager("❗ Worldserver are already running.\n")
            return

        try:
            # --- Start worldserver ---
            self.world_process = subprocess.Popen(
                [self.settings.WORLD_PATH],
                cwd=os.path.dirname(self.settings.WORLD_PATH),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
            )

            # Start threads to read worldserver stdout/stderr
            threading.Thread(
                target=self.read_stream,
                args=(self.world_process.stdout, self.logger.world),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_stream,
                args=(self.world_process.stderr, self.logger.world),
                daemon=True
            ).start()

            self.stop_log.clear()
            self.world_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.settings.WORLD_LOG_FILE, self.logger.world),
                daemon=True
            )
            self.world_log_thread.start()

            threading.Thread(target=self.monitor_worldserver, daemon=True).start()
            threading.Thread(target=self.update_resource_display, daemon=True).start()

            self.update_status()
            self.update_online_players()
            self.update_online_gms()
            self.update_open_tickets()
            self.show_faction_pie_chart()
            self.logger.manager("🔴 Worldserver started.\n")

        except Exception as e:
            self.logger.manager(f"❗ Error starting Worldserver: {e}\n")

    def read_stream(self, stream, log_function):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    log_function(line)
        except Exception as e:
            self.logger.manager(f"❗ Error reading server output: {e}\n")

    def tail_log_file(self, filepath, log_function):
        try:
            if not os.path.exists(filepath):
                self.logger.manager(f"❗ Log file not found: {filepath}\n")
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
                    self.logger.manager(f"❗ Error reading log {filepath}: {e}\n")
                    time.sleep(1)

        except Exception as e:
            self.logger.manager(f"❗ General error tailing log file {filepath}: {e}\n")

    def kill_authserver(self):
        if self.auth_process:
            self.auth_process.terminate()
            self.auth_process = None
        
        self.logger.manager("🔴 Authserver killed.\n")
        self.update_status()

    def stop_worldserver(self):
        self.stop_log.set()

        if self.world_process:
            self.world_process.stdin.write("server exit" + '\n')
            self.world_process.stdin.flush()
            self.world_process = None

        self.logger.manager("🔴 Worldserver stopped.\n")
        self.update_status()

    def kill_workdserver(self):
        if self.world_process:
            self.world_process.terminate()
            self.world_process = None
        
        self.logger.manager("🔴 Worldserver killed.\n")
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
            self.logger.manager(f"🔴 Worldserver will restart in {self.delay_str}...\n")

    def monitor_worldserver(self):
        exit_code = self.world_process.wait()
        self.logger.manager(f"🔴 Worldserver exited with code: {exit_code}\n")
        self.update_status()
        if exit_code == 2: # restart
            self.logger.manager("🔴 Restarting Worldserver...\n")
            self.start_worldserver()
        if exit_code == 1: # crash/error
            self.play_alert()
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            self.logger.manager(f"❗ Worldserver crash at {timestamp}.\n")
            if self.settings.RESTART_WORLDSERVER_ON_CRASH:
                self.logger.manager("🔴 Restarting Worldserver...\n")
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
                    host = self.settings.DATABASE_HOST,
                    port = self.settings.DATABASE_PORT,
                    user = self.settings.DATABASE_USER,
                    password = self.settings.DATABASE_PASSWORD,
                    database = self.settings.DATABASE_CHARACTERS,
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
                self.logger.manager(f"❗ update_online_players: MySQL error: {err}\n")
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
                    host = self.settings.DATABASE_HOST,
                    port = self.settings.DATABASE_PORT,
                    user = self.settings.DATABASE_USER,
                    password = self.settings.DATABASE_PASSWORD,
                    database = self.settings.DATABASE_CHARACTERS,
                )
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {self.settings.DATABASE_CHARACTERS}.characters c
                    JOIN {self.settings.DATABASE_AUTH}.account_access a ON c.account = a.id
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
                self.logger.manager(f"❗ update_online_gms: MySQL error: {err}\n")
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
                    host = self.settings.DATABASE_HOST,
                    port = self.settings.DATABASE_PORT,
                    user = self.settings.DATABASE_USER,
                    password = self.settings.DATABASE_PASSWORD,
                    database = self.settings.DATABASE_CHARACTERS,
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
                self.logger.manager(f"❗ update_open_tickets: MySQL error: {err}\n")
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
                    host=self.settings.DATABASE_HOST,
                    port=self.settings.DATABASE_PORT,
                    user=self.settings.DATABASE_USER,
                    password=self.settings.DATABASE_PASSWORD,
                    database=self.settings.DATABASE_CHARACTERS,
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
                self.logger.manager(f"❗ show_faction_pie_chart: MySQL error: {err}\n")

        if world_running:
            # Schedule check every 10s
            self.root.after(10000, self.show_faction_pie_chart)

    def check_process(self, name):
        return any(proc.info['name'] == name for proc in psutil.process_iter(['name']))

    def play_alert(self):
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)

if __name__ == "__main__":
    root = tk.Tk()
    app = AzerothManager(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_log.set(), root.destroy()))
    root.mainloop()
