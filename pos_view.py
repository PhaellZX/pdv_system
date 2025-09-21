# pos_view.py
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
from receipt_generator import create_receipt_image

BACKEND_URL = "http://127.0.0.1:8000"

class PaymentWindow(tk.Toplevel):
    def __init__(self, parent, total_amount, sale_data, api_headers):
        super().__init__(parent)
        self.parent = parent; self.total_amount = total_amount; self.sale_data = sale_data; self.api_headers = api_headers
        self.sale_successful = False; self.sale_details = None
        self.amount_received = 0.0 # Nova variável para guardar o valor recebido
        self.title("Finalizar Pagamento"); self.geometry("400x480"); self.resizable(False, False); self.transient(parent); self.grab_set()
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20); main_frame.pack(fill=tk.BOTH, expand=True); main_frame.columnconfigure(0, weight=1)
        ttk.Label(main_frame, text="Total a Pagar:", font=("Segoe UI", 14)).grid(row=0, column=0, sticky="ew")
        ttk.Label(main_frame, text=f"R$ {self.total_amount:.2f}", font=("Segoe UI", 28, "bold"), bootstyle="success").grid(row=1, column=0, pady=(5, 20))
        ttk.Separator(main_frame).grid(row=2, column=0, sticky="ew", pady=10)
        ttk.Label(main_frame, text="Forma de Pagamento:", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w")
        radio_frame = ttk.Frame(main_frame); radio_frame.grid(row=4, column=0, sticky="w", pady=5)
        self.payment_method_var = tk.StringVar(value="Dinheiro")
        ttk.Radiobutton(radio_frame, text="Dinheiro", variable=self.payment_method_var, value="Dinheiro", command=self.toggle_payment_fields, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(radio_frame, text="PIX/Cartão", variable=self.payment_method_var, value="PIX/Cartão", command=self.toggle_payment_fields, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        self.cash_payment_frame = ttk.Frame(main_frame); self.cash_payment_frame.grid(row=5, column=0, sticky="ew", pady=10); self.cash_payment_frame.columnconfigure(0, weight=1)
        ttk.Label(self.cash_payment_frame, text="Valor Recebido (R$):", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.amount_received_entry = ttk.Entry(self.cash_payment_frame, font=("Segoe UI", 12)); self.amount_received_entry.grid(row=1, column=0, sticky="ew"); self.amount_received_entry.bind("<KeyRelease>", self.calculate_change)
        self.change_label = ttk.Label(self.cash_payment_frame, text="Troco: R$ 0,00", font=("Segoe UI", 16, "bold"), bootstyle="info"); self.change_label.grid(row=2, column=0, pady=15)
        ttk.Button(main_frame, text="Confirmar Pagamento", command=self.process_payment, bootstyle="success").grid(row=6, column=0, ipady=8, ipadx=20, pady=20)

    def toggle_payment_fields(self):
        if self.payment_method_var.get() == "Dinheiro": self.cash_payment_frame.grid(row=5, column=0, sticky="ew", pady=10)
        else: self.cash_payment_frame.grid_remove()

    def calculate_change(self, event=None):
        try: received = float(self.amount_received_entry.get().replace(',', '.')); change = received - self.total_amount; self.change_label.config(text=f"Troco: R$ {max(0, change):.2f}")
        except ValueError: self.change_label.config(text="Troco: R$ 0,00")
            
    def process_payment(self):
        if self.payment_method_var.get() == "Dinheiro":
            try:
                received = float(self.amount_received_entry.get().replace(',', '.'))
                if received < self.total_amount: messagebox.showerror("Valor Insuficiente", "O valor recebido não pode ser menor que o total da venda.", parent=self); return
                self.amount_received = received # Guarda o valor recebido
            except ValueError: messagebox.showerror("Valor Inválido", "Por favor, insira um valor recebido válido.", parent=self); return
        else:
            self.amount_received = self.total_amount # Se for PIX/Cartão, o valor recebido é o total
        
        self.sale_data["payment_method"] = self.payment_method_var.get()
        try:
            response = requests.post(f"{BACKEND_URL}/vendas", json=self.sale_data, headers=self.api_headers)
            if response.status_code == 201: self.sale_details = response.json(); self.sale_successful = True; self.destroy()
            else: messagebox.showerror("Erro", f"Falha ao registrar a venda: {response.text}", parent=self)
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e), parent=self)

class POSView(ttk.Frame):
    def __init__(self, parent, token, **kwargs):
        super().__init__(parent, padding=10)
        self.token = token; self.api_headers = {"Authorization": f"Bearer {self.token}"}; self.cart_items = []
        self.create_widgets()
    def create_widgets(self):
        main_frame = ttk.Frame(self); main_frame.pack(fill=tk.BOTH, expand=True); main_frame.columnconfigure(1, weight=1)
        add_item_frame = ttk.LabelFrame(main_frame, text="Adicionar Produto", padding=10); add_item_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        ttk.Label(add_item_frame, text="Nome ou Cód. Barras:").pack(fill=tk.X)
        self.search_entry = ttk.Entry(add_item_frame); self.search_entry.pack(fill=tk.X, pady=(0, 10)); self.search_entry.bind("<Return>", self.add_product_to_cart)
        ttk.Label(add_item_frame, text="Quantidade:").pack(fill=tk.X)
        self.quantity_var = tk.IntVar(value=1)
        self.quantity_entry = ttk.Entry(add_item_frame, textvariable=self.quantity_var); self.quantity_entry.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(add_item_frame, text="Adicionar", command=self.add_product_to_cart, bootstyle="primary").pack(fill=tk.X)
        cart_frame = ttk.LabelFrame(main_frame, text="Carrinho", padding=10); cart_frame.grid(row=0, column=1, pady=5, sticky="nsew"); cart_frame.rowconfigure(0, weight=1); cart_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(cart_frame, columns=("Produto", "Qtd.", "Preço Unit.", "Subtotal"), show="headings"); self.tree.heading("Produto", text="Produto"); self.tree.heading("Qtd.", text="Qtd."); self.tree.heading("Preço Unit.", text="Preço Unit."); self.tree.heading("Subtotal", text="Subtotal"); self.tree.column("Qtd.", width=60, anchor='center'); self.tree.column("Preço Unit.", width=100, anchor='e'); self.tree.column("Subtotal", width=100, anchor='e'); self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self.tree.yview); self.tree.configure(yscroll=scrollbar.set); scrollbar.grid(row=0, column=1, sticky="ns")
        actions_frame = ttk.LabelFrame(main_frame, text="TOTAL", padding=10); actions_frame.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="nsew")
        self.total_label = ttk.Label(actions_frame, text="R$ 0,00", font=("Helvetica", 24, "bold"), bootstyle="success"); self.total_label.pack(pady=20, fill=tk.X)
        ttk.Button(actions_frame, text="Finalizar Venda", command=self.open_payment_window, bootstyle="success").pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(actions_frame, text="Remover Item", command=self.remove_item, bootstyle="danger").pack(fill=tk.X, pady=5)
        ttk.Button(actions_frame, text="Cancelar Venda", command=self.reset_cart, bootstyle="secondary").pack(fill=tk.X, pady=5)
        self.search_entry.focus_set()

    def open_payment_window(self):
        if not self.cart_items: messagebox.showwarning("Carrinho Vazio", "Adicione produtos antes de finalizar a venda."); return
        total_amount = sum(item['unit_price'] * item['quantity'] for item in self.cart_items)
        items_for_api = [{"product_id": item["_id"], "quantity": item["quantity"], "unit_price": item["unit_price"], "name": item["name"]} for item in self.cart_items]
        sale_data = {"items": items_for_api, "total_amount": total_amount, "user_id": "admin"}
        payment_popup = PaymentWindow(self, total_amount, sale_data, self.api_headers); self.wait_window(payment_popup)
        
        if payment_popup.sale_successful:
            messagebox.showinfo("Sucesso", "Venda finalizada com sucesso!")
            
            receipt_data = payment_popup.sale_details
            receipt_data['items'] = sale_data['items']
            # Adiciona o valor recebido aos dados do recibo
            receipt_data['amount_received'] = payment_popup.amount_received

            if messagebox.askyesno("Gerar Recibo", "Deseja gerar o comprovante da venda?"):
                try:
                    receipt_path = create_receipt_image(receipt_data)
                    messagebox.showinfo("Recibo Gerado", f"Recibo salvo em:\n{receipt_path}")
                except Exception as e:
                    messagebox.showerror("Erro no Recibo", f"Não foi possível gerar o recibo.\nDetalhe: {e}")
            self.reset_cart()

    def add_product_to_cart(self, event=None):
        term = self.search_entry.get(); quantity = self.quantity_var.get()
        if not term or quantity <= 0: return
        try:
            response = requests.get(f"{BACKEND_URL}/produtos/lookup/{term}", headers=self.api_headers)
            if response.status_code == 200:
                product = response.json()
                for item in self.cart_items:
                    if item["_id"] == product["_id"]:
                        item["quantity"] += quantity; self.update_cart_display(); break
                else: self.cart_items.append({"_id": product['_id'], "name": product['name'], "quantity": quantity, "unit_price": product['price_sell']}); self.update_cart_display()
            else: messagebox.showwarning("Não Encontrado", f"Produto com termo '{term}' não encontrado.")
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))
        self.search_entry.delete(0, tk.END); self.quantity_var.set(1); self.search_entry.focus_set()

    def update_cart_display(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = 0.0
        for item in self.cart_items:
            subtotal = item["unit_price"] * item["quantity"]
            self.tree.insert("", "end", values=(item["name"], item["quantity"], f"{item['unit_price']:.2f}", f"{subtotal:.2f}"))
            total += subtotal
        self.total_label.config(text=f"R$ {total:.2f}")

    def remove_item(self):
        selected_item = self.tree.selection()
        if not selected_item: messagebox.showwarning("Nenhum Item", "Selecione um item para remover."); return
        item_values = self.tree.item(selected_item, "values"); item_name = item_values[0]
        self.cart_items = [item for item in self.cart_items if item["name"] != item_name]; self.update_cart_display()

    def reset_cart(self):
        self.cart_items.clear(); self.update_cart_display(); self.search_entry.delete(0, tk.END); self.quantity_var.set(1); self.search_entry.focus_set()