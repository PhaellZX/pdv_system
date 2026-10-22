import os
import sys
import tkinter as tk
from tkinter import messagebox
import requests
import ttkbootstrap as ttk

# Updated relative imports matching the new src/views module location
from src.views.forecast_view import ForecastView
from src.views.pos_view import POSView
from src.views.product_view import ProductView
from src.views.reports_view import ReportsView

BACKEND_URL = "http://127.0.0.1:8000"


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller executable binaries."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainApplication(tk.Frame):
    """Main window application container housing the navigation menu and view frames."""

    def __init__(self, parent: tk.Tk, token: str):
        super().__init__(parent)
        self.parent = parent
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.current_view = None
        self.user_data = None

        self.parent.title("POS System - Main Dashboard")
        self.parent.geometry("1100x700")

        # Load window application icon from the assets directory
        try:
            icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
            img = tk.PhotoImage(file=icon_path)
            self.parent.iconphoto(False, img)
        except tk.TclError:
            print("Icon file 'assets/icons/icon.png' was not found or is invalid.")

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.load_user_info()

    def create_widgets(self):
        self.create_menu()

        # Styled Status Bar
        self.status_bar = ttk.Label(
            self.parent, text="Ready", padding=5, bootstyle="primary-inverse"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Logged User Info Bar
        user_info_frame = ttk.LabelFrame(
            self.parent, text="Active User", padding=10, bootstyle="secondary"
        )
        user_info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        self.user_info_label = ttk.Label(
            user_info_frame, text="Loading user profile...", font=("Segoe UI", 10)
        )
        self.user_info_label.pack()

        # Main Workspace Canvas
        self.main_content_frame = ttk.Frame(self.parent)
        self.main_content_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.welcome_label = ttk.Label(
            self.main_content_frame,
            text="Select a module from the top navigation menu to get started.",
            font=("Segoe UI", 16),
            bootstyle="secondary",
        )
        self.welcome_label.pack(pady=50)

    def create_menu(self):
        menubar = ttk.Menu(self.parent)
        self.parent.config(menu=menubar)

        # Checkout / POS Menu
        pos_menu = ttk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Point of Sale", menu=pos_menu)
        pos_menu.add_command(label="Open POS Terminal", command=self.show_pos_view)

        # Management Modules Menu
        management_menu = ttk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Management", menu=management_menu)
        management_menu.add_command(
            label="Product Inventory", command=self.show_product_view
        )
        management_menu.add_command(
            label="Reports & KPIs", command=self.show_reports_view
        )
        management_menu.add_command(
            label="Sales Forecast", command=self.show_forecast_view
        )
        management_menu.add_separator()
        management_menu.add_command(label="Exit", command=self.on_closing)

    def show_view(self, view_class, **kwargs):
        if self.welcome_label:
            self.welcome_label.pack_forget()
            self.welcome_label = None

        if self.current_view:
            self.current_view.destroy()

        self.current_view = view_class(
            self.main_content_frame, self.token, **kwargs
        )
        self.current_view.pack(fill=tk.BOTH, expand=True)

    def show_pos_view(self):
        if self.user_data:
            self.show_view(POSView, user_info=self.user_data)
        else:
            messagebox.showwarning(
                "Warning", "Please wait for user information to finish loading."
            )

    def show_product_view(self):
        self.show_view(ProductView)

    def show_reports_view(self):
        self.show_view(ReportsView)

    def show_forecast_view(self):
        self.show_view(ForecastView)

    def load_user_info(self):
        try:
            self.status_bar.config(text="Fetching user profile information...")
            response = requests.get(
                f"{BACKEND_URL}/users/me", headers=self.api_headers
            )
            if response.status_code == 200:
                self.user_data = response.json()
                welcome_message = (
                    f"Welcome, {self.user_data['username']}! | "
                    f"Role: {self.user_data['role'].capitalize()}"
                )
                self.user_info_label.config(text=welcome_message)
                self.status_bar.config(text="Ready")
            else:
                messagebox.showerror(
                    "Authentication Error",
                    f"Your session has expired.\n\nDetails: {response.text}",
                )
                self.parent.destroy()
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error", "Could not connect to authentication server."
            )
            self.parent.destroy()

    def on_closing(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit the application?"):
            self.parent.destroy()