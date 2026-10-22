import os
import sys
import tkinter as tk
from tkinter import messagebox
import requests
import ttkbootstrap as ttk

# Updated import path to match the new src/views module location
from src.views.main_view import MainApplication

BACKEND_URL = "http://127.0.0.1:8000"


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller executable binaries."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # Resolves base directory relative to project root
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class LoginApp:
    """Login window interface application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Login - POS System")
        self.root.geometry("400x320")
        self.root.resizable(True, True)

        try:
            # Updated path pointing to the new assets/icons directory
            icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
            img = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(False, img)
        except tk.TclError:
            print("Icon file 'assets/icons/icon.png' was not found or is invalid.")

        self.root.eval("tk::PlaceWindow . center")

        self.main_frame = ttk.Frame(self.root, padding=(20, 20))
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.create_widgets()

    def create_widgets(self):
        # Title Header
        title_label = ttk.Label(
            self.main_frame,
            text="System Login",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary",
        )
        title_label.pack(pady=(10, 20))

        # Form Controls
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10, fill=tk.X)

        username_label = ttk.Label(
            form_frame, text="Username:", font=("Segoe UI", 10)
        )
        username_label.pack(fill=tk.X)

        self.username_entry = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        self.username_entry.focus_set()

        password_label = ttk.Label(
            form_frame, text="Password:", font=("Segoe UI", 10)
        )
        password_label.pack(fill=tk.X)

        self.password_entry = ttk.Entry(
            form_frame, show="*", font=("Segoe UI", 10)
        )
        self.password_entry.pack(fill=tk.X)

        login_button = ttk.Button(
            self.main_frame,
            text="➤ Sign In",
            command=self.attempt_login,
            bootstyle="primary",
        )
        login_button.pack(pady=(20, 10), ipady=5, ipadx=20)

        # Bind Enter key to submit login
        self.root.bind("<Return>", lambda event=None: login_button.invoke())

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror(
                "Login Error", "Username and password are required fields."
            )
            return

        try:
            response = requests.post(
                f"{BACKEND_URL}/token",
                data={"username": username, "password": password},
            )

            if response.status_code == 200:
                access_token = response.json().get("access_token")
                self.main_frame.pack_forget()
                MainApplication(self.root, token=access_token).pack(
                    expand=True, fill=tk.BOTH
                )
            elif response.status_code == 401:
                messagebox.showerror(
                    "Login Error", "Incorrect username or password."
                )
            else:
                messagebox.showerror(
                    "Error", f"An unexpected error occurred: {response.text}"
                )
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "Could not connect to authentication server.",
            )


if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = LoginApp(root)
    root.mainloop()