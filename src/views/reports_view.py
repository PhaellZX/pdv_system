import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import requests
import ttkbootstrap as ttk

BACKEND_URL = "http://127.0.0.1:8000"


class ReportsView(ttk.Frame):
    """Dashboard tab view displaying sales KPIs and performance charts."""

    def __init__(self, parent, token, **kwargs):
        super().__init__(parent)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}

        self.create_widgets()
        self.load_dashboard_data()

    def create_widgets(self):
        # KPI Cards section header
        kpi_frame = ttk.Frame(self, padding=10)
        kpi_frame.pack(fill=tk.X, expand=True)
        kpi_frame.columnconfigure((0, 1, 2), weight=1)

        # Revenue Card
        revenue_card = ttk.LabelFrame(
            kpi_frame, text="Total Revenue", padding=20, bootstyle="primary"
        )
        revenue_card.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.kpi_revenue_label = ttk.Label(
            revenue_card,
            text="$ 0.00",
            font=("Segoe UI", 18, "bold"),
            anchor="center",
            bootstyle="inverse-primary",
        )
        self.kpi_revenue_label.pack(fill=tk.X)

        # Sales Count Card
        sales_card = ttk.LabelFrame(
            kpi_frame, text="Total Sales", padding=20, bootstyle="info"
        )
        sales_card.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.kpi_sales_label = ttk.Label(
            sales_card,
            text="0",
            font=("Segoe UI", 18, "bold"),
            anchor="center",
            bootstyle="inverse-info",
        )
        self.kpi_sales_label.pack(fill=tk.X)

        # Average Ticket Card
        ticket_card = ttk.LabelFrame(
            kpi_frame, text="Average Ticket", padding=20, bootstyle="success"
        )
        ticket_card.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.kpi_ticket_label = ttk.Label(
            ticket_card,
            text="$ 0.00",
            font=("Segoe UI", 18, "bold"),
            anchor="center",
            bootstyle="inverse-success",
        )
        self.kpi_ticket_label.pack(fill=tk.X)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=15, padx=10)

        # Charts section container
        self.charts_frame = ttk.Frame(self)
        self.charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.charts_frame.columnconfigure(0, weight=1)
        self.charts_frame.rowconfigure(0, weight=1)

        self.top_products_frame = ttk.Frame(self.charts_frame)
        self.top_products_frame.grid(row=0, column=0, sticky="nsew")

    def load_dashboard_data(self):
        try:
            # Fetch KPI metrics
            kpi_response = requests.get(
                f"{BACKEND_URL}/dashboard/kpis", headers=self.api_headers
            )
            if kpi_response.status_code == 200:
                kpis = kpi_response.json()
                self.kpi_revenue_label.config(
                    text=f"$ {kpis['total_revenue']:.2f}"
                )
                self.kpi_sales_label.config(text=f"{kpis['total_sales']}")
                self.kpi_ticket_label.config(
                    text=f"$ {kpis['average_ticket']:.2f}"
                )

            # Fetch Top Products metrics and render chart
            top_prod_response = requests.get(
                f"{BACKEND_URL}/dashboard/top-products", headers=self.api_headers
            )
            if top_prod_response.status_code == 200:
                self.plot_top_products(top_prod_response.json())

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e))

    def plot_top_products(self, data):
        for widget in self.top_products_frame.winfo_children():
            widget.destroy()

        if not data:
            ttk.Label(
                self.top_products_frame,
                text="Not enough sales data to generate chart.",
            ).pack()
            return

        plt.style.use("default")

        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor("#f8f9fa")

        ax = fig.add_subplot(111)
        ax.set_facecolor("#ffffff")

        products = [item["product_name"] for item in data]
        quantities = [item["total_sold"] for item in data]

        # Vertical bar graph
        bars = ax.bar(products, quantities, color="#0d6efd")
        ax.set_ylabel("Quantity Sold", color="gray")
        ax.set_title("Top 5 Best Selling Products")

        # Clean top/right borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Subtle Y-axis grid
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

        # Rotate labels to avoid overlap
        plt.setp(ax.get_xticklabels(), rotation=15, ha="right")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.top_products_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)