import sys
import os
import tkinter as tk
import webbrowser

class InfoWindow:
    def __init__(self, root):
        self.root = root

    def open_info_window(self):
        info_win = tk.Toplevel(self.root)
        info_win.title("Info")

        # Get the correct path to the icon
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "assets", "manager.ico")
        info_win.iconbitmap(icon_path)

        # Title
        title_label = tk.Label(info_win, text="AzerothCore Server Manager", font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 5))

        # Frame to hold Text and Scrollbar
        frame = tk.Frame(info_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        # Multi-line Text widget (read-only)
        text_widget = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, height=15, width=60)
        text_widget.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=text_widget.yview)

        # Sample multi-line info text
        info_text = (
            "MIT License\n\n"
            "Copyright (c) 2025 Kitzunu\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE."
        )

        text_widget.insert("1.0", info_text)
        text_widget.config(state="disabled")  # Make text read-only

        # Credits Label (simple, non-scrollable)
        credits_label = tk.Label(info_win, text="Developed by Kitzunu © 2025", font=("Arial", 10), fg="gray")
        credits_label.pack(pady=(0, 10))

        # Clickable GitHub link
        def open_github(event):
            webbrowser.open_new("https://github.com/Kitzunu")

        github_link = tk.Label(info_win, text="GitHub: https://github.com/Kitzunu", font=("Arial", 10, "underline"), fg="blue", cursor="hand2")
        github_link.pack()
        github_link.bind("<Button-1>", open_github)