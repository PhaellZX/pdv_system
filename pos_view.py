import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
import webbrowser
import pathlib
from receipt_generator import create_receipt_image

BACKEND_URL = "http://127.0.0.1:8000"

class PaymentDialog(ttk.Toplevel):
    def __init__(self, parent, total_amount):
        super().__init__(parent)
        self.total_amount = total_amount; self.result = None
        self.title("Finalizar Pagamento"); self.geometry("350x250"); self.resizable(False, False); self.grab_set()
        self.initial_frame = ttk.Frame(self, padding=10); self.cash_frame = ttk.Frame(self, padding=10)
        self.create_initial_widgets(); self.create_cash_widgets()
        self.initial_frame.pack(expand=True, fill=tk.BOTH)

    def create_initial_widgets(self):
        ttk.Label(self.initial_frame, text="Forma de pagamento:", font=("Segoe UI", 12)).pack(pady=10)
        ttk.Button(self.initial_frame, text="Dinheiro", command=self.show_cash_payment, bootstyle="primary").pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(self.initial_frame, text="Cartão/Pix", command=self.finish_other_payment, bootstyle="info").pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(self.initial_frame, text="Cancelar", command=self.destroy, bootstyle="secondary").pack(fill=tk.X, pady=15)

    def create_cash_widgets(self):
        total_formatted = f"R$ {self.total_amount:.2f}".replace('.', ',')
        ttk.Label(self.cash_frame, text=f"Total a Pagar: {total_formatted}", font=("Segoe UI", 12, "bold")).pack(pady=10)
        ttk.Label(self.cash_frame, text="Valor Recebido:").pack(pady=(10, 0))
        self.amount_received_entry = ttk.Entry(self.cash_frame, font=("Segoe UI", 12), justify='center')
        self.amount_received_entry.pack(pady=5)
        self.amount_received_entry.bind("<Return>", lambda e: self.process_cash_payment())
        ttk.Button(self.cash_frame, text="Confirmar", command=self.process_cash_payment, bootstyle="success").pack(fill=tk.X, pady=10, ipady=5)
        ttk.Button(self.cash_frame, text="Voltar", command=self.show_initial_view, bootstyle="secondary").pack(fill=tk.X, pady=5)

    def show_cash_payment(self): self.initial_frame.pack_forget(); self.cash_frame.pack(expand=True, fill=tk.BOTH); self.amount_received_entry.focus_set()
    def show_initial_view(self): self.cash_frame.pack_forget(); self.initial_frame.pack(expand=True, fill=tk.BOTH)
    def finish_other_payment(self): self.result = {"method": "Cartão/Pix", "change": 0.0}; self.destroy()
    def process_cash_payment(self):
        try: amount_received = float(self.amount_received_entry.get().replace(',', '.'))
        except ValueError: return messagebox.showerror("Erro", "Insira um número válido.", parent=self)
        if amount_received < self.total_amount: return messagebox.showwarning("Valor Insuficiente", "Valor recebido menor que o total.", parent=self)
        self.result = {"method": "Dinheiro", "change": amount_received - self.total_amount}; self.destroy()

class POSView(ttk.Frame):
    def __init__(self, parent, token, **kwargs):
        super().__init__(parent)
        self.token = token; self.user_info = kwargs.get("user_info", {}); self.api_headers = {"Authorization": f"Bearer {self.token}"}; self.cart = []
        self.create_widgets()

    def create_widgets(self):
        self.columnconfigure(1, weight=1); self.rowconfigure(0, weight=1)
        left_frame = ttk.LabelFrame(self, text="Adicionar Produto", padding=10, bootstyle="secondary")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        ttk.Label(left_frame, text="Nome ou Cód. Barras:").pack(pady=(0, 5))
        self.product_search_entry = ttk.Entry(left_frame, width=30); self.product_search_entry.pack(pady=(0, 10)); self.product_search_entry.bind("<Return>", self.find_product)
        ttk.Label(left_frame, text="Quantidade:").pack(pady=(0, 5))
        self.quantity_entry = ttk.Entry(left_frame, width=10, justify='center'); self.quantity_entry.pack(pady=(0, 10)); self.quantity_entry.insert(0, "1")
        ttk.Button(left_frame, text="Adicionar", command=self.find_product, bootstyle="primary").pack(pady=10)

        cart_frame = ttk.LabelFrame(self, text="Carrinho", padding=10, bootstyle="secondary")
        cart_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        cart_frame.columnconfigure(0, weight=1); cart_frame.rowconfigure(0, weight=1)
        self.cart_tree = ttk.Treeview(cart_frame, columns=("ID", "Nome", "Qtd", "Preço Unit.", "Subtotal"), show="headings", bootstyle="primary")
        self.cart_tree.heading("ID", text="ID"); self.cart_tree.heading("Nome", text="Produto"); self.cart_tree.heading("Qtd", text="Qtd."); self.cart_tree.heading("Preço Unit.", text="Preço Unit."); self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.column("ID", width=0, stretch=tk.NO); self.cart_tree.column("Qtd", width=50, anchor="center"); self.cart_tree.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(self, padding=10); right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="ns")
        total_frame = ttk.LabelFrame(right_frame, text="TOTAL", padding=10, bootstyle="primary")
        total_frame.pack(fill=tk.X)
        self.total_label = ttk.Label(total_frame, text="R$ 0,00", font=("Segoe UI", 24, "bold"), bootstyle="inverse-primary")
        self.total_label.pack()
        actions_frame = ttk.Frame(right_frame, padding=(0, 20)); actions_frame.pack(fill=tk.X)
        ttk.Button(actions_frame, text="Finalizar Venda", command=self.finalize_sale, bootstyle="success").pack(pady=10, fill=tk.X, ipady=10)
        ttk.Button(actions_frame, text="Remover Item", command=self.remove_item, bootstyle="danger").pack(pady=5, fill=tk.X)
        ttk.Button(actions_frame, text="Cancelar Venda", command=self.clear_sale, bootstyle="secondary").pack(pady=5, fill=tk.X)

    def find_product(self, event=None):
        search_term = self.product_search_entry.get()
        if not search_term: return
        try:
            quantity_to_add = int(self.quantity_entry.get())
            if quantity_to_add <= 0: return messagebox.showerror("Erro", "A quantidade deve ser positiva.")
        except ValueError: return messagebox.showerror("Erro", "Quantidade inválida.")
        try:
            response = requests.get(f"{BACKEND_URL}/produtos/lookup/{search_term}", headers=self.api_headers)
            if response.status_code == 200:
                self.add_to_cart(response.json(), quantity_to_add)
                self.product_search_entry.delete(0, tk.END); self.quantity_entry.delete(0, tk.END)
                self.quantity_entry.insert(0, "1"); self.product_search_entry.focus()
            else: messagebox.showwarning("Não Encontrado", f"Produto '{search_term}' não encontrado.")
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))

    def add_to_cart(self, product, quantity_to_add):
        product_id = product["_id"]
        for item in self.cart:
            if item["product_id"] == product_id: item["quantity"] += quantity_to_add; self.update_cart_display(); return
        self.cart.append({"product_id": product_id, "name": product["name"], "quantity": quantity_to_add, "unit_price": product["price_sell"]})
        self.update_cart_display()

    def update_cart_display(self):
        for item in self.cart_tree.get_children(): self.cart_tree.delete(item)
        total = 0
        for item in self.cart:
            subtotal = item["quantity"] * item["unit_price"]
            total += subtotal
            price_unit_formatted = f"R$ {item['unit_price']:.2f}".replace('.', ','); subtotal_formatted = f"R$ {subtotal:.2f}".replace('.', ',')
            self.cart_tree.insert("", tk.END, iid=item["product_id"], values=(item["product_id"], item["name"], item["quantity"], price_unit_formatted, subtotal_formatted))
        self.total_label.config(text=f"R$ {total:.2f}".replace('.', ','))

    def remove_item(self):
        if not (selected_item := self.cart_tree.focus()): return messagebox.showwarning("Atenção", "Selecione um item.")
        self.cart = [item for item in self.cart if item["product_id"] != selected_item]; self.update_cart_display()

    def clear_sale(self):
        if self.cart and messagebox.askokcancel("Cancelar Venda", "Limpar o carrinho?"):
            self.cart.clear(); self.update_cart_display()

    def finalize_sale(self):
        if not self.cart: return messagebox.showwarning("Atenção", "O carrinho está vazio.")
        total_amount = sum(i["quantity"] * i["unit_price"] for i in self.cart)
        dialog = PaymentDialog(self, total_amount)
        self.wait_window(dialog)
        if dialog.result is None: return
        payment_info = dialog.result; change_amount = payment_info.get("change", 0.0)
        
        sale_items = [{"product_id": i["product_id"], "quantity": i["quantity"], "unit_price": i["unit_price"]} for i in self.cart]
        sale_data = {"items": sale_items, "total_amount": total_amount, "payment_method": payment_info["method"], "user_id": self.user_info.get("username", "N/A")}
        try:
            response = requests.post(f"{BACKEND_URL}/vendas", headers=self.api_headers, json=sale_data)
            if response.status_code == 201:
                troco_str = f"\n\nTroco: R$ {change_amount:.2f}".replace('.', ',')
                messagebox.showinfo("Sucesso", f"Venda registrada!{troco_str}")
                receipt_data = response.json()
                for i, s_item in enumerate(receipt_data["items"]):
                    for c_item in self.cart:
                        if s_item["product_id"] == c_item["product_id"]: s_item["name"] = c_item["name"]; break
                if (path := create_receipt_image(receipt_data)) and messagebox.askyesno("Recibo Gerado", f"Salvo como '{path}'.\nVisualizar agora?"):
                    webbrowser.open(pathlib.Path(path).absolute().as_uri())
                self.cart.clear(); self.update_cart_display()
            else: messagebox.showerror("Erro ao Finalizar", f"Detalhe: {response.json().get('detail', response.text)}")
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))