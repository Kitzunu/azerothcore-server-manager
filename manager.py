import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import subprocess
import os
import psutil
import threading
import time
import configparser
import winsound
import datetime

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

        self.create_widgets()
        self.update_status()

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
            with open(SETTINGS_FILE, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(SETTINGS_FILE)

        self.WORLD_PATH = self.config['Paths']['worldserver']
        self.AUTH_PATH = self.config['Paths']['authserver']
        self.WORLD_LOG_FILE = self.config['Paths']['world_log_file']
        self.AUTH_LOG_FILE = self.config['Paths']['auth_log_file']
        self.RESTART_WORLDSERVER_ON_CRASH = self.config.getboolean('General', 'restart_worldserver_on_crash')

    def save_settings(self):
        self.config['Paths']['worldserver'] = self.WORLD_PATH
        self.config['Paths']['authserver'] = self.AUTH_PATH
        self.config['Paths']['world_log_file'] = self.WORLD_LOG_FILE
        self.config['Paths']['auth_log_file'] = self.AUTH_LOG_FILE
        self.config['General']['restart_worldserver_on_crash'] = self.RESTART_WORLDSERVER_ON_CRASH
        with open(SETTINGS_FILE, 'w') as configfile:
            self.config.write(configfile)

    def create_widgets(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        self.start_btn = tk.Button(button_frame, text="Start Server", command=self.start_server, width=15)
        self.stop_btn = tk.Button(button_frame, text="Stop Server", command=self.stop_server, width=15)
        self.restart_btn = tk.Button(button_frame, text="Restart Server", command=self.restart_server, width=15)
        self.settings_btn = tk.Button(button_frame, text="Settings", command=self.open_settings_window, width=15)

        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.restart_btn.pack(side=tk.LEFT, padx=5)
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        # Status Frame
        status_frame_wrapper = tk.Frame(self.root)
        status_frame_wrapper.pack(fill="x")  # allows child frame to center itself

        status_frame = tk.Frame(status_frame_wrapper)
        status_frame.pack(pady=5)  # this centers it by default in the x-filled wrapper

        self.world_status_lbl = tk.Label(status_frame, text="Worldserver: Unknown", fg="gray")
        self.world_status_lbl.pack(side="left", padx=5)

        self.auth_status_lbl = tk.Label(status_frame, text="Authserver: Unknown", fg="gray")
        self.auth_status_lbl.pack(side="left", padx=5)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Manager log tab
        self.manager_log = scrolledtext.ScrolledText(self.notebook, width=80, height=15, state='disabled')
        self.notebook.add(self.manager_log, text="Manager Log")
        self.manager_tab_index = self.notebook.index(self.manager_log)
        self.log_manager("❗ Make sure to configure the SETTINGS before running the servers.\n")

        # Authserver log tab
        self.auth_log = scrolledtext.ScrolledText(self.notebook, width=80, height=15, state='disabled')
        self.notebook.add(self.auth_log, text="Authserver Log")

        # Worldserver log tab
        self.world_log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.world_log_frame, text="Worldserver Console")

        # Frame to hold the text and scrollbar
        self.world_log_text_frame = tk.Frame(self.world_log_frame)
        self.world_log_text_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        # Scrollbar
        self.world_scrollbar = tk.Scrollbar(self.world_log_text_frame)
        self.world_scrollbar.pack(side="right", fill="y")

        # World log output (Text widget)
        self.world_log_output = tk.Text(
            self.world_log_text_frame,
            wrap="word",
            height=20,
            yscrollcommand=self.world_scrollbar.set
        )
        self.world_log_output.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar to text widget
        self.world_scrollbar.config(command=self.world_log_output.yview)

        # Frame for input + button
        self.world_input_frame = tk.Frame(self.world_log_frame)
        self.world_input_frame.pack(fill="x", padx=5, pady=5)

        # Input entry
        self.world_input = tk.Entry(self.world_input_frame)
        self.world_input.pack(side="left", fill="x", expand=True)

        # Send button
        self.world_send_button = tk.Button(self.world_input_frame, text="Send", command=self.send_world_input)
        self.world_send_button.pack(side="left", padx=(5, 0))
        self.world_input.bind("<Return>", lambda event: self.send_world_input())

    def send_world_input(self):
        command = self.world_input.get().strip()
        if command and self.world_process and self.world_process.stdin:
            try:
                self.world_process.stdin.write(command + '\n')
                self.world_process.stdin.flush()
                self.world_log_output.insert("end", f"> {command}\n")
                self.world_log_output.see("end")
                self.world_input.delete(0, 'end')
            except Exception as e:
                self.world_log_output.insert("end", f"❗ Failed to send command: {e}\n")
        else:
            self.manager_log.insert("end", "❗ Failed to send command: {e}\nWorldserver is not running or stdin is unavailable.\n")

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

        def save():
            self.WORLD_PATH = world_entry.get()
            self.AUTH_PATH = auth_entry.get()
            self.WORLD_LOG_FILE = world_log_entry.get()
            self.AUTH_LOG_FILE = auth_log_entry.get()
            self.RESTART_WORLDSERVER_ON_CRASH = restart_var.get()
            self.save_settings()
            settings_win.destroy()
            self.log_manager("🔴 Settings saved.\n")

        tk.Button(settings_win, text="Save", command=save).grid(row=5, column=1, pady=10)

    def start_authserver(self):
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

    def start_worldserver(self):
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

        threading.Thread(target=self.monitor_worldserver, daemon=True).start()

    def start_server(self):
        if self.auth_process or self.world_process:
            self.log_manager("❗ Servers are already running.\n")
            return

        try:
            self.start_authserver()
            self.start_worldserver()
            self.log_manager("🔴 Servers started.\n")

            # --- Start log tail threads ---
            self.stop_log.clear()
            self.auth_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.AUTH_LOG_FILE, self.log_auth),
                daemon=True
            )
            self.world_log_thread = threading.Thread(
                target=self.tail_log_file,
                args=(self.WORLD_LOG_FILE, self.log_world),
                daemon=True
            )
            self.auth_log_thread.start()
            self.world_log_thread.start()
            self.log_manager("🔴 Log threads started.\n")

            self.update_status()

        except Exception as e:
            self.log_manager(f"❗ Error starting servers: {e}\n")

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

    def stop_server(self):
        self.stop_log.set()

        if self.auth_process:
            self.auth_process.terminate()
            self.auth_process = None

        if self.world_process:
            self.world_process.stdin.write("server exit" + '\n')
            self.world_process.stdin.flush()
            self.world_process = None

        self.log_manager("🔴 Servers stopped.\n")
        self.update_status()

    def restart_server(self):
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
            tk.Label(restart_popup, text="You cannot restart the server if WorldServer is offline.", fg="red", font=("Arial", 8)).grid(row=0, column=0, columnspan=2)
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

            def submit():
                delay = delay_entry.get()
                exit_code = exitcode_entry.get()
                if delay and exit_code:
                    cmd = f"server restart {delay} {exit_code}\n"
                    self.world_process.stdin.write(cmd)
                    self.world_process.stdin.flush()
                    restart_popup.destroy()
                else:
                    tk.messagebox.showwarning("Input error", "Please fill both fields")

            submit_btn = tk.Button(restart_popup, text="Submit", command=submit)
            submit_btn.grid(row=4, column=0, columnspan=2, pady=10)

            self.log_manager("🔴 Worldserver restarting command sent...\n")

    def monitor_worldserver(self):
        exit_code = self.world_process.wait()
        self.log_manager(f"🔴 Worldserver exited with code: {exit_code}\n")
        self.update_status()
        if exit_code == 2: # restart
            self.log_manager("🔴 Restarting Worldserver...\n")
            self.start_worldserver()
        if exit_code == 1: # crash/error
            self.play_alert(self.root)
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

    def check_process(self, name):
        return any(proc.info['name'] == name for proc in psutil.process_iter(['name']))

    def play_alert(root, count=5):
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)

if __name__ == "__main__":
    root = tk.Tk()
    app = AzerothManager(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_log.set(), root.destroy()))
    root.mainloop()
