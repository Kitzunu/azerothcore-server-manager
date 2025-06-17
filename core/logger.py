import tkinter as tk

class Logger:
    def __init__(self, manager_widget: tk.Text, auth_widget: tk.Text, world_widget: tk.Text):
        self._manager_log = manager_widget
        self._auth_log = auth_widget
        self._world_log = world_widget

    def _append_text(self, widget: tk.Text, text: str):
        widget.config(state='normal')
        widget.insert(tk.END, text)
        widget.config(state='disabled')
        widget.see(tk.END)

    def manager(self, text: str):
        self._append_text(self._manager_log, text)

    def auth(self, text: str):
        self._append_text(self._auth_log, text)

    def world(self, text: str):
        self._append_text(self._world_log, text)
