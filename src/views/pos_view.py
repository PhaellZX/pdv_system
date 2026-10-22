import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests

# Updated import path to match the new src/utils structure
from src.utils.receipt_generator import create_receipt_image

BACKEND_URL = "http://127.0.0.1:8000"


class PaymentWindow(tk.Toplevel):
    def __init__(self, parent, total_amount, sale_data, api_headers):
        super().__init__(parent)
        self.parent = parent
        self.total_amount = total_amount
        self.sale_data = sale_data
        self.api_headers = api_headers
        self.sale_successful = False
        self.sale_details = None
        self.amount_received = 0.0  # Stores cash amount provided by the customer

        self.title("Checkout / Payment")
        self.geometry("400x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)

        # Total amount display
        ttk.Label(
            main_frame, text="Total Due:", font=("Segoe UI", 14)
        ).grid(row=0, column=0, sticky="ew")
        
        ttk.Label(
            main_frame,
            text=f"R$ {self.total_amount:.2f}",
            font=("Segoe UI", 28, "bold"),
            bootstyle="success",
        ).grid(row=1, column=0, pady=(5, 20))

        ttk.Separator(main_frame).grid(row=2, column=0, sticky="ew", pady=10)

        # Payment method selection
        ttk.Label(
            main_frame, text="Payment Method:", font=("Segoe UI", 12)
        ).grid(row=3, column=0, sticky="w")

        radio_frame = ttk.Frame(main_frame)
        radio_frame.grid(row=4, column=0, sticky="w", pady=5)

        self.payment_method_var = tk.StringVar(value="Cash")
        ttk.Radiobutton(
            radio_frame,
            text="Cash",
            variable=self.payment_method_var,
            value="Cash",
            command=self.toggle_payment_fields,
            bootstyle="primary",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            radio_frame,
            text="PIX / Card",
            variable=self.payment_method_var,
            value="PIX/Card",
            command=self.toggle_payment_fields,
            bootstyle="primary",
        ).pack(side=tk.LEFT, padx=5)

        # Cash payment input and change calculation frame
        self.cash_payment_frame = ttk.Frame(main_frame)
        self.cash_payment_frame.grid(row=5, column=0, sticky="ew", pady=10)
        self.cash_payment_frame.columnconfigure(0, weight=1)

        ttk.Label(
            self.cash_payment_frame,
            text="Amount Received (R$):",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="w")

        self.amount_received_entry = ttk.Entry(
            self.cash_payment_frame, font=("Segoe UI", 12)
        )
        self.amount_received_entry.grid(row=1, column=0, sticky="ew")
        self.amount_received_entry.bind("<KeyRelease>", self.calculate_change)

        self.change_label = ttk.Label(
            self.cash_payment_frame,
            text="Change: R$ 0.00",
            font=("Segoe UI", 16, "bold"),
            bootstyle="info",
        )
        self.change_label.grid(row=2, column=0, pady=15)

        ttk.Button(
            main_frame,
            text="Confirm Payment",
            command=self.process_payment,
            bootstyle="success",
        ).grid(row=6, column=0, ipady=8, ipadx=20, pady=20)

    def toggle_payment_fields(self):
        if self.payment_method_var.get() == "Cash":
            self.cash_payment_frame.grid(row=5, column=0, sticky="ew", pady=10)
        else:
            self.cash_payment_frame.grid_remove()

    def calculate_change(self, event=None):
        try:
            received = float(
                self.amount_received_entry.get().replace(",", ".")
            )
            change = received - self.total_amount
            self.change_label.config(
                text=f"Change: R$ {max(0, change):.2f}"
            )
        except ValueError:
            self.change_label.config(text="Change: R$ 0.00")

    def process_payment(self):
        if self.payment_method_var.get() == "Cash":
            try:
                received = float(
                    self.amount_received_entry.get().replace(",", ".")
                )
                if received < self.total_amount:
                    messagebox.showerror(
                        "Insufficient Amount",
                        "The amount received cannot be less than the sale total.",
                        parent=self,
                    )
                    return
                self.amount_received = received
            except ValueError:
                messagebox.showerror(
                    "Invalid Amount",
                    "Please enter a valid received amount.",
                    parent=self,
                )
                return
        else:
            # For digital/card payments, received amount equals the total sale amount
            self.amount_received = self.total_amount

        self.sale_data["payment_method"] = self.payment_method_var.get()

        try:
            response = requests.post(
                f"{BACKEND_URL}/sales",
                json=self.sale_data,
                headers=self.api_headers,
            )
            if response.status_code == 201:
                self.sale_details = response.json()
                self.sale_successful = True
                self.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to record sale: {response.text}",
                    parent=self,
                )
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e), parent=self)


class POSView(ttk.Frame):
    def __init__(self, parent, token, **kwargs):
        super().__init__(parent, padding=10)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.cart_items = []
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        # Item input section
        add_item_frame = ttk.LabelFrame(
            main_frame, text="Add Product", padding=10
        )
        add_item_frame.grid(
            row=0, column=0, padx=(0, 10), pady=5, sticky="nsew"
        )

        ttk.Label(add_item_frame, text="Name or Barcode:").pack(fill=tk.X)
        self.search_entry = ttk.Entry(add_item_frame)
        self.search_entry.pack(fill=tk.X, pady=(0, 10))
        self.search_entry.bind("<Return>", self.add_product_to_cart)

        ttk.Label(add_item_frame, text="Quantity:").pack(fill=tk.X)
        self.quantity_var = tk.IntVar(value=1)
        self.quantity_entry = ttk.Entry(
            add_item_frame, textvariable=self.quantity_var
        )
        self.quantity_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            add_item_frame,
            text="Add Item",
            command=self.add_product_to_cart,
            bootstyle="primary",
        ).pack(fill=tk.X)

        # Shopping cart section
        cart_frame = ttk.LabelFrame(main_frame, text="Cart", padding=10)
        cart_frame.grid(row=0, column=1, pady=5, sticky="nsew")
        cart_frame.rowconfigure(0, weight=1)
        cart_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            cart_frame,
            columns=("Product", "Qty", "Unit Price", "Subtotal"),
            show="headings",
        )
        self.tree.heading("Product", text="Product")
        self.tree.heading("Qty", text="Qty")
        self.tree.heading("Unit Price", text="Unit Price")
        self.tree.heading("Subtotal", text="Subtotal")

        self.tree.column("Qty", width=60, anchor="center")
        self.tree.column("Unit Price", width=100, anchor="e")
        self.tree.column("Subtotal", width=100, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            cart_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Checkout actions section
        actions_frame = ttk.LabelFrame(main_frame, text="TOTAL", padding=10)
        actions_frame.grid(
            row=0, column=2, padx=(10, 0), pady=5, sticky="nsew"
        )

        self.total_label = ttk.Label(
            actions_frame,
            text="R$ 0.00",
            font=("Helvetica", 24, "bold"),
            bootstyle="success",
        )
        self.total_label.pack(pady=20, fill=tk.X)

        ttk.Button(
            actions_frame,
            text="Complete Sale",
            command=self.open_payment_window,
            bootstyle="success",
        ).pack(fill=tk.X, pady=5, ipady=5)

        ttk.Button(
            actions_frame,
            text="Remove Item",
            command=self.remove_item,
            bootstyle="danger",
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            actions_frame,
            text="Cancel Sale",
            command=self.reset_cart,
            bootstyle="secondary",
        ).pack(fill=tk.X, pady=5)

        self.search_entry.focus_set()

    def open_payment_window(self):
        if not self.cart_items:
            messagebox.showwarning(
                "Empty Cart", "Add products before completing the sale."
            )
            return

        total_amount = sum(
            item["unit_price"] * item["quantity"] for item in self.cart_items
        )
        items_for_api = [
            {
                "product_id": item["_id"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "name": item["name"],
            }
            for item in self.cart_items
        ]
        sale_data = {
            "items": items_for_api,
            "total_amount": total_amount,
            "user_id": "admin",
        }

        payment_popup = PaymentWindow(
            self, total_amount, sale_data, self.api_headers
        )
        self.wait_window(payment_popup)

        if payment_popup.sale_successful:
            messagebox.showinfo("Success", "Sale completed successfully!")

            receipt_data = payment_popup.sale_details
            receipt_data["items"] = sale_data["items"]
            receipt_data["amount_received"] = payment_popup.amount_received

            if messagebox.askyesno(
                "Generate Receipt", "Would you like to print/generate the sale receipt?"
            ):
                try:
                    receipt_path = create_receipt_image(receipt_data)
                    messagebox.showinfo(
                        "Receipt Generated", f"Receipt saved at:\n{receipt_path}"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Receipt Error",
                        f"Failed to generate receipt.\nDetails: {e}",
                    )
            self.reset_cart()

    def add_product_to_cart(self, event=None):
        term = self.search_entry.get()
        quantity = self.quantity_var.get()
        if not term or quantity <= 0:
            return

        try:
            # Updated API endpoint URL convention if needed (e.g. /products/lookup/)
            response = requests.get(
                f"{BACKEND_URL}/products/lookup/{term}", headers=self.api_headers
            )
            if response.status_code == 200:
                product = response.json()
                for item in self.cart_items:
                    if item["_id"] == product["_id"]:
                        item["quantity"] += quantity
                        self.update_cart_display()
                        break
                else:
                    self.cart_items.append(
                        {
                            "_id": product["_id"],
                            "name": product["name"],
                            "quantity": quantity,
                            "unit_price": product["price_sell"],
                        }
                    )
                    self.update_cart_display()
            else:
                messagebox.showwarning(
                    "Not Found", f"Product with query '{term}' was not found."
                )
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", str(e))

        self.search_entry.delete(0, tk.END)
        self.quantity_var.set(1)
        self.search_entry.focus_set()

    def update_cart_display(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        total = 0.0
        for item in self.cart_items:
            subtotal = item["unit_price"] * item["quantity"]
            self.tree.insert(
                "",
                "end",
                values=(
                    item["name"],
                    item["quantity"],
                    f"{item['unit_price']:.2f}",
                    f"{subtotal:.2f}",
                ),
            )
            total += subtotal
        self.total_label.config(text=f"R$ {total:.2f}")

    def remove_item(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "No Item Selected", "Select an item from the cart to remove."
            )
            return
        item_values = self.tree.item(selected_item, "values")
        item_name = item_values[0]
        self.cart_items = [
            item for item in self.cart_items if item["name"] != item_name
        ]
        self.update_cart_display()

    def reset_cart(self):
        self.cart_items.clear()
        self.update_cart_display()
        self.search_entry.delete(0, tk.END)
        self.quantity_var.set(1)
        self.search_entry.focus_set()