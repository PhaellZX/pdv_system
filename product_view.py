import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox, filedialog
import requests
import json
import os

BACKEND_URL = "http://127.0.0.1:8000"

# (A classe ProductForm continua a mesma da versão anterior, não precisa ser alterada)
class ProductForm(ttk.Toplevel):
    def __init__(self, parent, token, product_id=None, initial_data=None, callback=None):
        super().__init__(parent)
        self.token = token; self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.product_id = product_id; self.initial_data = initial_data or {}; self.callback = callback
        self.title("Editar Produto" if self.product_id else "Adicionar Novo Produto")
        self.geometry("400x300"); self.resizable(False, False); self.grab_set()
        self.create_form(); self.load_initial_data()
    def create_form(self):
        frame = ttk.Frame(self, padding="20"); frame.pack(expand=True, fill=tk.BOTH); frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=5); self.name_entry = ttk.Entry(frame); self.name_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(frame, text="Cód. Barras:").grid(row=1, column=0, sticky="w", pady=5); self.barcode_entry = ttk.Entry(frame); self.barcode_entry.grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text="Preço de Venda:").grid(row=2, column=0, sticky="w", pady=5); self.price_entry = ttk.Entry(frame); self.price_entry.grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="Estoque:").grid(row=3, column=0, sticky="w", pady=5); self.stock_entry = ttk.Entry(frame); self.stock_entry.grid(row=3, column=1, sticky="ew")
        ttk.Label(frame, text="Descrição:").grid(row=4, column=0, sticky="w", pady=5); self.desc_entry = ttk.Entry(frame); self.desc_entry.grid(row=4, column=1, sticky="ew")
        btn_frame = ttk.Frame(frame); btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Salvar", command=self.save_product, bootstyle="success").pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy, bootstyle="secondary").pack(side=tk.LEFT)
    def load_initial_data(self):
        self.name_entry.insert(0, self.initial_data.get("name", "")); self.barcode_entry.insert(0, self.initial_data.get("barcode", "") or "")
        self.price_entry.insert(0, self.initial_data.get("price_sell", "")); self.stock_entry.insert(0, self.initial_data.get("stock_quantity", ""))
        self.desc_entry.insert(0, self.initial_data.get("description", "") or "")
    def save_product(self):
        try:
            price_val = self.price_entry.get().replace(',', '.')
            data = {"name": self.name_entry.get(), "barcode": self.barcode_entry.get() or None, "price_sell": float(price_val), "stock_quantity": int(self.stock_entry.get()), "description": self.desc_entry.get()}
            if not data["name"] or data["price_sell"] <= 0 or data["stock_quantity"] < 0: return messagebox.showerror("Erro de Validação", "Nome, Preço e Estoque são obrigatórios.", parent=self)
            if self.product_id: response = requests.put(f"{BACKEND_URL}/produtos/{self.product_id}", headers=self.api_headers, json=data)
            else: response = requests.post(f"{BACKEND_URL}/produtos", headers=self.api_headers, json=data)
            if response.status_code in [200, 201]: messagebox.showinfo("Sucesso", "Produto salvo com sucesso!", parent=self); self.callback(); self.destroy()
            else: messagebox.showerror("Erro ao Salvar", f"Detalhe: {response.json().get('detail', response.text)}", parent=self)
        except ValueError: messagebox.showerror("Erro de Formato", "Preço e Estoque devem ser números.", parent=self)
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e), parent=self)

class ProductView(ttk.Frame):
    def __init__(self, parent, token, **kwargs):
        super().__init__(parent)
        self.token = token; self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.create_widgets(); self.load_products()

    def create_widgets(self):
        # Frame de busca e ações principais
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        self.search_entry = ttk.Entry(top_frame); self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.load_products())
        ttk.Button(top_frame, text="Buscar", command=self.load_products, bootstyle="secondary").pack(side=tk.LEFT, padx=5)
        
        # Frame de ações de gerenciamento
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(actions_frame, text="Adicionar Novo", command=self.open_product_form, bootstyle="success").pack(side=tk.RIGHT)
        ttk.Button(actions_frame, text="Inativar", command=self.delete_selected, bootstyle="danger-outline").pack(side=tk.RIGHT, padx=5)
        ttk.Button(actions_frame, text="Editar", command=self.edit_selected, bootstyle="info-outline").pack(side=tk.RIGHT, padx=5)
        
        # --- NOVOS BOTÕES DE BACKUP ---
        ttk.Button(actions_frame, text="Importar Backup(JSON)", command=self.import_products, bootstyle="warning").pack(side=tk.LEFT)
        ttk.Button(actions_frame, text="Exportar Backup(JSON)", command=self.export_products, bootstyle="secondary").pack(side=tk.LEFT, padx=5)
        
        # Tabela de produtos
        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Nome", "Preço", "Estoque"), show="headings", bootstyle="primary")
        self.tree.heading("ID", text="ID"); self.tree.heading("Nome", text="Nome do Produto"); self.tree.heading("Preço", text="Preço (R$)"); self.tree.heading("Estoque", text="Qtd. em Estoque")
        self.tree.column("ID", width=250, stretch=tk.NO); self.tree.column("Nome", width=300); self.tree.column("Preço", width=100, anchor='e'); self.tree.column("Estoque", width=100, anchor='center')
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, bootstyle="round")
        self.tree.configure(yscroll=scrollbar.set); self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_products(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            response = requests.get(f"{BACKEND_URL}/produtos?search={self.search_entry.get()}", headers=self.api_headers)
            if response.status_code == 200:
                for prod in response.json():
                    price_formatted = f"R$ {prod['price_sell']:.2f}".replace('.', ',')
                    self.tree.insert("", tk.END, values=(prod['_id'], prod['name'], price_formatted, prod['stock_quantity']))
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))

    # --- NOVAS FUNÇÕES DE IMPORTAÇÃO E EXPORTAÇÃO ---
    def export_products(self):
        try:
            # Chama o endpoint pedindo TODOS os produtos, não apenas os ativos
            response = requests.get(f"{BACKEND_URL}/produtos?active_only=false", headers=self.api_headers)
            if response.status_code != 200:
                return messagebox.showerror("Erro", f"Não foi possível buscar os produtos para exportar.\nDetalhe: {response.text}")

            products_data = response.json()
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Salvar backup de produtos"
            )
            if not file_path: return # Usuário cancelou

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Sucesso", f"Backup de {len(products_data)} produtos exportado para:\n{file_path}")

        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))
        except Exception as e: messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao exportar: {e}")

    def import_products(self):
        if not messagebox.askyesno("Confirmar Importação", "Isso adicionará produtos a partir de um arquivo JSON. Produtos com códigos de barras já existentes serão ignorados. Deseja continuar?"):
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Abrir backup de produtos"
        )
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products_to_import = json.load(f)
            
            if not isinstance(products_to_import, list):
                return messagebox.showerror("Erro de Formato", "O arquivo JSON deve conter uma lista de produtos.")

            success_count = 0
            fail_count = 0
            
            for product in products_to_import:
                # Remove o ID para que o banco de dados gere um novo
                product.pop('_id', None)
                product.pop('id', None)
                
                response = requests.post(f"{BACKEND_URL}/produtos", headers=self.api_headers, json=product)
                if response.status_code == 201:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"Falha ao importar produto {product.get('name')}: {response.text}")
            
            messagebox.showinfo("Importação Concluída", f"Sucesso: {success_count} produtos importados.\nFalhas: {fail_count} produtos (verifique o console para detalhes).")
            self.load_products()

        except json.JSONDecodeError: messagebox.showerror("Erro de Arquivo", "O arquivo selecionado não é um JSON válido.")
        except Exception as e: messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao importar: {e}")


    # (O resto das funções: get_selected_product_id, edit_selected, delete_selected, open_product_form continuam as mesmas)
    def get_selected_product_id(self):
        if not (selected_item := self.tree.focus()): messagebox.showwarning("Atenção", "Selecione um produto."); return None
        return self.tree.item(selected_item)['values'][0]
    def edit_selected(self):
        if not (pid := self.get_selected_product_id()): return
        try:
            # Usamos a rota lookup que busca por ID também
            response = requests.get(f"{BACKEND_URL}/produtos/lookup/{pid}", headers=self.api_headers)
            if response.status_code == 200: self.open_product_form(product_id=pid, initial_data=response.json())
            else: messagebox.showerror("Erro", "Não foi possível buscar os dados do produto.")
        except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))
    def delete_selected(self):
        if not (pid := self.get_selected_product_id()): return
        if messagebox.askyesno("Confirmar Inativação", "Tem certeza que deseja inativar este produto?"):
            try:
                response = requests.delete(f"{BACKEND_URL}/produtos/{pid}", headers=self.api_headers)
                if response.status_code == 204: messagebox.showinfo("Sucesso", "Produto inativado."); self.load_products()
                else: messagebox.showerror("Erro", f"Falha ao inativar: {response.text}")
            except requests.exceptions.RequestException as e: messagebox.showerror("Erro de Conexão", str(e))
    def open_product_form(self, product_id=None, initial_data=None):
        ProductForm(self, self.token, product_id, initial_data, callback=self.load_products)