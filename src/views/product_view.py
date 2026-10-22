import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import ttkbootstrap as ttk

BACKEND_URL = "http://127.0.0.1:8000"


class ProductForm(ttk.Toplevel):
    """Modal dialog window for creating or editing product records."""

    def __init__(
        self, parent, token, product_id=None, initial_data=None, callback=None
    ):
        super().__init__(parent)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.product_id = product_id
        self.initial_data = initial_data or {}
        self.callback = callback

        self.title("Edit Product" if self.product_id else "Add New Product")
        self.geometry("400x320")
        self.resizable(False, False)
        self.grab_set()

        self.create_form()
        self.load_initial_data()

    def create_form(self):
        frame = ttk.Frame(self, padding="20")
        frame.pack(expand=True, fill=tk.BOTH)
        frame.columnconfigure(1, weight=1)

        # Name field
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(frame)
        self.name_entry.grid(row=0, column=1, sticky="ew")

        # Barcode field
        ttk.Label(frame, text="Barcode:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.barcode_entry = ttk.Entry(frame)
        self.barcode_entry.grid(row=1, column=1, sticky="ew")

        # Sell price field
        ttk.Label(frame, text="Selling Price:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.price_entry = ttk.Entry(frame)
        self.price_entry.grid(row=2, column=1, sticky="ew")

        # Stock quantity field
        ttk.Label(frame, text="Stock Qty:").grid(
            row=3, column=0, sticky="w", pady=5
        )
        self.stock_entry = ttk.Entry(frame)
        self.stock_entry.grid(row=3, column=1, sticky="ew")

        # Description field
        ttk.Label(frame, text="Description:").grid(
            row=4, column=0, sticky="w", pady=5
        )
        self.desc_entry = ttk.Entry(frame)
        self.desc_entry.grid(row=4, column=1, sticky="ew")

        # Control buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(
            btn_frame,
            text="Save",
            command=self.save_product,
            bootstyle="success",
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary",
        ).pack(side=tk.LEFT)

    def load_initial_data(self):
        self.name_entry.insert(0, self.initial_data.get("name", ""))
        self.barcode_entry.insert(
            0, self.initial_data.get("barcode", "") or ""
        )
        self.price_entry.insert(
            0, self.initial_data.get("price_sell", "")
        )
        self.stock_entry.insert(
            0, self.initial_data.get("stock_quantity", "")
        )
        self.desc_entry.insert(
            0, self.initial_data.get("description", "") or ""
        )

    def save_product(self):
        try:
            price_val = self.price_entry.get().replace(",", ".")
            data = {
                "name": self.name_entry.get(),
                "barcode": self.barcode_entry.get() or None,
                "price_sell": float(price_val),
                "stock_quantity": int(self.stock_entry.get()),
                "description": self.desc_entry.get(),
            }

            if (
                not data["name"]
                or data["price_sell"] <= 0
                or data["stock_quantity"] < 0
            ):
                return messagebox.showerror(
                    "Validation Error",
                    "Name, Price, and Stock Quantity are required.",
                    parent=self,
                )

            if self.product_id:
                response = requests.put(
                    f"{BACKEND_URL}/products/{self.product_id}",
                    headers=self.api_headers,
                    json=data,
                )
            else:
                response = requests.post(
                    f"{BACKEND_URL}/products",
                    headers=self.api_headers,
                    json=data,
                )

            if response.status_code in [200, 201]:
                messagebox.showinfo(
                    "Success", "Product saved successfully!", parent=self
                )
                if self.callback:
                    self.callback()
                self.destroy()
            else:
                messagebox.showerror(
                    "Save Error",
                    f"Details: {response.json().get('detail', response.text)}",
                    parent=self,
                )
        except ValueError:
            messagebox.showerror(
                "Format Error",
                "Price and Stock Quantity must be valid numbers.",
                parent=self,
            )
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e), parent=self)


class ProductView(ttk.Frame):
    """Main product inventory management tab view."""

    def __init__(self, parent, token, **kwargs):
        super().__init__(parent)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}

        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Top search section
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.load_products())

        ttk.Button(
            top_frame,
            text="Search",
            command=self.load_products,
            bootstyle="secondary",
        ).pack(side=tk.LEFT, padx=5)

        # Management actions header frame
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # CRUD actions
        ttk.Button(
            actions_frame,
            text="Add New",
            command=self.open_product_form,
            bootstyle="success",
        ).pack(side=tk.RIGHT)

        ttk.Button(
            actions_frame,
            text="Deactivate",
            command=self.delete_selected,
            bootstyle="danger-outline",
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Edit",
            command=self.edit_selected,
            bootstyle="info-outline",
        ).pack(side=tk.RIGHT, padx=5)

        # Backup controls
        ttk.Button(
            actions_frame,
            text="Import Backup (JSON)",
            command=self.import_full_backup,
            bootstyle="warning",
        ).pack(side=tk.LEFT)

        ttk.Button(
            actions_frame,
            text="Export Backup (JSON)",
            command=self.export_full_backup,
            bootstyle="secondary",
        ).pack(side=tk.LEFT, padx=5)

        # Product list table (Treeview)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Name", "Price", "Stock"),
            show="headings",
            bootstyle="primary",
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Product Name")
        self.tree.heading("Price", text="Price ($)")
        self.tree.heading("Stock", text="Stock Qty")

        self.tree.column("ID", width=250, stretch=tk.NO)
        self.tree.column("Name", width=300)
        self.tree.column("Price", width=100, anchor="e")
        self.tree.column("Stock", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview,
            bootstyle="round",
        )
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            response = requests.get(
                f"{BACKEND_URL}/products?search={self.search_entry.get()}",
                headers=self.api_headers,
            )
            if response.status_code == 200:
                for prod in response.json():
                    price_formatted = f"${prod['price_sell']:.2f}"
                    self.tree.insert(
                        "",
                        tk.END,
                        values=(
                            prod["_id"],
                            prod["name"],
                            price_formatted,
                            prod["stock_quantity"],
                        ),
                    )
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e))

    def export_full_backup(self):
        """Exports a full database backup (products, users, sales)."""
        try:
            response = requests.get(
                f"{BACKEND_URL}/backup/export/full", headers=self.api_headers
            )
            if response.status_code == 200:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    title="Save Full Backup",
                    initialfile="full_pos_backup.json",
                )
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(
                            response.json(), f, indent=4, ensure_ascii=False
                        )
                    messagebox.showinfo(
                        "Success", "Full backup exported successfully!"
                    )
            else:
                messagebox.showerror(
                    "Error", f"Failed to export backup: {response.text}"
                )
        except requests.exceptions.RequestException as e:
            messagebox.showerror(
                "Connection Error", f"Could not connect to server: {e}"
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error", f"An error occurred during export: {e}"
            )

    def import_full_backup(self):
        """Imports a full backup, replacing ALL current database records."""
        if not messagebox.askyesno(
            "Warning! Destructive Operation!",
            "You are about to import a full database backup.\n\n"
            "THIS WILL ERASE ALL CURRENT DATA (products, users, and sales) and replace them with the file data.\n\n"
            "This action cannot be undone.\n\nDo you wish to proceed?",
        ):
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Open Full Backup File",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            response = requests.post(
                f"{BACKEND_URL}/backup/import/full",
                headers=self.api_headers,
                json=backup_data,
            )

            if response.status_code == 200:
                messagebox.showinfo(
                    "Success",
                    "Full backup imported successfully!\nThe product list will now refresh.",
                )
                self.load_products()
            else:
                messagebox.showerror(
                    "Error", f"Failed to import backup: {response.text}"
                )
        except json.JSONDecodeError:
            messagebox.showerror(
                "File Error", "The selected file is not a valid JSON document."
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error", f"An error occurred during import: {e}"
            )

    def get_selected_product_id(self):
        if not (selected_item := self.tree.focus()):
            messagebox.showwarning("Warning", "Please select a product.")
            return None
        return self.tree.item(selected_item)["values"][0]

    def edit_selected(self):
        if not (pid := self.get_selected_product_id()):
            return
        try:
            response = requests.get(
                f"{BACKEND_URL}/products/lookup/{pid}", headers=self.api_headers
            )
            if response.status_code == 200:
                self.open_product_form(
                    product_id=pid, initial_data=response.json()
                )
            else:
                messagebox.showerror(
                    "Error", "Could not fetch product details."
                )
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e))

    def delete_selected(self):
        if not (pid := self.get_selected_product_id()):
            return
        if messagebox.askyesno(
            "Confirm Deactivation",
            "Are you sure you want to deactivate this product?",
        ):
            try:
                response = requests.delete(
                    f"{BACKEND_URL}/products/{pid}", headers=self.api_headers
                )
                if response.status_code in [200, 204]:
                    messagebox.showinfo("Success", "Product deactivated.")
                    self.load_products()
                else:
                    messagebox.showerror(
                        "Error", f"Failed to deactivate: {response.text}"
                    )
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", str(e))

    def open_product_form(self, product_id=None, initial_data=None):
        ProductForm(
            self,
            self.token,
            product_id,
            initial_data,
            callback=self.load_products,
        )